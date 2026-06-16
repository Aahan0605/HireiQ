import React, { useState } from 'react';
import { Link } from 'react-router-dom';
import { motion, AnimatePresence } from 'framer-motion';
import { Check, Sparkles, HelpCircle, ArrowRight, Star, Quote, ChevronDown, Award, Github, Linkedin, Terminal, Calendar, ShieldCheck } from 'lucide-react';
import ConstellationBackground from '../components/ConstellationBackground';

export default function Landing() {
  const [activeFaq, setActiveFaq] = useState(null);

  const testimonials = [
    {
      name: "Sarah Jenkins",
      role: "CTO, TalentForge",
      quote: "HireiQ transformed our engineering hiring process. We identified our top React architect within minutes using their interactive skill graphs.",
      stars: 5,
      avatar: "SJ"
    },
    {
      name: "Dave Miller",
      role: "Engineering Lead, StackHire",
      quote: "The GitHub sync feature is a game-changer. We no longer have to manually audit portfolios; we get direct signals on code frequency and stars.",
      stars: 5,
      avatar: "DM"
    },
    {
      name: "Elena Rostova",
      role: "VP of People, Meridian Labs",
      quote: "Highly accurate scoring and deterministic weighting. The match rates saved our recruiters over 20 hours a week of manual filtering.",
      stars: 5,
      avatar: "ER"
    }
  ];

  const faqs = [
    {
      question: "What is the accuracy of the match scores?",
      answer: "Our match score engine is deterministic, combining TF-IDF resume keyword parsing, GitHub commit frequency, Leetcode stats, and portfolio evaluations using customizable recruiter weights."
    },
    {
      question: "Can I run this offline?",
      answer: "Yes, HireiQ features a robust client-side session fallback using localStorage and client-side processing, allowing full demonstration even when backend servers are disconnected."
    },
    {
      question: "How does the Blind mode help?",
      answer: "By anonymizing candidate names, locations, and portfolios, recruiters can evaluate skills objectively, reducing demographic hiring bias."
    },
    {
      question: "Can I integrate with Supabase or PostgreSQL?",
      answer: "Yes, the system is fully compatible with both SQLite for local file-based storage and Supabase for cloud-ready Postgres database deployments."
    }
  ];

  const pricingPlans = [
    {
      name: "Free Trial",
      price: "$0",
      description: "Basic candidate evaluation and resume parsing tool.",
      features: [
        "5 resume parses / month",
        "Basic TF-IDF match score",
        "Candidate List View",
        "Anonymized Bias Audit"
      ],
      buttonText: "Try Free Demo",
      buttonLink: "/dashboard",
      popular: false
    },
    {
      name: "Recruiter Pro",
      price: "$79",
      description: "Power features for scaling teams and active recruiters.",
      features: [
        "Unlimited CV uploads",
        "Kanban Hiring pipeline board",
        "Advanced search filter controls",
        "Real-time GitHub profile sync",
        "AI-Generated Interview Q&A"
      ],
      buttonText: "Upgrade to Pro",
      buttonLink: "/settings",
      popular: true
    },
    {
      name: "Enterprise",
      price: "Custom",
      description: "Dedicated database infrastructure and security controls.",
      features: [
        "Custom scoring weight templates",
        "DB Sync (Supabase/PostgreSQL)",
        "PDF and CSV reports",
        "Dedicated Support SLA"
      ],
      buttonText: "Contact Sales",
      buttonLink: "/settings",
      popular: false
    }
  ];

  return (
    <div className="relative min-h-screen bg-[#07070e] text-gray-200 overflow-hidden font-sans">
      {/* Animated premium constellation network background */}
      <ConstellationBackground />

      {/* Decorative premium ambient glow highlights */}
      <div className="absolute top-1/4 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[600px] h-[600px] bg-emerald-500/10 rounded-full blur-[150px] pointer-events-none z-0" />
      <div className="absolute top-1/3 left-1/4 w-[400px] h-[400px] bg-cyan-500/10 rounded-full blur-[120px] pointer-events-none z-0" />
      <div className="absolute top-1/2 right-1/4 w-[500px] h-[500px] bg-violet/10 rounded-full blur-[140px] pointer-events-none z-0" />

      {/* Subtle modern mesh grid overlay */}
      <div className="absolute inset-0 bg-[linear-gradient(to_right,rgba(255,255,255,0.02)_1px,transparent_1px),linear-gradient(to_bottom,rgba(255,255,255,0.02)_1px,transparent_1px)] bg-[size:4rem_4rem] [mask-image:radial-gradient(ellipse_60%_50%_at_50%_50%,#000_70%,transparent_100%)] pointer-events-none z-0" />

      {/* Navigation Header */}
      <header className="fixed top-0 left-0 right-0 z-40 bg-[#07070e]/85 backdrop-blur-md border-b border-white/5 py-4 px-6">
        <div className="max-w-6xl mx-auto flex items-center justify-between">
          <Link to="/" className="flex items-center gap-2 text-white font-black text-xl tracking-wider hover:opacity-90 transition-opacity">
            <Award className="h-6 w-6 text-emerald-400" />
            <span>HIRE<span className="text-cyan-400">IQ</span></span>
          </Link>
          <nav className="hidden md:flex items-center gap-8 text-sm font-semibold text-gray-400">
            <a href="#features" className="hover:text-emerald-400 transition-colors">Features</a>
            <a href="#pricing" className="hover:text-emerald-400 transition-colors">Pricing</a>
            <a href="#faq" className="hover:text-emerald-400 transition-colors">FAQs</a>
          </nav>
          <div className="flex items-center gap-4">
            <Link to="/signin" className="text-sm font-semibold text-gray-400 hover:text-white transition-colors">
              Sign In
            </Link>
            <Link to="/dashboard" className="rounded-xl bg-gradient-to-r from-emerald-500 to-cyan-500 px-5 py-2 text-sm font-bold text-white shadow-lg shadow-emerald-500/10 hover:scale-[1.02] hover:shadow-emerald-500/20 active:scale-95 transition-all">
              Launch App
            </Link>
          </div>
        </div>
      </header>

      {/* Hero Section */}
      <section className="relative z-10 flex min-h-screen flex-col items-center justify-center px-6 pt-32 pb-20 max-w-5xl mx-auto text-center">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6 }}
          className="mb-6 inline-flex items-center gap-2 rounded-full border border-white/10 bg-white/5 backdrop-blur-md px-4 py-1.5 text-xs font-semibold text-gray-300"
        >
          <span className="flex h-2 w-2 rounded-full bg-emerald-400 animate-pulse" />
          ⚡ Interactive AI Applicant Tracking System
        </motion.div>

        <motion.h1
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6, delay: 0.1 }}
          className="mb-6 text-4xl font-black tracking-tight text-white sm:text-6xl md:text-7xl leading-[1.1] text-balance"
        >
          Hire the best, <br />
          <span className="bg-gradient-to-r from-emerald-400 to-cyan-400 bg-clip-text text-transparent">
            faster than ever.
          </span>
        </motion.h1>

        <motion.p
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6, delay: 0.2 }}
          className="mx-auto mb-10 max-w-2xl text-sm text-gray-400 sm:text-base leading-relaxed text-balance"
        >
          Leverage automated resume parsing, interactive skill graphs, blind bias audits, and live social portfolio footprints to identify and hire elite technical talent.
        </motion.p>

        <motion.div 
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6, delay: 0.3 }}
          className="flex flex-col items-center justify-center gap-4 sm:flex-row mb-16"
        >
          <Link
            to="/dashboard"
            className="group relative inline-flex h-12 items-center justify-center overflow-hidden rounded-xl bg-gradient-to-r from-emerald-500 to-cyan-500 px-8 text-sm font-bold text-white shadow-lg shadow-emerald-500/20 hover:scale-[1.02] active:scale-95 transition-all duration-200"
          >
            Go to Recruiter Dashboard
          </Link>
          <Link
            to="/settings"
            className="inline-flex h-12 items-center justify-center rounded-xl border border-white/10 bg-white/5 backdrop-blur-md px-8 text-sm font-semibold text-white hover:bg-white/10 active:scale-95 transition-all duration-200"
          >
            Explore B2B Plans
          </Link>
        </motion.div>

        {/* Interactive Dashboard Showcase Widget */}
        <motion.div
          initial={{ opacity: 0, y: 40 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.8, delay: 0.4 }}
          className="w-full max-w-4xl mx-auto border border-white/10 rounded-2xl bg-[#131326]/40 backdrop-blur-md p-6 shadow-2xl relative overflow-hidden"
        >
          {/* Mock Window Controls */}
          <div className="flex items-center gap-2 mb-6 border-b border-white/5 pb-4">
            <div className="w-2.5 h-2.5 rounded-full bg-red-500/60" />
            <div className="w-2.5 h-2.5 rounded-full bg-yellow-500/60" />
            <div className="w-2.5 h-2.5 rounded-full bg-green-500/60" />
            <span className="text-[10px] text-gray-500 font-mono ml-4">dashboard.hireiq.app/candidates</span>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-6 text-left">
            {/* Left Mock Sidebar */}
            <div className="bg-white/5 rounded-xl border border-white/5 p-4 space-y-4 flex flex-col justify-between">
              <div className="space-y-3">
                <div className="h-3.5 bg-white/10 rounded w-2/3" />
                <div className="h-7 bg-emerald-500/10 border border-emerald-500/20 rounded-lg p-2 flex items-center justify-between">
                  <span className="text-[10px] font-bold text-emerald-400">Total Candidates</span>
                  <span className="text-[10px] font-black text-white">48</span>
                </div>
                <div className="h-7 bg-cyan-500/10 border border-cyan-500/20 rounded-lg p-2 flex items-center justify-between">
                  <span className="text-[10px] font-bold text-cyan-400">GitHub Verified</span>
                  <span className="text-[10px] font-black text-white">32</span>
                </div>
              </div>
              <div className="space-y-2 pt-2 border-t border-white/5">
                <div className="h-2 bg-white/5 rounded w-full" />
                <div className="h-2 bg-white/5 rounded w-4/5" />
                <div className="h-2 bg-white/5 rounded w-5/6" />
              </div>
            </div>

            {/* Middle/Right Mock Content (Interactive Candidate Card) */}
            <div className="md:col-span-2 bg-[#19192f] border border-white/10 rounded-xl p-5 relative overflow-hidden flex flex-col justify-between">
              <div>
                <div className="flex justify-between items-start mb-3">
                  <div>
                    <h4 className="text-sm font-bold text-white flex items-center gap-2">
                      Aahan Gajera <span className="text-[9px] px-2 py-0.5 rounded-full bg-cyan-400/10 text-cyan-400 font-semibold border border-cyan-400/20">Mid-Level</span>
                    </h4>
                    <p className="text-[10px] text-gray-500 mt-0.5">Sourced via Resume upload</p>
                  </div>
                  <div className="px-2 py-0.5 rounded-full bg-emerald-500/10 text-emerald-400 text-xs font-bold border border-emerald-500/20">
                    67/100 Match
                  </div>
                </div>
                
                <p className="text-[11px] text-gray-400 leading-relaxed mb-4">
                  "Aahan Gajera is a Mid-Level Software Engineer candidate with a verified background in Bachelor of Technology (B.Tech), demonstrating 2.0 years of experience. Live engineering analytics successfully verified practical usage and competence in React and Python (score: 67/100)."
                </p>
              </div>

              {/* Mock Badges */}
              <div className="flex flex-wrap gap-1.5 pt-3 border-t border-white/5">
                <span className="text-[9px] px-2.5 py-0.5 rounded-full bg-white/5 text-gray-300 border border-white/5">FastAPI</span>
                <span className="text-[9px] px-2.5 py-0.5 rounded-full bg-white/5 text-gray-300 border border-white/5">React</span>
                <span className="text-[9px] px-2.5 py-0.5 rounded-full bg-white/5 text-gray-300 border border-white/5">PostgreSQL</span>
                <span className="text-[9px] px-2.5 py-0.5 rounded-full bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 flex items-center gap-1"><Github size={8} /> GitHub Verified</span>
              </div>
            </div>
          </div>
        </motion.div>
      </section>

      {/* Features Showcase Section */}
      <section id="features" className="relative z-10 py-28 px-6 max-w-6xl mx-auto border-t border-white/5">
        <h2 className="text-3xl font-black text-white text-center mb-4">Designed for Engineering Sourcing</h2>
        <p className="text-xs text-gray-400 text-center mb-16 max-w-md mx-auto">
          We combine deterministic screening tools with developer social footprints to automate and secure technical sourcing.
        </p>

        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6">
          <div className="bg-white/5 border border-white/5 rounded-2xl p-6 hover:border-emerald-500/20 hover:bg-white/10 transition-all duration-300 flex flex-col justify-between min-h-[200px]">
            <div>
              <span className="text-2xl mb-4 block">🤖</span>
              <h3 className="font-bold text-sm text-white mb-2">AI Resume Parsing</h3>
              <p className="text-[11px] text-gray-400 leading-relaxed">
                Scan semantic structures to extract skills, experience years, degrees, and certificates within 5 seconds.
              </p>
            </div>
          </div>
          <div className="bg-white/5 border border-white/5 rounded-2xl p-6 hover:border-cyan-500/20 hover:bg-white/10 transition-all duration-300 flex flex-col justify-between min-h-[200px]">
            <div>
              <span className="text-2xl mb-4 block">📈</span>
              <h3 className="font-bold text-sm text-white mb-2">GitHub Footprint Sync</h3>
              <p className="text-[11px] text-gray-400 leading-relaxed">
                Verify actual commits, star counts, polyglot language frequencies, and test coverage indicators directly.
              </p>
            </div>
          </div>
          <div className="bg-white/5 border border-white/5 rounded-2xl p-6 hover:border-violet/20 hover:bg-white/10 transition-all duration-300 flex flex-col justify-between min-h-[200px]">
            <div>
              <span className="text-2xl mb-4 block">🔒</span>
              <h3 className="font-bold text-sm text-white mb-2">Anonymized Bias Audit</h3>
              <p className="text-[11px] text-gray-400 leading-relaxed">
                Hide demographic data, locations, and names with one click to enforce objective skill-based reviews.
              </p>
            </div>
          </div>
          <div className="bg-white/5 border border-white/5 rounded-2xl p-6 hover:border-yellow-500/20 hover:bg-white/10 transition-all duration-300 flex flex-col justify-between min-h-[200px]">
            <div>
              <span className="text-2xl mb-4 block">📅</span>
              <h3 className="font-bold text-sm text-white mb-2">Greedy Scheduling</h3>
              <p className="text-[11px] text-gray-400 leading-relaxed">
                Schedule technical interviews without conflicts using greedy activity interval optimizations.
              </p>
            </div>
          </div>
        </div>
      </section>

      {/* Testimonials Section */}
      <section className="relative z-10 py-20 px-6 border-y border-white/5 bg-[#0a0a15]/40 backdrop-blur-sm">
        <div className="max-w-4xl mx-auto">
          <h2 className="text-3xl font-bold text-white text-center mb-12 flex items-center justify-center gap-2">
            <Quote className="text-emerald-400" /> What Engineering Teams Say
          </h2>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            {testimonials.map((t, idx) => (
              <div 
                key={idx} 
                className="bg-white/5 backdrop-blur-md border border-white/5 rounded-2xl p-6 hover:border-emerald-500/20 transition-all flex flex-col justify-between"
              >
                <div>
                  <div className="flex gap-1 mb-4">
                    {Array(t.stars).fill(0).map((_, i) => (
                      <Star key={i} size={14} className="fill-yellow-400 text-yellow-400" />
                    ))}
                  </div>
                  <p className="text-gray-300 text-xs italic leading-relaxed mb-6">"{t.quote}"</p>
                </div>
                <div className="flex items-center gap-3">
                  <div className="w-8 h-8 rounded-full bg-gradient-to-br from-emerald-500 to-cyan-500 flex items-center justify-center text-xs font-bold text-white">
                    {t.avatar}
                  </div>
                  <div>
                    <h4 className="text-xs font-bold text-white">{t.name}</h4>
                    <p className="text-[10px] text-gray-500">{t.role}</p>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Pricing Grid Section */}
      <section id="pricing" className="relative z-10 py-24 px-6 max-w-5xl mx-auto">
        <h2 className="text-3xl font-black text-white text-center mb-4">Transparent Recruiter Plans</h2>
        <p className="text-xs text-gray-400 text-center mb-16 max-w-md mx-auto">
          Choose a tier designed to support seed-stage startups through to growing enterprise recruiting teams.
        </p>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
          {pricingPlans.map((plan, idx) => (
            <div 
              key={idx}
              className={`rounded-2xl border p-6 flex flex-col justify-between bg-white/5 backdrop-blur-md relative overflow-hidden transition-all ${
                plan.popular 
                  ? 'border-emerald-500/50 shadow-lg' 
                  : 'border-white/5 hover:border-white/10'
              }`}
            >
              {plan.popular && (
                <div className="absolute top-0 right-0 bg-emerald-500/20 text-emerald-400 text-[8px] font-black tracking-widest px-3 py-1 rounded-bl">
                  POPULAR
                </div>
              )}
              <div>
                <h3 className="font-bold text-sm text-white mb-2">{plan.name}</h3>
                <div className="text-3xl font-black text-white mb-2">{plan.price}</div>
                <p className="text-xs text-gray-400 leading-relaxed mb-6">{plan.description}</p>
                <div className="h-px bg-white/5 mb-6" />
                <ul className="space-y-3 mb-8">
                  {plan.features.map((f, i) => (
                    <li key={i} className="flex items-center gap-2 text-xs text-gray-300">
                      <Check size={12} className="text-emerald-400 flex-shrink-0" /> {f}
                    </li>
                  ))}
                </ul>
              </div>
              <Link
                to={plan.buttonLink}
                className={`w-full py-2.5 rounded-xl text-center text-xs font-bold transition-all ${
                  plan.popular
                    ? 'bg-gradient-to-r from-emerald-500 to-cyan-500 text-white shadow-lg hover:opacity-95'
                    : 'bg-white/5 hover:bg-white/10 text-white border border-white/10'
                }`}
              >
                {plan.buttonText}
              </Link>
            </div>
          ))}
        </div>
      </section>

      {/* FAQ Accordion Section */}
      <section id="faq" className="relative z-10 py-20 px-6 border-t border-white/5 bg-[#0a0a15]/40 backdrop-blur-sm">
        <div className="max-w-3xl mx-auto">
          <h2 className="text-3xl font-bold text-white text-center mb-12 flex items-center justify-center gap-2">
            <HelpCircle className="text-emerald-400" /> Frequently Asked Questions
          </h2>

          <div className="space-y-4">
            {faqs.map((faq, idx) => {
              const isOpen = activeFaq === idx;
              return (
                <div 
                  key={idx}
                  className="bg-white/5 border border-white/5 rounded-2xl overflow-hidden transition-all duration-300"
                >
                  <button
                    onClick={() => setActiveFaq(isOpen ? null : idx)}
                    className="w-full px-6 py-4 flex justify-between items-center text-left text-white hover:bg-white/5 transition-all"
                  >
                    <span className="text-sm font-semibold">{faq.question}</span>
                    <ChevronDown 
                      size={16} 
                      className={`text-gray-400 transition-transform duration-300 ${isOpen ? 'rotate-180 text-emerald-400' : ''}`} 
                    />
                  </button>
                  <AnimatePresence initial={false}>
                    {isOpen && (
                      <motion.div
                        initial={{ height: 0 }}
                        animate={{ height: 'auto' }}
                        exit={{ height: 0 }}
                        transition={{ duration: 0.2 }}
                        className="overflow-hidden"
                      >
                        <div className="px-6 pb-5 pt-1 text-xs text-gray-400 leading-relaxed border-t border-white/5">
                          {faq.answer}
                        </div>
                      </motion.div>
                    )}
                  </AnimatePresence>
                </div>
              );
            })}
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer className="relative z-10 py-12 px-6 border-t border-white/5 text-center text-xs text-gray-500">
        <p className="mb-2">© 2026 HireiQ. Transforming AI recruiting intelligence globally.</p>
        <p>Built with React, FastAPI, Supabase, and Tailwind CSS.</p>
      </footer>
    </div>
  );
}
