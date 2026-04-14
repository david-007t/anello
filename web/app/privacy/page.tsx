export default function PrivacyPage() {
  return (
    <main className="min-h-screen bg-black text-white px-6 py-16">
      <div className="mx-auto max-w-3xl">
        <h1 className="mb-3 text-3xl font-bold">Privacy Policy</h1>
        <p className="mb-10 text-sm text-slate-400">Last updated: April 14, 2026</p>

        <div className="space-y-8 text-slate-300">
          <section className="space-y-3">
            <h2 className="text-xl font-semibold text-white">Overview</h2>
            <p className="leading-relaxed">
              Anelo helps you set up a job-search profile, scan job listings, and send a curated digest to your inbox.
              This policy explains what we collect, how we use it, and how you can ask us to delete it.
            </p>
          </section>

          <section className="space-y-3">
            <h2 className="text-xl font-semibold text-white">What We Collect</h2>
            <p className="leading-relaxed">
              When you use Anelo, we may collect the information you provide directly, including your name, email
              address, Google account details made available through sign-in, resume uploads, onboarding answers,
              job preferences, and any actions you take in the product.
            </p>
          </section>

          <section className="space-y-3">
            <h2 className="text-xl font-semibold text-white">How We Use Your Information</h2>
            <p className="leading-relaxed">
              We use your information to create and maintain your account, personalize your job digest, improve job
              matching, send product emails, operate the service, prevent abuse, and understand how Anelo is being
              used during early access.
            </p>
          </section>

          <section className="space-y-3">
            <h2 className="text-xl font-semibold text-white">Service Providers</h2>
            <p className="leading-relaxed">
              We use third-party providers to operate Anelo, including providers for authentication, hosting,
              databases, storage, email delivery, analytics, and job discovery. Those providers may process your
              information only as needed to help us run the service.
            </p>
          </section>

          <section className="space-y-3">
            <h2 className="text-xl font-semibold text-white">Job Data and Resume Data</h2>
            <p className="leading-relaxed">
              If you upload a resume, we store it so we can help tailor your profile and improve matching. We may
              also store the extracted text needed to power matching and product features. You should avoid uploading
              sensitive information that is not relevant to your job search.
            </p>
          </section>

          <section className="space-y-3">
            <h2 className="text-xl font-semibold text-white">Retention and Deletion</h2>
            <p className="leading-relaxed">
              We keep your information for as long as needed to operate Anelo during early access, unless you ask us
              to delete it sooner. To request deletion of your account or data, email{" "}
              <a className="text-white underline underline-offset-4" href="mailto:waitlist@anelo.io">
                waitlist@anelo.io
              </a>
              .
            </p>
          </section>

          <section className="space-y-3">
            <h2 className="text-xl font-semibold text-white">Security</h2>
            <p className="leading-relaxed">
              We use reasonable technical and organizational safeguards to protect your data, but no system is
              perfectly secure. If we learn of a material security issue affecting your information, we will take
              reasonable steps to investigate and respond.
            </p>
          </section>

          <section className="space-y-3">
            <h2 className="text-xl font-semibold text-white">Changes</h2>
            <p className="leading-relaxed">
              We may update this policy as Anelo evolves. When we do, we will update the date at the top of this
              page.
            </p>
          </section>

          <section className="space-y-3">
            <h2 className="text-xl font-semibold text-white">Contact</h2>
            <p className="leading-relaxed">
              If you have privacy questions, email{" "}
              <a className="text-white underline underline-offset-4" href="mailto:waitlist@anelo.io">
                waitlist@anelo.io
              </a>
              .
            </p>
          </section>
        </div>
      </div>
    </main>
  );
}
