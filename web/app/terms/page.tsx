export default function TermsPage() {
  return (
    <main className="min-h-screen bg-black text-white px-6 py-16">
      <div className="mx-auto max-w-3xl">
        <h1 className="mb-3 text-3xl font-bold">Terms of Service</h1>
        <p className="mb-10 text-sm text-slate-400">Last updated: April 14, 2026</p>

        <div className="space-y-8 text-slate-300">
          <section className="space-y-3">
            <h2 className="text-xl font-semibold text-white">Overview</h2>
            <p className="leading-relaxed">
              These Terms of Service govern your use of Anelo during early access. By using Anelo, you agree to these
              terms.
            </p>
          </section>

          <section className="space-y-3">
            <h2 className="text-xl font-semibold text-white">Early Access</h2>
            <p className="leading-relaxed">
              Anelo is an early-access product. Features may change, improve, or be removed at any time. We may add
              limits, pause access, or update the service as we learn from real usage.
            </p>
          </section>

          <section className="space-y-3">
            <h2 className="text-xl font-semibold text-white">Acceptable Use</h2>
            <p className="leading-relaxed">
              You agree not to abuse the service, interfere with the product, attempt to gain unauthorized access,
              scrape the app in ways we do not allow, reverse engineer protected systems, or use Anelo for unlawful
              activity.
            </p>
          </section>

          <section className="space-y-3">
            <h2 className="text-xl font-semibold text-white">Your Content</h2>
            <p className="leading-relaxed">
              You are responsible for the information you upload or submit, including resumes, preferences, and any
              profile details. You should only provide information you have the right to share.
            </p>
          </section>

          <section className="space-y-3">
            <h2 className="text-xl font-semibold text-white">No Guarantee of Results</h2>
            <p className="leading-relaxed">
              Anelo helps surface job opportunities, but we do not guarantee that any listing is available, accurate,
              current, or a fit for you. We also do not guarantee interviews, offers, or outcomes from using the
              product.
            </p>
          </section>

          <section className="space-y-3">
            <h2 className="text-xl font-semibold text-white">Suspension and Termination</h2>
            <p className="leading-relaxed">
              We may suspend or terminate access to Anelo at any time, including if we believe someone is abusing the
              service, creating risk for other users, or violating these terms.
            </p>
          </section>

          <section className="space-y-3">
            <h2 className="text-xl font-semibold text-white">Disclaimers and Liability</h2>
            <p className="leading-relaxed">
              Anelo is provided on an &quot;as is&quot; and &quot;as available&quot; basis. To the fullest extent permitted by law, we
              disclaim warranties and are not liable for indirect, incidental, special, consequential, or punitive
              damages arising from your use of the service.
            </p>
          </section>

          <section className="space-y-3">
            <h2 className="text-xl font-semibold text-white">Changes</h2>
            <p className="leading-relaxed">
              We may update these terms from time to time. When we do, we will update the date at the top of this
              page. Continued use of Anelo after updates means you accept the revised terms.
            </p>
          </section>

          <section className="space-y-3">
            <h2 className="text-xl font-semibold text-white">Contact</h2>
            <p className="leading-relaxed">
              Questions about these terms can be sent to{" "}
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
