import React from 'react';
import { Link } from 'react-router-dom';
import { Shield, MoveLeft } from 'lucide-react';
import ConstellationBackground from '../components/ConstellationBackground';

export default function PrivacyPolicy() {
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
            <Shield className="h-6 w-6" />
          </div>
          <div>
            <h1 className="font-display text-3xl font-bold tracking-tight text-white sm:text-4xl">
              Privacy Policy
            </h1>
            <p className="text-sm text-gray-400 mt-1">Last Updated: June 20, 2026</p>
          </div>
        </div>

        {/* Content Card */}
        <div className="rounded-2xl border border-white/10 bg-white/[0.02] p-8 md:p-10 backdrop-blur-xl shadow-2xl space-y-6 text-gray-300 leading-relaxed text-sm">
          <section className="space-y-3">
            <h2 className="font-display text-lg font-semibold text-white">1. Introduction</h2>
            <p>
              Welcome to HireIQ. We respect your privacy and are committed to protecting the Personal Identifiable Information (PII) of our users, recruiters, and candidates. This Privacy Policy describes how we collect, use, and share information when you use our platform.
            </p>
          </section>

          <section className="space-y-3">
            <h2 className="font-display text-lg font-semibold text-white">2. Data We Collect</h2>
            <p>
              We collect the following categories of information to provide and improve our services:
            </p>
            <ul className="list-disc pl-6 space-y-2">
              <li>
                <strong className="text-white">Recruiter Accounts:</strong> Name, business email, password, role, company name, and payment/billing information.
              </li>
              <li>
                <strong className="text-white">Candidate Profiles & Resumes:</strong> Raw text extracted from uploaded resumes, names, emails, phone numbers, career levels, work histories, education backgrounds, skills, social profiles (LinkedIn, GitHub), interview question scorecards, and developer insights.
              </li>
              <li>
                <strong className="text-white">Usage & Diagnostic Data:</strong> Product interactions, performance metrics, navigation patterns, and error logs.
              </li>
            </ul>
          </section>

          <section className="space-y-3">
            <h2 className="font-display text-lg font-semibold text-white">3. How We Use Your Data</h2>
            <p>
              Your data is processed only for explicit, legitimate recruiting purposes, including:
            </p>
            <ul className="list-disc pl-6 space-y-2">
              <li>Parsing and analyzing resumes to extract technical features.</li>
              <li>Calculating objective match scores and candidate rank listings.</li>
              <li>Anonymizing profiles for bias-blind hiring metrics.</li>
              <li>Facilitating internal recruiter summaries and interview question generation.</li>
              <li>Monitoring platform stability, rate-limiting, and error diagnostics.</li>
            </ul>
          </section>

          <section className="space-y-3">
            <h2 className="font-display text-lg font-semibold text-white">4. Data Sharing & Third Parties</h2>
            <p>
              We do not sell your personal data. We share information only with trusted service providers necessary to operate the platform:
            </p>
            <ul className="list-disc pl-6 space-y-2">
              <li>
                <strong className="text-white">Supabase:</strong> For cloud database storage, user authentication, and secure backups.
              </li>
              <li>
                <strong className="text-white">Stripe:</strong> For secure subscription billing and payment processing.
              </li>
              <li>
                <strong className="text-white">Resend:</strong> For automated transactional emails and member invitations.
              </li>
              <li>
                <strong className="text-white">Sentry:</strong> For application performance monitoring and error telemetry.
              </li>
              <li>
                <strong className="text-white">PostHog:</strong> For analyzing platform usage analytics and user experience flow.
              </li>
            </ul>
          </section>

          <section className="space-y-3">
            <h2 className="font-display text-lg font-semibold text-white">5. Security & Encryption at Rest</h2>
            <p>
              Candidate resume texts containing PII are symmetrically encrypted using Fernet keys before storage in our cloud database to prevent unauthorized access. All network communication is encrypted in transit over HTTPS/TLS.
            </p>
          </section>

          <section className="space-y-3">
            <h2 className="font-display text-lg font-semibold text-white">6. Data Retention & GDPR Compliance</h2>
            <p>
              We retain candidate data as long as the recruiter account is active or until a deletion request is received. Under GDPR regulations, candidates and recruiters have the right to request:
            </p>
            <ul className="list-disc pl-6 space-y-2">
              <li>
                <strong className="text-white">Access & Export:</strong> Exporting all candidate PII data stored in the database.
              </li>
              <li>
                <strong className="text-white">The Right to be Forgotten:</strong> Permanently deleting candidate profile logs, scores, and resume texts.
              </li>
            </ul>
            <p className="mt-2">
              To invoke these rights, users can access the **GDPR Export** or **Delete Profile (GDPR Forget)** actions directly within the Candidate Profile interface in their recruiter dashboard.
            </p>
          </section>

          <section className="space-y-3">
            <h2 className="font-display text-lg font-semibold text-white">7. Contact Us</h2>
            <p>
              If you have any questions about this Privacy Policy or wish to assert your data rights, contact us at <span className="text-violet">support@hireiq.dev</span>.
            </p>
          </section>
        </div>
      </div>
    </div>
  );
}
