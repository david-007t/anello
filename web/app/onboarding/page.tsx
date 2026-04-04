'use client';

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
  work_authorization: string;
  disability_status: string;
  veteran_status: string;
  security_clearance: string;
  resume_uploaded: boolean;

  // Step 3 — Future Self
  ideal_job_title_1: string;
  ideal_job_title_2: string;
  ideal_job_title_3: string;
  target_salary: string;
  desired_locations: string;
  work_life_balance: string;
  company_culture: string;
  skills_to_acquire: string;
  industry_domain: string;
  values_impact: string;
}

const inputClass =
  'w-full px-4 py-3 rounded-xl bg-white/[0.08] border border-white/20 text-white placeholder-white/30 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-transparent';

const labelClass = 'text-sm font-medium text-white/70 mb-1.5 block';

const selectClass = inputClass;

const textareaClass = `${inputClass} resize-none`;

const stepLabels = ['Current Self', 'Future Self', 'Preview'];

const defaultForm: FormState = {
  current_role_title: '',
  years_experience: '',
  key_skills: '',
  current_salary: '',
  current_location: '',
  work_authorization: 'Prefer not to say',
  disability_status: 'Prefer not to say',
  veteran_status: 'Prefer not to say',
  security_clearance: 'None',
  resume_uploaded: false,

  ideal_job_title_1: '',
  ideal_job_title_2: '',
  ideal_job_title_3: '',
  target_salary: '',
  desired_locations: '',
  work_life_balance: 'Prefer not to say',
  company_culture: '',
  skills_to_acquire: '',
  industry_domain: '',
  values_impact: '',
};

