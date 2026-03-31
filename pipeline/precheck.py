"""
precheck.py — Pre-push validation for the Anelo pipeline.

Catches every class of bug that has crashed this pipeline in production:
  1. Python syntax errors in all pipeline .py files
  2. Import resolution errors
  3. None-coercion hazards (.get("key", "").somemethod() patterns)
  4. Supabase table existence (preferences, users, resumes, digest_jobs)
  5. Anthropic API key validity (minimal test call)
  6. Required env vars present

Run standalone: python precheck.py
Exit code 0 = all checks pass (WARNs are non-blocking).
Exit code 1 = at least one FAIL.
"""

import ast
import importlib
import os
import sys
import textwrap
from pathlib import Path

# Load .env from the pipeline directory (where this script lives)
_PIPELINE_DIR = Path(__file__).parent.resolve()
sys.path.insert(0, str(_PIPELINE_DIR))

try:
    from dotenv import load_dotenv
    load_dotenv(_PIPELINE_DIR / ".env")
except ImportError:
    # python-dotenv not installed — env must come from the environment
    pass

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_PASS = "PASS"
_FAIL = "FAIL"
_WARN = "WARN"

_results: list[tuple[str, str, str]] = []  # (status, check_name, reason)


def _record(status: str, name: str, reason: str) -> None:
    _results.append((status, name, reason))
    tag = f"[{status}]"
    width = 8
    print(f"  {tag:<{width}} {name}: {reason}")


# ---------------------------------------------------------------------------
# Check 1 — Python syntax
# ---------------------------------------------------------------------------

def check_syntax() -> None:
    print("\n-- Syntax check --")
    py_files = sorted(_PIPELINE_DIR.glob("*.py"))
    # exclude this script itself from import-resolution check, but include for syntax
    all_ok = True
    for path in py_files:
        source = path.read_text(encoding="utf-8")
        try:
            ast.parse(source, filename=str(path))
            _record(_PASS, f"syntax:{path.name}", "ok")
        except SyntaxError as exc:
            _record(_FAIL, f"syntax:{path.name}", f"line {exc.lineno}: {exc.msg}")
            all_ok = False
    if not py_files:
        _record(_WARN, "syntax", "no .py files found in pipeline dir")


# ---------------------------------------------------------------------------
# Check 2 — Import resolution
# ---------------------------------------------------------------------------

_PIPELINE_MODULES = ["main", "jobs", "scorer", "tailor", "digest"]


def check_imports() -> None:
    print("\n-- Import resolution --")
    for mod_name in _PIPELINE_MODULES:
        mod_path = _PIPELINE_DIR / f"{mod_name}.py"
        if not mod_path.exists():
            _record(_WARN, f"import:{mod_name}", "file not found, skipping")
            continue
        source = mod_path.read_text(encoding="utf-8")
        try:
            tree = ast.parse(source)
        except SyntaxError:
            _record(_WARN, f"import:{mod_name}", "syntax error prevents import check")
            continue

        missing = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    pkg = alias.name.split(".")[0]
                    _check_importable(pkg, missing)
            elif isinstance(node, ast.ImportFrom):
                if node.module and node.level == 0:
                    pkg = node.module.split(".")[0]
                    _check_importable(pkg, missing)

        if missing:
            # Missing packages are only a FAIL if we have a .env (i.e. running in pipeline env).
            # Outside the pipeline venv, third-party packages won't be installed locally.
            level = _FAIL if _ENV_DOTFILE_EXISTS else _WARN
            _record(level, f"import:{mod_name}", f"unresolvable: {', '.join(missing)}")
        else:
            _record(_PASS, f"import:{mod_name}", "all imports resolvable")


_STDLIB_SKIP = frozenset([
    "os", "re", "sys", "ast", "json", "logging", "pathlib", "importlib",
    "textwrap", "typing", "collections", "functools", "itertools", "datetime",
    "time", "math", "hashlib", "base64", "io", "copy", "enum", "dataclasses",
    "abc", "contextlib", "warnings", "traceback", "inspect", "types",
    "threading", "queue", "subprocess", "shutil", "tempfile", "glob",
    "httpx",  # listed separately — it IS third-party but always present
    # local pipeline modules
    "main", "jobs", "scorer", "tailor", "digest",
    # this script
    "precheck",
])


