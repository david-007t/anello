#!/Users/ohsay22/Developer/jobauto/venv/bin/python3
"""
pipeline.py — Full job automation pipeline orchestrator.

Runs the complete pipeline:
  1. digest.py     — Scrape, score, verify, log jobs to Sheets
  2. validate.py   — Pre-apply quality gate on high-score jobs
  3. tailor_watcher.py --once — Tailor resumes for validated jobs
  4. apply_watcher.py --once  — Apply to tailored jobs

Usage:
    python3 pipeline.py            # full pipeline
    python3 pipeline.py --dry-run  # preview only, no applications
    python3 pipeline.py --step digest    # run only digest step
    python3 pipeline.py --step validate  # run only validate step
    python3 pipeline.py --step tailor    # run only tailor step
    python3 pipeline.py --step apply     # run only apply step
"""

import argparse
import subprocess
import sys
import time
import logging
from pathlib import Path
from datetime import datetime

BASE_DIR = Path(__file__).parent
LOG_DIR = BASE_DIR / "logs"
LOG_DIR.mkdir(exist_ok=True)

# Rich terminal output (with plain fallback)
try:
    from rich.console import Console
    from rich.panel import Panel
    HAS_RICH = True
    console = Console()
except ImportError:
    HAS_RICH = False

    class _PlainConsole:
        @staticmethod
        def print(msg, **kwargs):
            # Strip rich markup for plain output
            import re
            clean = re.sub(r'\[/?[^\]]+\]', '', str(msg))
            print(clean)

    console = _PlainConsole()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [pipeline] %(levelname)s: %(message)s",
    handlers=[
        logging.FileHandler(LOG_DIR / "pipeline.log"),
        logging.StreamHandler(),
    ],
)
logger = logging.getLogger(__name__)


STEPS = {
    "digest": {
        "script": "digest.py",
        "label": "Scraping & scoring jobs",
        "timeout": 1200,  # 20 min (65+ LinkedIn jobs × ~10s Playwright each)
    },
    "validate": {
        "script": "validate.py",
        "args": ["--queue-tailor"],  # approved jobs → "Needs Tailor" so tailor step picks them up
        "label": "Validating top candidates",
        "timeout": 300,  # 5 min
    },
    "tailor": {
        "script": "tailor_watcher.py",
        "args": ["--once"],
        "label": "Tailoring resumes",
        "timeout": 600,  # 10 min
    },
    "apply": {
        "script": "apply_watcher.py",
        "args": ["--once"],
        "label": "Submitting applications",
        "timeout": 1800,  # 30 min (multiple applications with delays)
    },
}


def run_step(name: str, config: dict, dry_run: bool = False) -> tuple[bool, str]:
    """Run a single pipeline step, streaming output live. Returns (success, last_lines)."""
    script = BASE_DIR / config["script"]
    if not script.exists():
        return False, f"Script not found: {script}"

    cmd = [sys.executable, str(script)] + config.get("args", [])
    if dry_run and name == "apply":
        cmd.append("--dry-run")

    start = time.time()
    collected: list[str] = []

    try:
        proc = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,   # merge stderr into stdout stream
            text=True,
            bufsize=1,                   # line-buffered
            cwd=BASE_DIR,
        )

        import threading

        def _reader():
            for raw in proc.stdout:
                line = raw.rstrip()
                if not line:
                    continue
                collected.append(line)
                # Indent under the step header so it's visually grouped
                print(f"     {line}", flush=True)

        t = threading.Thread(target=_reader, daemon=True)
        t.start()
        try:
            proc.wait(timeout=config["timeout"])
        except subprocess.TimeoutExpired:
            proc.kill()
            t.join(timeout=2)
            logger.error(f"Step '{name}' timed out after {config['timeout']}s")
            return False, f"Timed out after {config['timeout']}s"
        t.join(timeout=5)

        elapsed = time.time() - start
        success = proc.returncode == 0
        summary = '\n'.join(collected[-5:]) if collected else "(no output)"
        logger.info(f"Step '{name}' completed in {elapsed:.0f}s (exit {proc.returncode})")
        return success, summary

    except Exception as e:
        return False, str(e)


def print_header():
    now = datetime.now().strftime("%A %b %d, %Y %I:%M %p")
    if HAS_RICH:
        console.print(Panel(
            f"[bold purple]Job Auto Pipeline[/bold purple]\n[dim]{now}[/dim]",
            border_style="purple"
        ))
    else:
        print(f"\n{'=' * 50}")
        print(f"  Job Auto Pipeline  |  {now}")
        print(f"{'=' * 50}\n")


def print_step_result(label: str, success: bool, elapsed: float):
    icon = "+" if success else "X"
    status = "Done" if success else "FAILED"
    if HAS_RICH:
        color = "green" if success else "red"
        console.print(f"  [{color}][{icon}] {label}[/{color}] -- {status} ({elapsed:.0f}s)")
    else:
        print(f"  [{icon}] {label} -- {status} ({elapsed:.0f}s)")


def main():
    parser = argparse.ArgumentParser(description="Job automation pipeline")
    parser.add_argument("--dry-run", action="store_true", help="Preview only, no applications submitted")
    parser.add_argument("--step", choices=list(STEPS.keys()), help="Run only a specific step")
    parser.add_argument("--extra-terms", action="append", default=[], dest="extra_terms", help="Extra job search terms to inject into digest")
    args = parser.parse_args()

    print_header()

    if args.dry_run:
        if HAS_RICH:
            console.print("  [yellow]DRY RUN -- applications will not be submitted[/yellow]\n")
        else:
            print("  DRY RUN -- applications will not be submitted\n")

    steps_to_run = {args.step: STEPS[args.step]} if args.step else STEPS
    # Inject extra terms into digest step if provided
    if args.extra_terms and "digest" in steps_to_run:
        import copy
        steps_to_run = copy.deepcopy(steps_to_run)
        for term in args.extra_terms:
            steps_to_run["digest"].setdefault("args", []).extend(["--extra-terms", term])
    results = {}

    for name, config in steps_to_run.items():
        label = config["label"]
        if HAS_RICH:
            console.print(f"\n  [bold]> {label}...[/bold]")
        else:
            print(f"\n  > {label}...")

        start = time.time()
        success, summary = run_step(name, config, dry_run=args.dry_run)
        elapsed = time.time() - start

        results[name] = success
        print_step_result(label, success, elapsed)

        # Don't run apply if tailor failed
        if name == "tailor" and not success:
            logger.warning("Tailor step failed -- skipping apply step")
            if HAS_RICH:
                console.print("  [yellow]Skipping apply -- tailor step failed[/yellow]")
            else:
                print("  Skipping apply -- tailor step failed")
            break

    # Final summary
    total = len(results)
    passed = sum(results.values())
    if HAS_RICH:
        color = "green" if passed == total else "yellow" if passed > 0 else "red"
        console.print(f"\n  [{color}]Pipeline complete: {passed}/{total} steps succeeded[/{color}]\n")
    else:
        print(f"\n  Pipeline complete: {passed}/{total} steps succeeded\n")

    sys.exit(0 if passed == total else 1)


if __name__ == "__main__":
    main()
