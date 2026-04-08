'use client';

import Link from 'next/link';
import { useState, useRef, useEffect, Suspense } from 'react';
import { useRouter, useSearchParams } from 'next/navigation';
import { useUser } from '@clerk/nextjs';
import { motion } from 'framer-motion';
import { FallingPattern } from '@/components/ui/falling-pattern';
import { HoverButton } from '@/components/ui/hover-button';

interface FormState {
  // Step 2 — Current Self
  current_role_title: string;
  years_experience: string;
  key_skills: string;
  current_salary: string;
  current_location: string;
  resume_uploaded: boolean;

  // Step 3 — Future Self
  ideal_job_title_1: string;
  ideal_job_title_2: string;
  ideal_job_title_3: string;
  target_salary: string;
  desired_locations: string;
  work_arrangement: string;
  location: string;
  work_life_balance: string;
  company_culture: string;
  skills_to_acquire: string;
  industry_domain: string;
  values_impact: string;
}

const inputClass =
  'w-full px-4 py-3 rounded-xl bg-white/[0.08] border border-white/20 text-white placeholder-white/30 text-sm focus:outline-none focus:ring-2 focus:ring-white/50 focus:border-transparent';


const defaultForm: FormState = {
  current_role_title: '',
  years_experience: '',
  key_skills: '',
  current_salary: '',
  current_location: '',
  resume_uploaded: false,

  ideal_job_title_1: '',
  ideal_job_title_2: '',
  ideal_job_title_3: '',
  target_salary: '',
  desired_locations: '',
  work_arrangement: '',
  location: '',
  work_life_balance: '',
  company_culture: '',
  skills_to_acquire: '',
  industry_domain: '',
  values_impact: '',
};

// ─── Conversational question types ───────────────────────────────────────────

type QuestionType = 'single' | 'multi' | 'text' | 'text_input' | 'roles';

interface ConvQuestion {
  id: string;
  question: string;
  subtitle?: string;
  type: QuestionType;
  field?: keyof FormState | (keyof FormState)[];
  options?: { label: string; value: string; emoji?: string }[];
  maxSelect?: number;
  placeholder?: string;
}

const PROFILE_QUESTION_BASE: ConvQuestion[] = [
  {
    id: 'career_stage',
    question: 'Where are you in your career?',
    type: 'single',
    field: 'years_experience',
    options: [
      { label: 'Early career', value: '3', emoji: '🌱' },
      { label: 'Mid-level', value: '8', emoji: '📈' },
      { label: 'Senior', value: '15', emoji: '⭐' },
      { label: 'Director+', value: '20', emoji: '🏆' },
    ],
  },
  {
    id: 'current_role',
    question: "What's your current role?",
    subtitle: 'Be specific — this helps us find the right matches.',
    type: 'text',
    field: 'current_role_title',
    placeholder: 'e.g. Senior Product Manager',
  },
  {
    id: 'move_type',
    question: 'What kind of move are you making?',
    type: 'single',
    field: 'values_impact',
    options: [
      { label: 'Same role, better company', value: 'Lateral move to a stronger company' },
      { label: 'Step up to leadership', value: 'Stepping into leadership' },
      { label: 'Career pivot', value: 'Full career pivot' },
      { label: 'Re-entering the market', value: 'Re-entering the market' },
    ],
  },
  {
    id: 'priorities',
    question: 'What matters most in your next role?',
    subtitle: 'Pick up to 2.',
    type: 'multi',
    field: 'work_life_balance',
    maxSelect: 2,
    options: [
      { label: 'Compensation', value: 'Compensation', emoji: '💰' },
      { label: 'Work-life balance', value: 'Work-life balance', emoji: '⚖️' },
      { label: 'Growth & learning', value: 'Growth & learning', emoji: '🧠' },
      { label: 'Mission & impact', value: 'Mission & impact', emoji: '🎯' },
      { label: 'Startup energy', value: 'Startup energy', emoji: '⚡' },
      { label: 'Stability', value: 'Stability', emoji: '🏛️' },
      { label: 'Remote flexibility', value: 'Remote flexibility', emoji: '🌍' },
      { label: 'Team & culture', value: 'Team & culture', emoji: '🤝' },
    ],
  },
  {
    id: 'work_arrangement',
    question: 'Where do you want to work?',
    type: 'single',
    field: 'work_arrangement',
    options: [
      { label: 'Remote only', value: 'Remote', emoji: '🏠' },
      { label: 'On-site', value: 'On-site', emoji: '🏢' },
      { label: 'Open to anything', value: 'Flexible', emoji: '✈️' },
    ],
  },
  {
    id: 'location',
    question: 'What city are you based in?',
    subtitle: 'e.g. New York, San Francisco, Austin',
    type: 'text_input',
    field: 'location',
  },
  {
    id: 'salary',
    question: "What's your salary target?",
    type: 'single',
    field: 'target_salary',
    options: [
      { label: 'Under $80K', value: '75000' },
      { label: '$80K–$120K', value: '100000' },
      { label: '$120K–$160K', value: '140000' },
      { label: '$160K–$200K', value: '180000' },
      { label: '$200K+', value: '200000' },
      { label: 'Not sure yet', value: 'not_sure' },
    ],
  },
  {
    id: 'target_roles',
    question: 'What roles are you targeting?',
    subtitle: "Up to 3. We'll search all of them.",
    type: 'roles',
    field: ['ideal_job_title_1', 'ideal_job_title_2', 'ideal_job_title_3'],
  },
];

