import React from 'react';
import { Link } from 'react-router-dom';
import { Scale, MoveLeft } from 'lucide-react';
import ConstellationBackground from '../components/ConstellationBackground';

export default function TermsOfService() {
  return (
    <div className="relative min-h-screen bg-[#0a0a16] px-6 py-24 text-white overflow-y-auto">
      {/* Dynamic Constellation Background */}
      <div className="absolute inset-0 z-0 opacity-20 pointer-events-none">
        <ConstellationBackground />
      </div>

      {/* Decorative Blur Orbs */}
      <div className="absolute top-10 left-10 h-96 w-96 rounded-full bg-violet/10 blur-[120px] pointer-events-none" />
      <div className="absolute bottom-10 right-10 h-96 w-96 rounded-full bg-mint/5 blur-[120px] pointer-events-none" />

      {/* Main Container */}
      <div className="relative z-10 mx-auto max-w-3xl">
        {/* Back Link */}
        <Link
          to="/"
          className="inline-flex items-center gap-2 mb-8 text-sm text-gray-400 hover:text-white transition-colors"
        >
          <MoveLeft className="h-4 w-4" />
          Back to Home
        </Link>

        {/* Header */}
        <div className="flex items-center gap-4 mb-10 border-b border-white/10 pb-6">
          <div className="flex h-12 w-12 items-center justify-center rounded-xl border border-violet/30 bg-violet/10 text-violet">
            <Scale className="h-6 w-6" />
          </div>
          <div>
            <h1 className="font-display text-3xl font-bold tracking-tight text-white sm:text-4xl">
              Terms of Service
            </h1>
            <p className="text-sm text-gray-400 mt-1">Last Updated: June 20, 2026</p>
          </div>
        </div>

        {/* Content Card */}
        <div className="rounded-2xl border border-white/10 bg-white/[0.02] p-8 md:p-10 backdrop-blur-xl shadow-2xl space-y-6 text-gray-300 leading-relaxed text-sm">
          <section className="space-y-3">
            <h2 className="font-display text-lg font-semibold text-white">1. Agreement to Terms</h2>
            <p>
              By creating a recruiter account or using the HireIQ platform, you agree to be bound by these Terms of Service. If you do not agree to these terms, you must immediately cease all access and use of our platform.
            </p>
          </section>

          <section className="space-y-3">
            <h2 className="font-display text-lg font-semibold text-white">2. Acceptable Use Policy</h2>
            <p>
              You agree to use HireIQ only for lawful purposes in connection with candidate evaluation, recruiting management, and talent acquisition. You must not:
            </p>
            <ul className="list-disc pl-6 space-y-2">
              <li>Upload resume documents containing malware, viruses, or corrupt data.</li>
              <li>Upload resumes or candidate profiles without having the necessary rights, permissions, or legal bases under applicable privacy laws (e.g., GDPR, CCPA).</li>
              <li>Use the scoring models, ranking algorithms, or PDF parse outputs to engage in unlawful employment discrimination.</li>
              <li>Attempt to scrape, reverse-engineer, or breach security controls of the HireIQ platform.</li>
            </ul>
          </section>

          <section className="space-y-3">
            <h2 className="font-display text-lg font-semibold text-white">3. User Accounts & Organization Tenants</h2>
            <p>
              Accounts are grouped under tenant organizations. You are responsible for maintaining the confidentiality of your account credentials, limiting access to invited members, and ensuring all member activities under your tenant comply with these terms. We reserve the right to suspend or terminate accounts that breach security guidelines or act maliciously.
            </p>
          </section>

          <section className="space-y-3">
            <h2 className="font-display text-lg font-semibold text-white">4. Billing, Subscriptions & Refunds</h2>
            <p>
              HireIQ offers tiered pricing plans (Free, Pro, Business, Enterprise) billed on a monthly recurring cycle via Stripe.
            </p>
            <ul className="list-disc pl-6 space-y-2">
              <li>
                <strong className="text-white">Plan Quotas:</strong> Quota limits (such as resume parse uploads or job creation caps) are determined by your current tier. Exceeding these caps will require upgrading your Stripe subscription.
              </li>
              <li>
                <strong className="text-white">Cancellation:</strong> You may cancel your subscription at any time via the billing settings in the dashboard. Cancellations apply to the subsequent billing cycle.
              </li>
              <li>
                <strong className="text-white">Refunds:</strong> Payments are non-refundable. Exceptional cases may be evaluated by support but are subject to our sole discretion.
              </li>
            </ul>
          </section>

          <section className="space-y-3">
            <h2 className="font-display text-lg font-semibold text-white">5. Limitation of Liability</h2>
            <p>
              HireIQ provides candidate scoring, TF-IDF ranking, and bias mitigation audits as advisory, intelligence tools. We do not make final hiring decisions, and we are not liable for any employment actions, loss of data, or operational interruptions. To the maximum extent permitted by law, HireIQ's liability is capped at the total amount paid by you to HireIQ in the preceding 12 months.
            </p>
          </section>

          <section className="space-y-3">
            <h2 className="font-display text-lg font-semibold text-white">6. Changes to Terms</h2>
            <p>
              We reserves the right to modify these terms at any time. We will notify recruiters of significant revisions. Continued use of the platform after updates constitute acceptance of the revised Terms of Service.
            </p>
          </section>
        </div>
      </div>
    </div>
  );
}