function OnboardingInner() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const { isLoaded, isSignedIn, user } = useUser();
  const isEditMode = searchParams.get('mode') === 'edit';
  const stepParam = parseInt(searchParams.get('step') ?? '1', 10);

  const [step, setStep] = useState<1 | 2 | 3 | 4 | 5>(1);
  const [submitting, setSubmitting] = useState(false);
  const [errors, setErrors] = useState<Record<string, string>>({});
  const [dataLoaded, setDataLoaded] = useState(!isEditMode);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const [form, setForm] = useState<FormState>(defaultForm);

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
            work_authorization: data.work_authorization ?? 'Prefer not to say',
            disability_status: data.disability_status ?? 'Prefer not to say',
            veteran_status: data.veteran_status ?? 'Prefer not to say',
            security_clearance: data.security_clearance ?? 'None',
            // Future Self fields
            ideal_job_title_1: data.role ?? '',
            ideal_job_title_2: data.role_2 ?? '',
            ideal_job_title_3: data.role_3 ?? '',
            target_salary: data.min_salary ?? '',
            desired_locations: data.location ?? '',
            work_life_balance: data.work_life_balance ?? 'Prefer not to say',
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

  // Once data is loaded, jump to the requested step
  useEffect(() => {
    if (!dataLoaded) return;
    const target = Math.min(Math.max(stepParam, 1), 5) as 1 | 2 | 3 | 4 | 5;
    setStep(target);
  }, [dataLoaded, stepParam]);

  function set(key: keyof FormState, value: string | boolean) {
    setForm((f) => ({ ...f, [key]: value }));
    setErrors((e) => {
      const next = { ...e };
      delete next[key];
      return next;
    });
  }

  function goToStep(s: 1 | 2 | 3 | 4 | 5) {
    setStep(s);
    window.scrollTo(0, 0);
  }

  function handleStep2Next() {
    const next: Record<string, string> = {};
    if (!form.current_role_title.trim()) {
      next.current_role_title = 'Current role title is required.';
    }
    if (Object.keys(next).length > 0) {
      setErrors(next);
      return;
    }
    setErrors({});
    goToStep(3);
  }

  async function saveCurrentSelf(): Promise<boolean> {
    setSubmitting(true);
    try {
      const res = await fetch('/api/preferences', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          current_role_title: form.current_role_title,
          years_experience: form.years_experience,
          key_skills: form.key_skills,
          current_salary: form.current_salary,
          current_location: form.current_location,
          work_authorization: form.work_authorization,
          disability_status: form.disability_status,
          veteran_status: form.veteran_status,
          security_clearance: form.security_clearance,
        }),
      });
      if (!res.ok) {
        setErrors({ submit: 'Could not save your preferences. Please try again.' });
        setSubmitting(false);
        return false;
      }
    } catch {
      setErrors({ submit: 'Network error. Please check your connection and try again.' });
      setSubmitting(false);
      return false;
    }
    setSubmitting(false);
    return true;
  }

  async function handleStep2SaveAndExit() {
    const next: Record<string, string> = {};
    if (!form.current_role_title.trim()) {
      next.current_role_title = 'Current role title is required.';
    }
    if (Object.keys(next).length > 0) {
      setErrors(next);
      return;
    }
    setErrors({});
    const ok = await saveCurrentSelf();
    if (ok) router.push('/dashboard');
  }

  async function handleStep3Submit() {
    const next: Record<string, string> = {};
    if (!form.ideal_job_title_1.trim()) {
      next.ideal_job_title_1 = 'At least one ideal job title is required.';
    }
    if (Object.keys(next).length > 0) {
      setErrors(next);
      return;
    }
    setErrors({});
    setSubmitting(true);
    try {
      const res = await fetch('/api/preferences', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          role: form.ideal_job_title_1,
          role_2: form.ideal_job_title_2,
          role_3: form.ideal_job_title_3,
          location: form.desired_locations,
          experience_max: form.years_experience,
          min_salary: form.target_salary,
          company_types: form.company_culture,
          skills: form.skills_to_acquire,
          work_life_balance: form.work_life_balance,
          industry_domain: form.industry_domain,
          values_impact: form.values_impact,
        }),
      });
      if (!res.ok) {
        setErrors({ submit: 'Could not save your preferences. Please try again.' });
        setSubmitting(false);
        return;
      }
    } catch {
      setErrors({ submit: 'Network error. Please check your connection and try again.' });
      setSubmitting(false);
      return;
    }
    setSubmitting(false);
    if (isEditMode) {
      router.push('/dashboard');
    } else {
      goToStep(4);
    }
  }

  async function handleStep3SaveAndExit() {
    const next: Record<string, string> = {};
    if (!form.ideal_job_title_1.trim()) {
      next.ideal_job_title_1 = 'At least one ideal job title is required.';
    }
    if (Object.keys(next).length > 0) {
      setErrors(next);
      return;
    }
    setErrors({});
    setSubmitting(true);
    try {
      const res = await fetch('/api/preferences', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          role: form.ideal_job_title_1,
          role_2: form.ideal_job_title_2,
          role_3: form.ideal_job_title_3,
          location: form.desired_locations,
          experience_max: form.years_experience,
          min_salary: form.target_salary,
          company_types: form.company_culture,
          skills: form.skills_to_acquire,
          work_life_balance: form.work_life_balance,
          industry_domain: form.industry_domain,
          values_impact: form.values_impact,
        }),
      });
      if (!res.ok) {
        setErrors({ submit: 'Could not save your preferences. Please try again.' });
        setSubmitting(false);
        return;
      }
    } catch {
      setErrors({ submit: 'Network error. Please check your connection and try again.' });
      setSubmitting(false);
      return;
    }
    setSubmitting(false);
    router.push('/dashboard');
  }

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
            <a href="/" className="text-xl font-black tracking-tight text-white hover:opacity-80 transition-opacity">
              anelo
            </a>
          </div>
        </nav>

        {/* Content */}
        <div className="max-w-lg mx-auto px-6 py-16">
          {/* Step indicator — shown on steps 2-4 only */}
          {step >= 2 && step <= 4 && (
            <>
              <div className="flex items-center gap-4 mb-6">
                {stepLabels.map((label, i) => (
                  <div key={label} className="contents">
                    <div className="flex items-center gap-2">
                      <div
                        className={`w-8 h-8 rounded-full flex items-center justify-center text-sm font-bold transition-colors ${
                          step - 1 === i + 1 ? 'bg-white text-black' : 'bg-white/20 text-white/40'
                        }`}
                      >
                        {String(i + 1).padStart(2, '0')}
                      </div>
                      <span
                        className={`text-sm font-medium transition-colors ${
                          step - 1 === i + 1 ? 'text-white' : 'text-white/30'
                        }`}
                      >
                        {label}
                      </span>
                    </div>
                    {i < stepLabels.length - 1 && <div className="flex-1 h-px bg-white/10" />}
                  </div>
                ))}
              </div>
              <p className="text-xs text-white/40 mb-4">Step {step - 1} of 3</p>
            </>
          )}

          {/* Step 1 — Welcome */}
          {step === 1 && (
            <motion.div
              key="step-1"
              initial={{ opacity: 0, y: 16 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.4, ease: 'easeOut' }}
            >
              <div className="bg-white/5 backdrop-blur-sm border border-white/10 rounded-2xl p-8 space-y-6 text-center">
                <h1 className="text-3xl font-bold text-white">Meet Your Future Self, Powered by Anelo.</h1>
                <p className="text-slate-400 text-sm leading-relaxed">
                  Anelo isn&apos;t just a job search; it&apos;s your personal guide to the career you&apos;ve always envisioned.
                </p>
                <HoverButton
                  onClick={() => goToStep(2)}
                  backgroundColor="rgba(255,255,255,0.05)"
                  glowColor="#9ca3af"
                  textColor="#e5e7eb"
                  hoverTextColor="#ffffff"
                  className="!text-base !py-3 !px-6 !rounded-xl border border-white/10 w-full"
                >
                  Start Your Transformation &rarr;
                </HoverButton>
                {isEditMode && (
                  <a
                    href="/update-preferences"
                    className="block text-sm text-white/40 hover:text-white/60 transition-colors"
                  >
                    &larr; Back to update menu
                  </a>
                )}
              </div>
            </motion.div>
          )}

          {/* Step 2 — Current Self */}
          {step === 2 && (
            <motion.div
              key="step-2"
              initial={{ opacity: 0, y: 16 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.4, ease: 'easeOut' }}
            >
              <div className="bg-white/5 backdrop-blur-sm border border-white/10 rounded-2xl p-8 space-y-6">
                <div>
                  <h1 className="text-3xl font-bold text-white mb-2">Your Starting Point: Who Are You Now?</h1>
                  <p className="text-slate-400 text-sm">This is your foundation. Let Anelo understand where you are today.</p>
                </div>

                {/* Resume upload */}
                <div>
                  <div
                    onClick={() => fileInputRef.current?.click()}
                    className="border-2 border-dashed border-white/20 rounded-xl p-8 text-center cursor-pointer hover:border-white/40 transition-colors"
                  >
                    {form.resume_uploaded ? (
                      <p className="text-sm text-indigo-400">
                        Anelo sees you as a professional ready for your next chapter.
                      </p>
                    ) : (
                      <p className="text-sm text-white/40">
                        Drag &amp; drop your resume here, or click to upload
                      </p>
                    )}
                  </div>
                  <input
                    ref={fileInputRef}
                    type="file"
                    accept=".pdf,.doc,.docx"
                    className="hidden"
                    onChange={() => set('resume_uploaded', true)}
                  />
                </div>

                {/* Divider */}
                <div className="flex items-center gap-3">
                  <div className="flex-1 h-px bg-white/10" />
                  <span className="text-xs text-white/30">or fill in manually</span>
                  <div className="flex-1 h-px bg-white/10" />
                </div>

                {/* Manual fields */}
                <div className="space-y-4">
                  <div>
                    <label htmlFor="current_role_title" className={labelClass}>Current role title *</label>
                    <input
                      id="current_role_title"
                      type="text"
                      value={form.current_role_title}
                      onChange={(e) => set('current_role_title', e.target.value)}
                      placeholder="e.g. Senior Product Manager"
                      className={inputClass}
                      aria-required="true"
                    />
                    {errors.current_role_title && (
                      <p className="text-red-400 text-xs mt-1">{errors.current_role_title}</p>
                    )}
                  </div>
                  <div>
                    <label htmlFor="years_experience" className={labelClass}>Years of experience</label>
                    <input
                      id="years_experience"
                      type="number"
                      min={0}
                      value={form.years_experience}
                      onChange={(e) => set('years_experience', e.target.value)}
                      placeholder="e.g. 5"
                      className={inputClass}
                    />
                  </div>
                  <div>
                    <label htmlFor="key_skills" className={labelClass}>Key skills</label>
                    <input
                      id="key_skills"
                      type="text"
                      value={form.key_skills}
                      onChange={(e) => set('key_skills', e.target.value)}
                      placeholder="e.g. React, Python, SQL"
                      className={inputClass}
                    />
                  </div>
                  <div>
                    <label htmlFor="current_salary" className={labelClass}>Current salary (optional)</label>
                    <input
                      id="current_salary"
                      type="text"
                      value={form.current_salary}
                      onChange={(e) => set('current_salary', e.target.value)}
                      placeholder="e.g. 120000 (optional)"
                      className={inputClass}
                    />
                  </div>
                  <div>
                    <label htmlFor="current_location" className={labelClass}>Current location</label>
                    <input
                      id="current_location"
                      type="text"
                      value={form.current_location}
                      onChange={(e) => set('current_location', e.target.value)}
                      placeholder="e.g. San Francisco, CA"
                      className={inputClass}
                    />
                  </div>
                </div>

                {/* EEO divider */}
                <div className="flex items-center gap-3">
                  <div className="flex-1 h-px bg-white/10" />
                  <span className="text-xs text-white/30">A few quick details to find 100% right opportunities:</span>
                  <div className="flex-1 h-px bg-white/10" />
                </div>

                {/* Dropdowns */}
                <div className="space-y-4">
                  <div>
                    <label htmlFor="work_authorization" className={labelClass}>Work authorization / sponsorship</label>
                    <select
                      id="work_authorization"
                      value={form.work_authorization}
                      onChange={(e) => set('work_authorization', e.target.value)}
                      className={selectClass}
                    >
                      <option value="Prefer not to say">Prefer not to say</option>
                      <option value="Yes, I require sponsorship">Yes, I require sponsorship</option>
                      <option value="No, I don't require sponsorship">No, I don&apos;t require sponsorship</option>
                    </select>
                  </div>
                  <div>
                    <label htmlFor="disability_status" className={labelClass}>Disability status</label>
                    <select
                      id="disability_status"
                      value={form.disability_status}
                      onChange={(e) => set('disability_status', e.target.value)}
                      className={selectClass}
                    >
                      <option value="Prefer not to say">Prefer not to say</option>
                      <option value="Yes">Yes</option>
                      <option value="No">No</option>
                    </select>
                  </div>
                  <div>
                    <label htmlFor="veteran_status" className={labelClass}>Veteran status</label>
                    <select
                      id="veteran_status"
                      value={form.veteran_status}
                      onChange={(e) => set('veteran_status', e.target.value)}
                      className={selectClass}
                    >
                      <option value="Prefer not to say">Prefer not to say</option>
                      <option value="Yes">Yes</option>
                      <option value="No">No</option>
                    </select>
                  </div>
                  <div>
                    <label htmlFor="security_clearance" className={labelClass}>Security clearance</label>
                    <select
                      id="security_clearance"
                      value={form.security_clearance}
                      onChange={(e) => set('security_clearance', e.target.value)}
                      className={selectClass}
                    >
                      <option value="None">None</option>
                      <option value="Confidential">Confidential</option>
                      <option value="Secret">Secret</option>
                      <option value="Top Secret">Top Secret</option>
                      <option value="TS/SCI">TS/SCI</option>
                      <option value="Prefer not to say">Prefer not to say</option>
                    </select>
                  </div>
                </div>

                {errors.submit && (
                  <p className="text-red-400 text-xs text-center">{errors.submit}</p>
                )}

                <div className="flex flex-col gap-3">
                  <HoverButton
                    onClick={handleStep2Next}
                    backgroundColor="rgba(255,255,255,0.05)"
                    glowColor="#9ca3af"
                    textColor="#e5e7eb"
                    hoverTextColor="#ffffff"
                    className="!text-base !py-3 !px-6 !rounded-xl border border-white/10 w-full"
                  >
                    Next: Define Your Future Self &rarr;
                  </HoverButton>
                  {isEditMode && (
                    <button
                      onClick={handleStep2SaveAndExit}
                      disabled={submitting}
                      className="text-sm text-white/50 hover:text-white/80 transition-colors text-center disabled:opacity-40"
                    >
                      {submitting ? 'Saving...' : 'Save & exit'}
                    </button>
                  )}
                  <button
                    onClick={() => goToStep(1)}
                    className="text-sm text-white/40 hover:text-white/60 transition-colors text-center"
                  >
                    &larr; Back
                  </button>
                </div>
              </div>
            </motion.div>
          )}

          {/* Step 3 — Future Self */}
          {step === 3 && (
            <motion.div
              key="step-3"
              initial={{ opacity: 0, y: 16 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.4, ease: 'easeOut' }}
            >
              <div className="bg-white/5 backdrop-blur-sm border border-white/10 rounded-2xl p-8 space-y-6">
                <div>
                  <h1 className="text-3xl font-bold text-white mb-2">Your Destination: Who Do You Want to Be?</h1>
                  <p className="text-slate-400 text-sm">Design your ideal professional future. Anelo will work to make it a reality.</p>
                </div>

                <div className="space-y-4">
                  <div>
                    <label htmlFor="ideal_job_title_1" className={labelClass}>Ideal job title 1 *</label>
                    <input
                      id="ideal_job_title_1"
                      type="text"
                      value={form.ideal_job_title_1}
                      onChange={(e) => set('ideal_job_title_1', e.target.value)}
                      placeholder="e.g. Head of Product"
                      className={inputClass}
                      aria-required="true"
                    />
                    {errors.ideal_job_title_1 && (
                      <p className="text-red-400 text-xs mt-1">{errors.ideal_job_title_1}</p>
                    )}
                  </div>
                  <div>
                    <label htmlFor="ideal_job_title_2" className={labelClass}>Ideal job title 2</label>
                    <input
                      id="ideal_job_title_2"
                      type="text"
                      value={form.ideal_job_title_2}
                      onChange={(e) => set('ideal_job_title_2', e.target.value)}
                      placeholder="e.g. VP Engineering"
                      className={inputClass}
                    />
                  </div>
                  <div>
                    <label htmlFor="ideal_job_title_3" className={labelClass}>Ideal job title 3</label>
                    <input
                      id="ideal_job_title_3"
                      type="text"
                      value={form.ideal_job_title_3}
                      onChange={(e) => set('ideal_job_title_3', e.target.value)}
                      placeholder="e.g. Chief of Staff"
                      className={inputClass}
                    />
                  </div>
                  <div>
                    <label htmlFor="target_salary" className={labelClass}>Target salary</label>
                    <input
                      id="target_salary"
                      type="text"
                      value={form.target_salary}
                      onChange={(e) => set('target_salary', e.target.value)}
                      placeholder="e.g. 180000"
                      className={inputClass}
                    />
                  </div>
                  <div>
                    <label htmlFor="desired_locations" className={labelClass}>Desired locations</label>
                    <input
                      id="desired_locations"
                      type="text"
                      value={form.desired_locations}
                      onChange={(e) => set('desired_locations', e.target.value)}
                      placeholder="e.g. New York, Remote"
                      className={inputClass}
                    />
                  </div>
                  <div>
                    <label htmlFor="work_life_balance" className={labelClass}>Work-life balance</label>
                    <select
                      id="work_life_balance"
                      value={form.work_life_balance}
                      onChange={(e) => set('work_life_balance', e.target.value)}
                      className={selectClass}
                    >
                      <option value="Prefer not to say">Prefer not to say</option>
                      <option value="Balanced (9-5)">Balanced (9-5)</option>
                      <option value="Flexible hours">Flexible hours</option>
                      <option value="Remote-first">Remote-first</option>
                      <option value="High-growth / hustle">High-growth / hustle</option>
                    </select>
                  </div>
                  <div>
                    <label htmlFor="company_culture" className={labelClass}>Company culture</label>
                    <input
                      id="company_culture"
                      type="text"
                      value={form.company_culture}
                      onChange={(e) => set('company_culture', e.target.value)}
                      placeholder="e.g. Startup, mission-driven, collaborative"
                      className={inputClass}
                    />
                  </div>
                  <div>
                    <label htmlFor="skills_to_acquire" className={labelClass}>Skills to acquire</label>
                    <input
                      id="skills_to_acquire"
                      type="text"
                      value={form.skills_to_acquire}
                      onChange={(e) => set('skills_to_acquire', e.target.value)}
                      placeholder="e.g. Leadership, AI/ML, Go"
                      className={inputClass}
                    />
                  </div>
                  <div>
                    <label htmlFor="industry_domain" className={labelClass}>Industry / domain</label>
                    <input
                      id="industry_domain"
                      type="text"
                      value={form.industry_domain}
                      onChange={(e) => set('industry_domain', e.target.value)}
                      placeholder="e.g. FinTech, Healthcare, SaaS"
                      className={inputClass}
                    />
                  </div>
                  <div>
                    <label htmlFor="values_impact" className={labelClass}>Values &amp; impact</label>
                    <textarea
                      id="values_impact"
                      rows={3}
                      value={form.values_impact}
                      onChange={(e) => set('values_impact', e.target.value)}
                      placeholder="What kind of impact do you want to have? (optional)"
                      className={textareaClass}
                    />
                  </div>
                </div>

                <div className="flex flex-col gap-3">
                  {errors.submit && (
                    <p className="text-red-400 text-xs text-center">{errors.submit}</p>
                  )}
                  <HoverButton
                    onClick={handleStep3Submit}
                    disabled={submitting}
                    backgroundColor="rgba(255,255,255,0.05)"
                    glowColor="#9ca3af"
                    textColor="#e5e7eb"
                    hoverTextColor="#ffffff"
                    className="!text-base !py-3 !px-6 !rounded-xl border border-white/10 w-full"
                  >
                    {submitting
                      ? 'Saving...'
                      : isEditMode
                      ? 'Save changes \u2192'
                      : 'See Your First Anelo Digest Preview \u2192'}
                  </HoverButton>
                  {isEditMode && (
                    <button
                      onClick={handleStep3SaveAndExit}
                      disabled={submitting}
                      className="text-sm text-white/50 hover:text-white/80 transition-colors text-center disabled:opacity-40"
                    >
                      {submitting ? 'Saving...' : 'Save & exit'}
                    </button>
                  )}
                  <button
                    onClick={() => goToStep(2)}
                    className="text-sm text-white/40 hover:text-white/60 transition-colors text-center"
                  >
                    &larr; Back
                  </button>
                </div>
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
                  <h1 className="text-3xl font-bold text-white mb-2">Your Future, Delivered: First Anelo Digest Preview</h1>
                  <p className="text-slate-400 text-sm">See how Anelo brings your Future Self to life with personalized opportunities.</p>
                </div>

                {/* Email preview card */}
                <div className="bg-white/[0.04] border border-white/10 rounded-xl p-6 space-y-6">
                  <p className="text-white text-sm">
                    Hello {user?.firstName || 'there'}, your Anelo is here. 👋
                  </p>

                  {/* Job listings */}
                  <div>
                    <h3 className="text-xs font-semibold uppercase tracking-wider text-white/50 mb-3">
                      Your Future Self Likes These Jobs
                    </h3>
                    <div className="space-y-3">
                      {/* Job 1 */}
                      <div className="bg-white/[0.06] rounded-lg p-4 space-y-2">
                        <div className="flex items-start justify-between gap-2">
                          <div>
                            <p className="text-sm font-semibold text-white">Senior Product Manager</p>
                            <p className="text-xs text-white/50">Stripe</p>
                          </div>
                          <span className="text-xs bg-white/10 text-white/60 rounded-full px-2 py-0.5 whitespace-nowrap">Remote</span>
                        </div>
                        <p className="text-xs text-white/40 italic">
                          This role aligns with your ambition to lead product at a high-growth fintech. Stripe&apos;s global impact matches your values around meaningful work.
                        </p>
                        <a href="#" className="text-xs text-indigo-400 hover:text-indigo-300 transition-colors">
                          Apply Directly &rarr;
                        </a>
                      </div>

                      {/* Job 2 */}
                      <div className="bg-white/[0.06] rounded-lg p-4 space-y-2">
                        <div className="flex items-start justify-between gap-2">
                          <div>
                            <p className="text-sm font-semibold text-white">Head of Product</p>
                            <p className="text-xs text-white/50">Notion</p>
                          </div>
                          <span className="text-xs bg-white/10 text-white/60 rounded-full px-2 py-0.5 whitespace-nowrap">San Francisco, CA</span>
                        </div>
                        <p className="text-xs text-white/40 italic">
                          Notion&apos;s collaborative culture is a strong fit for your desired work environment. This position offers the leadership scope your Future Self is targeting.
                        </p>
                        <a href="#" className="text-xs text-indigo-400 hover:text-indigo-300 transition-colors">
                          Apply Directly &rarr;
                        </a>
                      </div>

                      {/* Job 3 */}
                      <div className="bg-white/[0.06] rounded-lg p-4 space-y-2">
                        <div className="flex items-start justify-between gap-2">
                          <div>
                            <p className="text-sm font-semibold text-white">Director of Product Management</p>
                            <p className="text-xs text-white/50">OpenAI</p>
                          </div>
                          <span className="text-xs bg-white/10 text-white/60 rounded-full px-2 py-0.5 whitespace-nowrap">San Francisco, CA</span>
                        </div>
                        <p className="text-xs text-white/40 italic">
                          OpenAI sits at the intersection of AI and massive impact — two themes central to your Future Self profile. A strategic move that aligns with your skills-to-acquire goal.
                        </p>
                        <a href="#" className="text-xs text-indigo-400 hover:text-indigo-300 transition-colors">
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
                    🔒 Auto-Apply is currently in Beta — stay tuned for your invite to unlock even more time!
                  </div>
                </div>

                <div className="flex flex-col gap-3">
                  <HoverButton
                    onClick={() => goToStep(5)}
                    backgroundColor="rgba(255,255,255,0.05)"
                    glowColor="#9ca3af"
                    textColor="#e5e7eb"
                    hoverTextColor="#ffffff"
                    className="!text-base !py-3 !px-6 !rounded-xl border border-white/10 w-full"
                  >
                    Looks good! Send my first digest &rarr;
                  </HoverButton>
                  <button
                    onClick={() => goToStep(3)}
                    className="text-sm text-white/40 hover:text-white/60 transition-colors text-center"
                  >
                    &larr; Refine my profile
                  </button>
                  {isEditMode && (
                    <a
                      href="/update-preferences"
                      className="text-sm text-white/40 hover:text-white/60 transition-colors text-center"
                    >
                      &larr; Back to update menu
                    </a>
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
                <div className="w-14 h-14 rounded-full bg-indigo-500/20 border border-indigo-500/40 flex items-center justify-center mb-6">
                  <svg width="24" height="24" viewBox="0 0 24 24" fill="none">
                    <path d="M5 13l4 4L19 7" stroke="#6366f1" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round" />
                  </svg>
                </div>
                <h1 className="text-3xl font-bold text-white">Your Anelo is Active!</h1>
                <p className="text-slate-400 text-sm leading-relaxed">
                  Your Anelo profile is now active! Your first personalized digest will arrive at{' '}
                  <span className="text-white/70">{user?.primaryEmailAddress?.emailAddress ?? 'your inbox'}</span> shortly.
                </p>

                {/* Next steps */}
                <div className="w-full space-y-3 pt-4 text-left">
                  <div className="flex items-center gap-3 text-sm text-white/60">
                    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" className="shrink-0">
                      <rect x="2" y="4" width="20" height="16" rx="2" stroke="currentColor" strokeWidth="1.5" />
                      <path d="M2 8l10 5 10-5" stroke="currentColor" strokeWidth="1.5" />
                    </svg>
                    <span>Check your email</span>
                  </div>
                  <a
                    href="/dashboard/preferences"
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
                    <span>Manage your Anelo profile</span>
                  </a>
                  <a
                    href="#"
                    className="flex items-center gap-3 text-sm text-white/60 hover:text-white/80 transition-colors"
                  >
                    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" className="shrink-0">
                      <path
                        d="M4 12v6a2 2 0 002 2h12a2 2 0 002-2v-6M16 6l-4-4-4 4M12 2v13"
                        stroke="currentColor"
                        strokeWidth="1.5"
                        strokeLinecap="round"
                        strokeLinejoin="round"
                      />
                    </svg>
                    <span>Invite a friend</span>
                  </a>
                </div>

                <HoverButton
                  onClick={() => router.push('/dashboard')}
                  backgroundColor="rgba(255,255,255,0.05)"
                  glowColor="#9ca3af"
                  textColor="#e5e7eb"
                  hoverTextColor="#ffffff"
                  className="!text-base !py-3 !px-6 !rounded-xl border border-white/10 w-full mt-2"
                >
                  Go to dashboard &rarr;
                </HoverButton>
                {isEditMode && (
                  <a
                    href="/update-preferences"
                    className="text-sm text-white/40 hover:text-white/60 transition-colors"
                  >
                    &larr; Back to update menu
                  </a>
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