function getProfileQuestions(workArrangement: string): ConvQuestion[] {
  return PROFILE_QUESTION_BASE.filter((question) => {
    if (question.id === 'location' && workArrangement === 'Remote') {
      return false;
    }
    return true;
  });
}

function shortenPreviewBlurb(blurb: string, fallback: string) {
  const source = (blurb || fallback).trim();
  const sentences = source.match(/[^.!?]+[.!?]?/g)?.map((part) => part.trim()).filter(Boolean) ?? [];
  return (sentences.slice(0, 2).join(' ') || fallback).trim();
}

// ─────────────────────────────────────────────────────────────────────────────

function OnboardingInner() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const { isLoaded, isSignedIn, user } = useUser();
  const isEditMode = searchParams.get('mode') === 'edit';
  const stepParam = parseInt(searchParams.get('step') ?? '1', 10);

  const [step, setStep] = useState<2 | 4 | 5>(2);
  const [convStep, setConvStep] = useState(0);
  const [submitting, setSubmitting] = useState(false);
  const [digestFailed, setDigestFailed] = useState(false);
  const [errors, setErrors] = useState<Record<string, string>>({});
  const [dataLoaded, setDataLoaded] = useState(!isEditMode);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const [form, setForm] = useState<FormState>(defaultForm);
  const [resumeFileName, setResumeFileName] = useState<string | null>(null);
  const [resumeUploading, setResumeUploading] = useState(false);
  const [resumeError, setResumeError] = useState('');
  const [blurbs, setBlurbs] = useState({ blurb1: '', blurb2: '', blurb3: '' });
  const [blurbsLoading, setBlurbsLoading] = useState(false);
  const [shareCopied, setShareCopied] = useState(false);
  const profileQuestions = getProfileQuestions(form.work_arrangement);
  const totalProfileSteps = profileQuestions.length + 1;

  // Always: fetch existing resume so returning users see it pre-loaded
  useEffect(() => {
    if (!isLoaded || !isSignedIn) return;
    fetch('/api/resume')
      .then((r) => r.json())
      .then(({ data }) => {
        if (data?.file_name) {
          setResumeFileName(data.file_name);
          setForm((f) => ({ ...f, resume_uploaded: true }));
        }
      })
      .catch(() => {});
  }, [isLoaded, isSignedIn]);

  // In edit mode: fetch existing prefs and pre-fill, then jump to the requested step
  useEffect(() => {
    if (!isEditMode) return;
    if (!isLoaded || !isSignedIn) return;

    fetch('/api/preferences')
      .then((r) => r.json())
      .then(({ data }) => {
        if (data) {
          setForm((f) => ({
            ...f,
            // Current Self fields
            current_role_title: data.current_role_title ?? '',
            years_experience: data.experience_max ?? data.years_experience ?? '',
            key_skills: data.key_skills ?? '',
            current_salary: data.current_salary ?? '',
            current_location: data.current_location ?? '',
            // Future Self fields
            ideal_job_title_1: data.role ?? '',
            ideal_job_title_2: data.role_2 ?? '',
            ideal_job_title_3: data.role_3 ?? '',
            target_salary: data.min_salary ?? '',
            desired_locations: data.desired_locations ?? '',
            work_arrangement: data.work_arrangement ?? '',
            location: data.location ?? '',
            work_life_balance: (data.work_life_balance ?? '').split(', ').filter((v: string) => ['Compensation', 'Work-life balance', 'Growth & learning', 'Mission & impact', 'Startup energy', 'Stability', 'Remote flexibility', 'Team & culture'].includes(v)).join(', '),
            company_culture: data.company_types ?? '',
            skills_to_acquire: data.skills ?? '',
            industry_domain: data.industry_domain ?? '',
            values_impact: data.values_impact ?? '',
          }));
        }
        setDataLoaded(true);
      })
      .catch(() => {
        setDataLoaded(true);
      });
  }, [isEditMode, isLoaded, isSignedIn]);

  // Once data is loaded, jump to the requested step (step 1 no longer exists — redirect to 2)
  useEffect(() => {
    if (!dataLoaded) return;
    const raw = Math.min(Math.max(stepParam, 1), 5);
    const target = (raw <= 2 ? 2 : raw === 3 ? 4 : Math.min(raw, 5)) as 2 | 4 | 5;
    const timeout = window.setTimeout(() => setStep(target), 0);
    return () => window.clearTimeout(timeout);
  }, [dataLoaded, stepParam]);

  useEffect(() => {
    if (step !== 4 || !form.ideal_job_title_1) return;
    let cancelled = false;

    async function loadBlurbs() {
      setBlurbsLoading(true);
      try {
        const response = await fetch('/api/onboarding/preview-blurbs', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            role1: form.ideal_job_title_1,
            role2: form.ideal_job_title_2 || form.ideal_job_title_1,
            role3: form.ideal_job_title_3 || form.ideal_job_title_1,
            values: form.values_impact,
            culture: form.company_culture,
            domain: form.industry_domain,
            skills: form.skills_to_acquire,
          }),
        });
        const data = response.ok ? await response.json() : null;
        if (!cancelled && data) {
          setBlurbs(data);
        }
      } catch {
        // Fall back to the default preview copy below.
      } finally {
        if (!cancelled) {
          setBlurbsLoading(false);
        }
      }
    }

    void loadBlurbs();
    return () => {
      cancelled = true;
    };
  }, [step, form.company_culture, form.ideal_job_title_1, form.ideal_job_title_2, form.ideal_job_title_3, form.industry_domain, form.skills_to_acquire, form.values_impact]);

  function set(key: keyof FormState, value: string | boolean) {
    setForm((f) => {
      if (key === 'work_arrangement' && typeof value === 'string') {
        if (value === 'Remote') {
          return { ...f, work_arrangement: value, location: 'Remote' };
        }
        return {
          ...f,
          work_arrangement: value,
          location: f.location === 'Remote' ? '' : f.location,
        };
      }
      return { ...f, [key]: value };
    });
    setErrors((e) => {
      const next = { ...e };
      delete next[key];
      return next;
    });
  }

  async function handleResumeFile(file: File) {
    setResumeUploading(true);
    setResumeError('');
    const formData = new FormData();
    formData.append('resume', file);
    try {
      const res = await fetch('/api/resume/upload', { method: 'POST', body: formData });
      const data = await res.json();
      if (res.ok) {
        setResumeFileName(file.name);
        set('resume_uploaded', true);
      } else {
        setResumeError(data.error || 'Upload failed.');
      }
    } catch {
      setResumeError('Upload failed. Try again.');
    }
    setResumeUploading(false);
  }

  function goToStep(s: 2 | 4 | 5) {
    setConvStep(0);
    setStep(s);
    window.scrollTo(0, 0);
  }

  async function handleProfileSubmit() {
    setErrors({});
    setSubmitting(true);
    try {
      const res = await fetch('/api/preferences', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          current_role_title: form.current_role_title,
          years_experience: form.years_experience,
          role: form.ideal_job_title_1,
          role_2: form.ideal_job_title_2,
          role_3: form.ideal_job_title_3,
          location: form.work_arrangement === 'Remote' ? 'Remote' : form.location,
          work_arrangement: form.work_arrangement,
          experience_max: form.years_experience,
          min_salary: form.target_salary === 'not_sure' ? '' : form.target_salary,
          company_types: form.company_culture,
          skills: form.skills_to_acquire,
          work_life_balance: form.work_life_balance,
          industry_domain: form.industry_domain,
          values_impact: form.values_impact,
        }),
      });
      if (!res.ok) {
        const errData = await res.json().catch(() => ({}));
        setErrors({ submit: errData.error || 'Could not save your preferences. Please try again.' });
        setSubmitting(false);
        return;
      }
    } catch (e) {
      console.error('Preferences network error:', e);
      setErrors({ submit: 'Network error. Please check your connection and try again.' });
      setSubmitting(false);
      return;
    }
    setSubmitting(false);
    goToStep(4);
  }

  async function handleCopyInviteLink() {
    try {
      await navigator.clipboard.writeText(window.location.origin);
      setShareCopied(true);
      window.setTimeout(() => setShareCopied(false), 2000);
    } catch {
      setShareCopied(false);
    }
  }

  async function handleSendDigest() {
    setSubmitting(true);
    try {
      const res = await fetch('/api/run-digest', { method: 'POST' });
      if (!res.ok) setDigestFailed(true);
    } catch {
      setDigestFailed(true);
    }
    setSubmitting(false);
    goToStep(5);
  }

  // ── Conversational question renderer (defined inside component — uses form/set/errors state) ──

  function renderConvQuestion(
    questions: ConvQuestion[],
    currentIdx: number,
    onNext: () => void,
    onBack: () => void,
    isLastQuestion: boolean,
    nextLabel: string = 'Continue →',
    stepOffset: number = 0,
    totalSteps?: number,
  ) {
    const q = questions[currentIdx];
    if (!q) return null;

    const handleSingleSelect = (value: string) => {
      if (Array.isArray(q.field)) return;
      set(q.field as keyof FormState, value);
    };

    const handleMultiToggle = (value: string) => {
      if (Array.isArray(q.field)) return;
      const key = q.field as keyof FormState;
      setForm((prev) => {
        const current = (prev[key] as string) || '';
        const parts = current ? current.split(', ').filter(Boolean) : [];
        const idx = parts.indexOf(value);
        let next: string[];
        if (idx >= 0) {
          next = parts.filter((_, i) => i !== idx);
        } else if (!q.maxSelect || parts.length < q.maxSelect) {
          next = [...parts, value];
        } else {
          next = parts;
        }
        return { ...prev, [key]: next.join(', ') };
      });
      setErrors((e) => { const n = { ...e }; delete n[key as string]; return n; });
    };

    const isMultiSelected = (value: string) => {
      if (Array.isArray(q.field)) return false;
      const current = (form[q.field as keyof FormState] as string) || '';
      return current.split(', ').includes(value);
    };

    const multiCount = () => {
      if (Array.isArray(q.field)) return 0;
      const current = (form[q.field as keyof FormState] as string) || '';
      return current ? current.split(', ').filter(Boolean).length : 0;
    };

    const hasSingleSelection = () => {
      if (Array.isArray(q.field) || !q.options) return false;
      return q.options.some(opt => opt.value === form[q.field as keyof FormState]);
    };

    const getTextValue = () => {
      if (Array.isArray(q.field)) return '';
      return String(form[q.field as keyof FormState] ?? '').trim();
    };

    const validateCurrentQuestion = () => {
      if (q.id === 'current_role' && !getTextValue()) {
        setErrors({ current_role_title: 'Please add your current role.' });
        return false;
      }
      if (q.id === 'location' && !getTextValue()) {
        setErrors({ location: 'Please add your city.' });
        return false;
      }
      return true;
    };

    return (
      <motion.div
        key={q.id}
        initial={{ opacity: 0, x: 20 }}
        animate={{ opacity: 1, x: 0 }}
        exit={{ opacity: 0, x: -20 }}
        transition={{ duration: 0.25, ease: 'easeOut' }}
        className="space-y-6"
      >
        {/* Progress */}
        <div className="flex items-center gap-1.5 mb-2">
          {Array.from({ length: totalSteps ?? questions.length }).map((_, i) => (
            <div
              key={i}
              className={`h-1 rounded-full flex-1 transition-all ${
                i < stepOffset + currentIdx ? 'bg-white' : i === stepOffset + currentIdx ? 'bg-white/70' : 'bg-white/10'
              }`}
            />
          ))}
        </div>

        {/* Question */}
        <div>
          <p className="text-xs text-white/40 font-mono mb-2">{stepOffset + currentIdx + 1} / {totalSteps ?? questions.length}</p>
          <h2 className="text-2xl font-bold text-white leading-snug">{q.question}</h2>
          {q.subtitle && <p className="text-sm text-white/40 mt-1">{q.subtitle}</p>}
        </div>

        {/* Options */}
        {q.type === 'single' && q.options && (
          <div className="space-y-4">
            <div className="grid grid-cols-1 gap-2 sm:grid-cols-2">
              {q.options.map((opt) => {
                const selected = !Array.isArray(q.field) && form[q.field as keyof FormState] === opt.value;
                return (
                  <button
                    key={opt.value}
                    onClick={() => handleSingleSelect(opt.value)}
                    className={`flex items-center gap-3 px-4 py-3.5 rounded-xl border text-left transition-all ${
                      selected
                        ? 'border-white/80 bg-white/10 text-white'
                        : 'border-white/10 bg-white/[0.03] text-white/70 hover:border-white/25 hover:bg-white/[0.06] hover:text-white'
                    }`}
                  >
                    {opt.emoji && <span className="text-lg shrink-0">{opt.emoji}</span>}
                    <span className="text-sm font-medium">{opt.label}</span>
                    {selected && (
                      <span className="ml-auto shrink-0">
                        <svg width="14" height="14" viewBox="0 0 14 14" fill="none">
                          <path d="M2 7l4 4 6-7" stroke="#ffffff" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
                        </svg>
                      </span>
                    )}
                  </button>
                );
              })}
            </div>
            <HoverButton
              onClick={onNext}
              disabled={!hasSingleSelection()}
              backgroundColor="rgba(255,255,255,0.05)"
              glowColor="#9ca3af"
              textColor="#e5e7eb"
              hoverTextColor="#ffffff"
              className="!text-sm !py-2.5 !px-5 !rounded-xl border border-white/10 w-full"
            >
              {nextLabel}
            </HoverButton>
          </div>
        )}

        {q.type === 'multi' && q.options && (
          <div className="space-y-4">
            <div className="grid grid-cols-1 gap-2 sm:grid-cols-2">
              {q.options.map((opt) => {
                const selected = isMultiSelected(opt.value);
                return (
                  <button
                    key={opt.value}
                    onClick={() => handleMultiToggle(opt.value)}
                    className={`flex items-center gap-3 px-4 py-3.5 rounded-xl border text-left transition-all ${
                      selected
                        ? 'border-white bg-white/20 text-white ring-1 ring-white/30'
                        : 'border-white/10 bg-white/[0.03] text-white/70 hover:border-white/25 hover:bg-white/[0.06] hover:text-white'
                    }`}
                  >
                    {opt.emoji && <span className="text-lg shrink-0">{opt.emoji}</span>}
                    <span className="text-sm font-medium">{opt.label}</span>
                    {selected && (
                      <span className="ml-auto shrink-0">
                        <svg width="14" height="14" viewBox="0 0 14 14" fill="none">
                          <path d="M2 7l4 4 6-7" stroke="#ffffff" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
                        </svg>
                      </span>
                    )}
                  </button>
                );
              })}
            </div>
            <HoverButton
              onClick={onNext}
              disabled={multiCount() === 0}
              backgroundColor="rgba(255,255,255,0.05)"
              glowColor="#9ca3af"
              textColor="#e5e7eb"
              hoverTextColor="#ffffff"
              className="!text-sm !py-2.5 !px-5 !rounded-xl border border-white/10 w-full"
            >
              {nextLabel}
            </HoverButton>
          </div>
        )}

        {q.type === 'text' && (
          <div className="space-y-4">
            <input
              type="text"
              value={!Array.isArray(q.field) ? (form[q.field as keyof FormState] as string) : ''}
              onChange={(e) => {
                if (!Array.isArray(q.field)) set(q.field as keyof FormState, e.target.value);
              }}
              onKeyDown={(e) => e.key === 'Enter' && onNext()}
              placeholder={q.placeholder}
              className={inputClass}
              autoFocus
            />
            <HoverButton
              onClick={() => {
                if (!validateCurrentQuestion()) return;
                onNext();
              }}
              disabled={!getTextValue()}
              backgroundColor="rgba(255,255,255,0.05)"
              glowColor="#9ca3af"
              textColor="#e5e7eb"
              hoverTextColor="#ffffff"
              className="!text-sm !py-2.5 !px-5 !rounded-xl border border-white/10 w-full"
            >
              {nextLabel}
            </HoverButton>
            {q.field && !Array.isArray(q.field) && errors[q.field] && (
              <p className="text-red-400 text-xs">{errors[q.field]}</p>
            )}
          </div>
        )}

        {q.type === 'text_input' && (
          <div className="space-y-4">
            <input
              type="text"
              value={!Array.isArray(q.field) ? (form[q.field as keyof FormState] as string) : ''}
              onChange={(e) => {
                if (!Array.isArray(q.field)) set(q.field as keyof FormState, e.target.value);
              }}
              onKeyDown={(e) => e.key === 'Enter' && onNext()}
              placeholder={q.placeholder}
              className={inputClass}
              autoFocus
            />
            <HoverButton
              onClick={() => {
                if (!validateCurrentQuestion()) return;
                onNext();
              }}
              disabled={!getTextValue()}
              backgroundColor="rgba(255,255,255,0.05)"
              glowColor="#9ca3af"
              textColor="#e5e7eb"
              hoverTextColor="#ffffff"
              className="!text-sm !py-2.5 !px-5 !rounded-xl border border-white/10 w-full"
            >
              {nextLabel}
            </HoverButton>
            {q.field && !Array.isArray(q.field) && errors[q.field] && (
              <p className="text-red-400 text-xs">{errors[q.field]}</p>
            )}
          </div>
        )}

        {q.type === 'roles' && Array.isArray(q.field) && (
          <div className="space-y-4">
            {q.field.map((fieldKey, i) => (
              <div key={fieldKey}>
                <input
                  type="text"
                  value={form[fieldKey] as string}
                  onChange={(e) => set(fieldKey, e.target.value)}
                  placeholder={i === 0 ? 'Primary role, e.g. Head of Product' : i === 1 ? 'Role 2 (optional)' : 'Role 3 (optional)'}
                  className={inputClass}
                  autoFocus={i === 0}
                />
              </div>
            ))}
            {errors.ideal_job_title_1 && (
              <p className="text-red-400 text-xs">{errors.ideal_job_title_1}</p>
            )}
            <HoverButton
              onClick={onNext}
              backgroundColor="rgba(255,255,255,0.05)"
              glowColor="#9ca3af"
              textColor="#e5e7eb"
              hoverTextColor="#ffffff"
              className="!text-sm !py-2.5 !px-5 !rounded-xl border border-white/10 w-full"
            >
              {nextLabel}
            </HoverButton>
          </div>
        )}

        {/* Back */}
        <button
          onClick={onBack}
          className="text-sm text-white/30 hover:text-white/60 transition-colors"
        >
          ← Back
        </button>
      </motion.div>
    );
  }

  // ─── Guards ───────────────────────────────────────────────────────────────

  if (!isLoaded || (isEditMode && !dataLoaded)) {
    return (
      <div className="min-h-screen bg-black flex items-center justify-center">
        <div className="w-6 h-6 border-2 border-white/20 border-t-white rounded-full animate-spin" />
      </div>
    );
  }

  if (!isSignedIn) {
    router.push('/sign-in');
    return null;
  }

  return (
    <div className="min-h-screen text-white">
      <FallingPattern
        color="rgba(255,255,255,0.3)"
        backgroundColor="#000000"
        duration={120}
        blurIntensity="1em"
        density={1}
        className="fixed inset-0 z-0"
      />
      <div className="relative z-10">
        {/* Nav */}
        <nav className="sticky top-0 z-50 border-b border-white/10 bg-black/80 backdrop-blur-md">
          <div className="max-w-6xl mx-auto px-6 h-16 flex items-center">
            <Link href="/" className="text-xl font-black tracking-tight text-white hover:opacity-80 transition-opacity">
              anelo
            </Link>
          </div>
        </nav>

        {/* Content */}
        <div className="max-w-lg mx-auto px-6 py-16">

          {/* Step 2 — Profile questions (conversational) */}
          {step === 2 && (
            <motion.div
              key="step-2"
              initial={{ opacity: 0, y: 16 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.4, ease: 'easeOut' }}
            >
              <div className="bg-white/5 backdrop-blur-sm border border-white/10 rounded-2xl p-8 space-y-6">
                {/* Resume upload — always shown as Q0 */}
                {convStep === 0 && (
                  <motion.div
                    key="resume-upload"
                    initial={{ opacity: 0, x: 20 }}
                    animate={{ opacity: 1, x: 0 }}
                    transition={{ duration: 0.25 }}
                    className="space-y-6"
                  >
                    {/* Progress */}
                    <div className="flex items-center gap-1.5 mb-2">
                      {Array.from({ length: totalProfileSteps }).map((_, i) => (
                        <div key={i} className={`h-1 rounded-full flex-1 transition-all ${i === 0 ? 'bg-white/70' : 'bg-white/10'}`} />
                      ))}
                    </div>
                    <p className="text-xs text-white/40 font-mono mb-2">1 / {totalProfileSteps}</p>

                    <div>
                      <h2 className="text-2xl font-bold text-white leading-snug">Drop your resume.</h2>
                      <p className="text-sm text-white/40 mt-1">We&apos;ll extract what we can so you answer fewer questions.</p>
                    </div>

                    <div
                      onClick={() => !resumeUploading && fileInputRef.current?.click()}
                      className={`border-2 border-dashed rounded-xl p-10 text-center transition-colors ${resumeUploading ? 'cursor-wait border-white/20' : 'cursor-pointer hover:border-white/40 border-white/20'}`}
                    >
                      {resumeUploading ? (
                        <p className="text-sm text-white/50">Uploading…</p>
                      ) : resumeFileName ? (
                        <div className="space-y-1">
                          <p className="text-sm text-white/80 font-medium">✓ {resumeFileName}</p>
                          <p className="text-xs text-white/30">Click to replace</p>
                        </div>
                      ) : (
                        <div className="space-y-2">
                          <p className="text-base font-medium text-white/60">Drop or click to upload</p>
                          <p className="text-xs text-white/30">PDF or DOCX · Max 5MB</p>
                        </div>
                      )}
                      {resumeError && <p className="text-xs text-red-400 mt-2">{resumeError}</p>}
                    </div>
                    <input
                      ref={fileInputRef}
                      type="file"
                      accept=".pdf,.doc,.docx"
                      className="hidden"
                      onChange={(e) => { const f = e.target.files?.[0]; if (f) handleResumeFile(f); }}
                    />

                    <HoverButton
                      onClick={() => setConvStep(1)}
                      backgroundColor="rgba(255,255,255,0.05)"
                      glowColor="#9ca3af"
                      textColor="#e5e7eb"
                      hoverTextColor="#ffffff"
                      className="!text-sm !py-2.5 !px-5 !rounded-xl border border-white/10 w-full"
                    >
                      {resumeFileName ? 'Looks good →' : 'Skip for now →'}
                    </HoverButton>

                  </motion.div>
                )}

                {/* Conversational questions Q1-Q7 (convStep 1-7) */}
                {convStep >= 1 && convStep <= profileQuestions.length && renderConvQuestion(
                  profileQuestions,
                  convStep - 1,
                  async () => {
                    // Validate roles question
                    if (profileQuestions[convStep - 1]?.id === 'target_roles') {
                      if (!form.ideal_job_title_1.trim()) {
                        setErrors({ ideal_job_title_1: 'At least one role is required.' });
                        return;
                      }
                      setErrors({});
                    }
                    if (convStep < profileQuestions.length) {
                      setConvStep(convStep + 1);
                    } else {
                      await handleProfileSubmit();
                    }
                  },
                  () => {
                    if (convStep > 1) setConvStep(convStep - 1);
                    else setConvStep(0);
                  },
                  convStep === profileQuestions.length,
                  convStep === profileQuestions.length ? (submitting ? 'Saving...' : 'See my digest preview →') : 'Continue →',
                  1,
                  totalProfileSteps,
                )}
              </div>
            </motion.div>
          )}

          {/* Step 4 — Digest Preview */}
          {step === 4 && (
            <motion.div
              key="step-4"
              initial={{ opacity: 0, y: 16 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.4, ease: 'easeOut' }}
            >
              <div className="bg-white/5 backdrop-blur-sm border border-white/10 rounded-2xl p-8 space-y-6">
                <div>
                  <h1 className="text-3xl font-bold text-white mb-2">Here&apos;s what your digest looks like.</h1>
                  <p className="text-slate-400 text-sm">A preview of the personalized job matches Anelo will send you.</p>
                </div>

                {/* Email preview card */}
                <div className="bg-white/[0.04] border border-white/10 rounded-xl p-6 space-y-6">
                  <p className="text-white text-sm">
                    Hello {user?.firstName || 'there'}, your Anelo is here. 👋
                  </p>

                  {/* Job listings */}
                  <div>
                    <h3 className="text-xs font-semibold uppercase tracking-wider text-white/50 mb-3">
                      Your matches
                    </h3>
                    <div className="space-y-3">
                      {/* Job 1 */}
                      <div className="bg-white/[0.06] rounded-lg p-4 space-y-2">
                        <div className="flex items-start justify-between gap-2">
                          <div>
                            <p className="text-sm font-semibold text-white">{form.ideal_job_title_1 || 'your role'}</p>
                            <p className="text-xs text-white/50">Stripe</p>
                          </div>
                          <span className="text-xs bg-white/10 text-white/60 rounded-full px-2 py-0.5 whitespace-nowrap">{form.work_arrangement === 'Remote' ? 'Remote' : 'Remote'}</span>
                        </div>
                        <p className="text-xs text-white/40 italic">{blurbsLoading ? 'Writing your preview...' : shortenPreviewBlurb(blurbs.blurb1, 'Stripe looks like a strong fit for the kind of role you want next. The team and scope line up well with your profile.')}</p>
                        <a href="#" className="text-xs text-white/50 hover:text-white/80 transition-colors">
                          Apply Directly &rarr;
                        </a>
                      </div>

                      {/* Job 2 */}
                      <div className="bg-white/[0.06] rounded-lg p-4 space-y-2">
                        <div className="flex items-start justify-between gap-2">
                          <div>
                            <p className="text-sm font-semibold text-white">{form.ideal_job_title_2 || form.ideal_job_title_1 || 'your role'}</p>
                            <p className="text-xs text-white/50">Notion</p>
                          </div>
                          <span className="text-xs bg-white/10 text-white/60 rounded-full px-2 py-0.5 whitespace-nowrap">{form.work_arrangement === 'Remote' ? 'Remote' : form.location || 'San Francisco, CA'}</span>
                        </div>
                        <p className="text-xs text-white/40 italic">{blurbsLoading ? 'Writing your preview...' : shortenPreviewBlurb(blurbs.blurb2, 'Notion fits the kind of team environment you said you want. It looks like the sort of role where you could have real ownership quickly.')}</p>
                        <a href="#" className="text-xs text-white/50 hover:text-white/80 transition-colors">
                          Apply Directly &rarr;
                        </a>
                      </div>

                      {/* Job 3 */}
                      <div className="bg-white/[0.06] rounded-lg p-4 space-y-2">
                        <div className="flex items-start justify-between gap-2">
                          <div>
                            <p className="text-sm font-semibold text-white">{form.ideal_job_title_3 || form.ideal_job_title_1 || 'your role'}</p>
                            <p className="text-xs text-white/50">OpenAI</p>
                          </div>
                          <span className="text-xs bg-white/10 text-white/60 rounded-full px-2 py-0.5 whitespace-nowrap">{form.work_arrangement === 'Remote' ? 'Remote' : form.location || 'San Francisco, CA'}</span>
                        </div>
                        <p className="text-xs text-white/40 italic">{blurbsLoading ? 'Writing your preview...' : shortenPreviewBlurb(blurbs.blurb3, 'OpenAI lines up with the ambitious direction you are aiming for. It is the kind of high-upside role Anelo is built to surface early.')}</p>
                        <a href="#" className="text-xs text-white/50 hover:text-white/80 transition-colors">
                          Apply Directly &rarr;
                        </a>
                      </div>
                    </div>
                  </div>

                  {/* Anelo's Extra Step */}
                  <div>
                    <h3 className="text-xs font-semibold uppercase tracking-wider text-white/50 mb-3">
                      Anelo&apos;s Extra Step
                    </h3>
                    <p className="text-xs text-white/40 mb-3">We pull company signals and LinkedIn data to give you context before you apply.</p>
                    <div className="space-y-2 text-xs text-white/50">
                      <p>
                        <span className="text-white/70 font-medium">Insider Insight:</span>{' '}
                        Stripe recently expanded their payments infrastructure team — now is an optimal time to apply.
                      </p>
                      <p>
                        <span className="text-white/70 font-medium">Skill Spotlight:</span>{' '}
                        Product leaders with AI fluency are 3x more likely to receive callbacks in 2025.
                      </p>
                      <p>
                        <span className="text-white/70 font-medium">Networking Nudge:</span>{' '}
                        You have 2nd-degree LinkedIn connections at Notion — consider a warm outreach before applying.
                      </p>
                    </div>
                  </div>

                  {/* Beta badge */}
                  <div className="text-center text-xs text-white/40 border border-white/10 rounded-lg px-4 py-2 mt-4">
                    Coming soon: one-click apply, straight from your digest.
                  </div>
                </div>

                <div className="flex flex-col gap-3">
                  <HoverButton
                    onClick={handleSendDigest}
                    disabled={submitting}
                    backgroundColor="rgba(255,255,255,0.05)"
                    glowColor="#9ca3af"
                    textColor="#e5e7eb"
                    hoverTextColor="#ffffff"
                    className="!text-base !py-3 !px-6 !rounded-xl border border-white/10 w-full"
                  >
                    {submitting ? 'Sending...' : 'Looks good! Send my first digest \u2192'}
                  </HoverButton>
                  <button
                    onClick={() => goToStep(2)}
                    className="text-sm text-white/40 hover:text-white/60 transition-colors text-center"
                  >
                    &larr; Refine my profile
                  </button>
                  {isEditMode && (
                    <Link
                      href="/update-preferences"
                      className="text-sm text-white/40 hover:text-white/60 transition-colors text-center"
                    >
                      &larr; Back to update menu
                    </Link>
                  )}
                </div>
              </div>
            </motion.div>
          )}

          {/* Step 5 — Confirmation */}
          {step === 5 && (
            <motion.div
              key="step-5"
              initial={{ opacity: 0, y: 16 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.4, ease: 'easeOut' }}
            >
              <div className="bg-white/5 backdrop-blur-sm border border-white/10 rounded-2xl p-8 flex flex-col items-center text-center space-y-4">
                <div className="w-14 h-14 rounded-full bg-white/10 border border-white/20 flex items-center justify-center mb-6">
                  <svg width="24" height="24" viewBox="0 0 24 24" fill="none">
                    <path d="M5 13l4 4L19 7" stroke="#ffffff" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round" />
                  </svg>
                </div>
                <h1 className="text-3xl font-bold text-white">Your Anelo is Active!</h1>
                {digestFailed ? (
                  <div className="w-full bg-yellow-500/10 border border-yellow-500/30 rounded-xl px-4 py-3 text-sm text-yellow-300 text-left">
                    We couldn&apos;t trigger your digest right now — we&apos;ll retry automatically. Check back soon.
                  </div>
                ) : (
                  <p className="text-slate-400 text-sm leading-relaxed">
                    Your Anelo profile is now active! Your first personalized digest will arrive at{' '}
                    <span className="text-white/70">{user?.primaryEmailAddress?.emailAddress ?? 'your inbox'}</span> in about 20 minutes.
                  </p>
                )}

                {/* Next steps */}
                <div className="w-full space-y-3 pt-4 text-left">
                  <div className="flex items-center gap-3 text-sm text-white/60">
                    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" className="shrink-0">
                      <rect x="2" y="4" width="20" height="16" rx="2" stroke="currentColor" strokeWidth="1.5" />
                      <path d="M2 8l10 5 10-5" stroke="currentColor" strokeWidth="1.5" />
                    </svg>
                    <span>Check your email</span>
                  </div>
                  <p className="text-xs text-white/30 pl-[30px]">Don&apos;t see it? Check your spam folder.</p>
                    <Link
                      href="/update-preferences"
                      className="flex items-center gap-3 text-sm text-white/60 hover:text-white/80 transition-colors"
                    >
                      <svg width="18" height="18" viewBox="0 0 24 24" fill="none" className="shrink-0">
                        <circle cx="12" cy="12" r="3" stroke="currentColor" strokeWidth="1.5" />
                        <path
                        d="M12 1v2m0 18v2m11-11h-2M3 12H1m17.07-7.07l-1.41 1.41M6.34 17.66l-1.41 1.41m14.14 0l-1.41-1.41M6.34 6.34L4.93 4.93"
                        stroke="currentColor"
                        strokeWidth="1.5"
                        strokeLinecap="round"
                      />
                    </svg>
                    <span>Change your roles, salary, or location →</span>
                  </Link>
                </div>

                <div className="w-full rounded-xl border border-white/10 bg-white/[0.04] px-4 py-4 text-left">
                  <p className="text-sm font-medium text-white">Know someone else job hunting?</p>
                  <p className="text-xs text-white/45 mt-1">Share Anelo to give them priority beta access.</p>
                  <div className="mt-3 flex flex-col gap-2 sm:flex-row">
                    <HoverButton
                      onClick={handleCopyInviteLink}
                      backgroundColor="rgba(255,255,255,0.05)"
                      glowColor="#9ca3af"
                      textColor="#e5e7eb"
                      hoverTextColor="#ffffff"
                      className="!text-sm !py-2.5 !px-4 !rounded-xl border border-white/10"
                    >
                      {shareCopied ? 'Invite link copied' : 'Copy invite link'}
                    </HoverButton>
                    <Link
                      href="/"
                      className="inline-flex items-center justify-center rounded-xl border border-white/10 px-4 py-2.5 text-sm text-white/60 hover:text-white/80 transition-colors"
                    >
                      View Anelo home
                    </Link>
                  </div>
                </div>

                <HoverButton
                  onClick={() => router.push('/')}
                  backgroundColor="rgba(255,255,255,0.05)"
                  glowColor="#9ca3af"
                  textColor="#e5e7eb"
                  hoverTextColor="#ffffff"
                  className="!text-base !py-3 !px-6 !rounded-xl border border-white/10 w-full mt-2"
                >
                  Back to home &rarr;
                </HoverButton>
                {isEditMode && (
                  <Link
                    href="/update-preferences"
                    className="text-sm text-white/40 hover:text-white/60 transition-colors"
                  >
                    &larr; Back to update menu
                  </Link>
                )}
              </div>
            </motion.div>
          )}
        </div>
      </div>
    </div>
  );
}

export default function OnboardingPage() {
  return (
    <Suspense
      fallback={
        <div className="min-h-screen bg-black flex items-center justify-center">
          <div className="w-6 h-6 border-2 border-white/20 border-t-white rounded-full animate-spin" />
        </div>
      }
    >
      <OnboardingInner />
    </Suspense>
  );
}