def _check_importable(pkg: str, missing: list[str]) -> None:
    if pkg in _STDLIB_SKIP:
        return
    if pkg in sys.stdlib_module_names if hasattr(sys, "stdlib_module_names") else set():
        return
    try:
        importlib.import_module(pkg)
    except ImportError:
        if pkg not in missing:
            missing.append(pkg)
    except Exception:
        # ModuleNotFoundError is a subclass; other errors mean it's importable
        pass


# ---------------------------------------------------------------------------
# Check 3 — None-coercion hazards
# ---------------------------------------------------------------------------

class _NoneCoercionVisitor(ast.NodeVisitor):
    """
    Finds patterns like: obj.get("key", "").somemethod()
    These crash at runtime when the DB returns None for "key" because the
    default "" is only used when the key is absent — not when the value is None.
    The caller then chains .strip()/.lower()/etc. on None and gets AttributeError.
    """

    def __init__(self, filename: str) -> None:
        self.filename = filename
        self.hits: list[str] = []

    def visit_Attribute(self, node: ast.Attribute) -> None:
        # We're looking for:  <expr>.get(<arg>, <default>).<method>()
        # The outer node is the Attribute access (.somemethod) whose value is a Call
        # that is itself .get(...)
        if isinstance(node.value, ast.Call):
            call = node.value
            # call.func should be an Attribute named "get"
            if (
                isinstance(call.func, ast.Attribute)
                and call.func.attr == "get"
                and len(call.args) >= 2
            ):
                default_node = call.args[1]
                # Flag when default is a string constant (including "")
                if isinstance(default_node, ast.Constant) and isinstance(default_node.value, str):
                    method = node.attr
                    line = node.lineno
                    # Get the key name for context
                    key_arg = call.args[0]
                    key = key_arg.value if isinstance(key_arg, ast.Constant) else "?"
                    self.hits.append(
                        f"line {line}: .get({key!r}, {default_node.value!r}).{method}() — "
                        f"DB None will cause AttributeError"
                    )
        self.generic_visit(node)


def check_none_coercion() -> None:
    print("\n-- None-coercion hazard check --")
    py_files = sorted(_PIPELINE_DIR.glob("*.py"))
    any_hit = False
    for path in py_files:
        if path.name == "precheck.py":
            continue
        source = path.read_text(encoding="utf-8")
        try:
            tree = ast.parse(source, filename=str(path))
        except SyntaxError:
            continue
        visitor = _NoneCoercionVisitor(path.name)
        visitor.visit(tree)
        if visitor.hits:
            any_hit = True
            for hit in visitor.hits:
                _record(_WARN, f"none-coerce:{path.name}", hit)
    if not any_hit:
        _record(_PASS, "none-coercion", "no hazardous .get().method() patterns found")


# ---------------------------------------------------------------------------
# Check 4 — Supabase table existence
# ---------------------------------------------------------------------------

_REQUIRED_TABLES = ["preferences", "users", "resumes", "digest_jobs"]


def check_supabase_tables() -> None:
    print("\n-- Supabase table existence --")
    url = os.environ.get("NEXT_PUBLIC_SUPABASE_URL") or os.environ.get("SUPABASE_URL", "")
    key = os.environ.get("SUPABASE_SERVICE_ROLE_KEY", "")

    if not url or not key:
        level = _FAIL if _ENV_DOTFILE_EXISTS else _WARN
        _record(level, "supabase:credentials", "SUPABASE_URL/SERVICE_ROLE_KEY not set — skipping table check")
        return

    try:
        from supabase import create_client
    except ImportError:
        _record(_WARN, "supabase:import", "supabase package not installed — skipping table check")
        return

    try:
        db = create_client(url, key)
    except Exception as exc:
        _record(_FAIL, "supabase:connect", str(exc))
        return

    for table in _REQUIRED_TABLES:
        try:
            # Fetch 0 rows — just verifies the table exists and is accessible
            resp = db.table(table).select("*").limit(0).execute()
            _record(_PASS, f"supabase:table:{table}", "exists")
        except Exception as exc:
            msg = str(exc)
            # PostgREST returns 42P01 for "relation does not exist"
            if "42P01" in msg or "does not exist" in msg.lower():
                _record(_FAIL, f"supabase:table:{table}", "table does not exist")
            else:
                _record(_FAIL, f"supabase:table:{table}", f"error: {msg[:120]}")


