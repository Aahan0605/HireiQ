import React, { useState } from 'react';
import { Link } from 'react-router-dom';
import { motion, AnimatePresence } from 'framer-motion';
import { Check, Sparkles, HelpCircle, ArrowRight, Star, Quote, ChevronDown, Award } from 'lucide-react';
import ConstellationBackground from '../components/ConstellationBackground';

export default function Landing() {
  const [activeFaq, setActiveFaq] = useState(null);
  const [activeTestimonial, setActiveTestimonial] = useState(0);

  const testimonials = [
    {
      name: "Sarah Jenkins",
      role: "CTO, NetScale",
      quote: "HireiQ transformed our engineering hiring process. We identified our top React architect within minutes using their interactive skill graphs.",
      stars: 5,
      avatar: "SJ"
    },
    {
      name: "Dave Miller",
      role: "Engineering Lead, WebFlow",
      quote: "The GitHub sync feature is a game-changer. We no longer have to manually audit portfolios; we get direct signals on code frequency and stars.",
      stars: 5,
      avatar: "DM"
    },
    {
      name: "Elena Rostova",
      role: "VP of People, AlphaTech",
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
    <div className="relative min-h-screen bg-bg text-theme-1 overflow-hidden">
      {/* Animated premium constellation network background */}
      <ConstellationBackground />

      {/* Hero Section */}
      <section className="relative z-10 flex min-h-[90vh] flex-col items-center justify-center px-6 pt-20 max-w-5xl mx-auto text-center">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6 }}
          className="mb-6 inline-flex items-center gap-2 rounded-full border border-white/10 bg-surface/30 backdrop-blur-md px-4 py-1.5 text-xs font-semibold text-gray-300"
        >
          <span className="flex h-2 w-2 rounded-full bg-emerald-400 animate-pulseGlow shadow-glow-emerald" />
          ⚡ Interactive AI Applicant Tracking System
        </motion.div>

        <motion.h1
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6, delay: 0.1 }}
          className="mb-8 text-5xl font-black tracking-tight text-white sm:text-7xl leading-[1.1]"
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
          className="mx-auto mb-10 max-w-2xl text-base text-gray-400 sm:text-lg leading-relaxed text-balance"
        >
          Leverage automated resume parsing, interactive skill graphs, blind bias audits, and social portfolio footprints to build elite teams.
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
            className="inline-flex h-12 items-center justify-center rounded-xl border border-white/10 bg-surface/30 backdrop-blur-md px-8 text-sm font-semibold text-white hover:bg-white/5 active:scale-95 transition-all duration-200"
          >
            Explore B2B Plans
          </Link>
        </motion.div>
      </section>

      {/* Testimonials section */}
      <section className="relative z-10 py-20 px-6 border-y border-white/5 bg-[#0a0a15]/40 backdrop-blur-sm">
        <div className="max-w-4xl mx-auto">
          <h2 className="text-3xl font-bold text-white text-center mb-12 flex items-center justify-center gap-2">
            <Quote className="text-emerald-400" /> What Engineering Teams Say
          </h2>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            {testimonials.map((t, idx) => (
              <div 
                key={idx} 
                className="bg-surface/30 backdrop-blur-md border border-white/5 rounded-2xl p-6 hover:border-emerald-500/20 transition-all flex flex-col justify-between"
              >
                <div>
                  <div className="flex gap-1 mb-4">
                    {Array(t.stars).fill(0).map((_, i) => (
                      <Star key={i} size={13} className="fill-yellow-400 text-yellow-400" />
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

      {/* Pricing grid section */}
      <section className="relative z-10 py-20 px-6 max-w-5xl mx-auto">
        <h2 className="text-3xl font-bold text-white text-center mb-4">Transparent Recruiter Plans</h2>
        <p className="text-xs text-gray-400 text-center mb-16 max-w-md mx-auto">
          Choose a tier designed to support seed-stage startups through to growing enterprise recruiting teams.
        </p>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
          {pricingPlans.map((plan, idx) => (
            <div 
              key={idx}
              className={`rounded-2xl border p-6 flex flex-col justify-between bg-surface/35 backdrop-blur-md relative overflow-hidden transition-all ${
                plan.popular 
                  ? 'border-emerald-500/50 shadow-glow-emerald/10' 
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

      {/* FAQ accordion section */}
      <section className="relative z-10 py-20 px-6 border-t border-white/5 bg-[#0a0a15]/40 backdrop-blur-sm">
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
                  className="bg-surface/30 border border-white/5 rounded-2xl overflow-hidden transition-all duration-300"
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
        <p>Built with React, FastAPI, SQLite, and Tailwind CSS.</p>
      </footer>
    </div>
  );
}