# ---------------------------------------------------------------------------
# Check 5 — Anthropic API key validity
# ---------------------------------------------------------------------------

def check_anthropic_key() -> None:
    print("\n-- Anthropic API key --")
    api_key = os.environ.get("ANTHROPIC_API_KEY", "")
    if not api_key:
        level = _FAIL if _ENV_DOTFILE_EXISTS else _WARN
        _record(level, "anthropic:key", "ANTHROPIC_API_KEY not set — unverifiable without local credentials")
        return

    try:
        import anthropic
    except ImportError:
        _record(_WARN, "anthropic:import", "anthropic package not installed — skipping key check")
        return

    try:
        client = anthropic.Anthropic(api_key=api_key)
        client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=1,
            messages=[{"role": "user", "content": "hi"}],
        )
        _record(_PASS, "anthropic:key", "valid and has credits")
    except anthropic.AuthenticationError:
        _record(_FAIL, "anthropic:key", "invalid API key (authentication failed)")
    except anthropic.PermissionDeniedError:
        _record(_FAIL, "anthropic:key", "permission denied — check key scopes")
    except Exception as exc:
        msg = str(exc)
        # Credit exhaustion — treat as WARN so it doesn't block pushes
        if "credit" in msg.lower() or "billing" in msg.lower() or "quota" in msg.lower() or "overloaded" in msg.lower():
            _record(_WARN, "anthropic:key", f"key valid but credits/quota issue: {msg[:120]}")
        else:
            _record(_WARN, "anthropic:key", f"unexpected error (key may be valid): {msg[:120]}")


# ---------------------------------------------------------------------------
# Check 6 — Required env vars
# ---------------------------------------------------------------------------

_REQUIRED_VARS = [
    # At least one of these two must be set
    ("SUPABASE_URL", "NEXT_PUBLIC_SUPABASE_URL"),
    # These must all be set individually
    ("SUPABASE_SERVICE_ROLE_KEY",),
    ("ADZUNA_APP_ID",),
    ("ADZUNA_API_KEY",),
    ("ANTHROPIC_API_KEY",),
    ("RESEND_API_KEY",),
]


_ENV_DOTFILE_EXISTS = (_PIPELINE_DIR / ".env").exists()


def check_env_vars() -> None:
    print("\n-- Required env vars --")
    for group in _REQUIRED_VARS:
        if len(group) == 1:
            var = group[0]
            if os.environ.get(var):
                _record(_PASS, f"env:{var}", "set")
            elif _ENV_DOTFILE_EXISTS:
                # .env exists but var is missing — that's a real gap
                _record(_FAIL, f"env:{var}", "not set or empty")
            else:
                _record(_WARN, f"env:{var}", "not set locally (Railway secret — unverifiable here)")
        else:
            found = [v for v in group if os.environ.get(v)]
            if found:
                _record(_PASS, f"env:{'|'.join(group)}", f"set via {found[0]}")
            elif _ENV_DOTFILE_EXISTS:
                _record(_FAIL, f"env:{'|'.join(group)}", f"none of {list(group)} are set")
            else:
                _record(_WARN, f"env:{'|'.join(group)}", "not set locally (Railway secret — unverifiable here)")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> int:
    print("=" * 60)
    print("  Anelo pipeline pre-push checks")
    print(f"  Pipeline dir: {_PIPELINE_DIR}")
    print("=" * 60)

    check_env_vars()
    check_syntax()
    check_imports()
    check_none_coercion()
    check_supabase_tables()
    check_anthropic_key()

    # Summary
    fails = [r for r in _results if r[0] == _FAIL]
    warns = [r for r in _results if r[0] == _WARN]
    passes = [r for r in _results if r[0] == _PASS]

    print("\n" + "=" * 60)
    print(f"  Results: {len(passes)} PASS  {len(warns)} WARN  {len(fails)} FAIL")

    if fails:
        print("\n  FAILED checks:")
        for _, name, reason in fails:
            print(f"    - {name}: {reason}")
        print("\n  Fix the above errors before pushing.")
        print("=" * 60)
        return 1

    if warns:
        print("\n  Warnings (non-blocking):")
        for _, name, reason in warns:
            print(f"    - {name}: {reason}")

    print("\n  All checks passed.")
    print("=" * 60)
    return 0


if __name__ == "__main__":
    sys.exit(main())
