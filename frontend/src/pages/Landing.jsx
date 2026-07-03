import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { motion, AnimatePresence } from 'framer-motion';
import { Check, Sparkles, HelpCircle, ArrowRight, Star, Quote, ChevronDown, Award, Github, Linkedin, Terminal, Calendar, ShieldCheck, Mail, MapPin, Phone, Globe, Users, Heart } from 'lucide-react';
import ConstellationBackground from '../components/ConstellationBackground';
import { usePrefersReducedMotion, useCountUp, useIntersection, useMagneticTilt } from '../lib/hooks';

const MotionLink = motion.create(Link);

export default function Landing() {
  const [activeFaq, setActiveFaq] = useState(null);
  const prefersReducedMotion = usePrefersReducedMotion();

  // Force body background to dark while on the landing page
  // Prevents the light-mode body bg from showing as a white line behind the scrollbar
  useEffect(() => {
    const prev = document.body.style.backgroundColor;
    document.body.style.backgroundColor = '#07070e';
    return () => { document.body.style.backgroundColor = prev; };
  }, []);
  const tiltConfig = useMagneticTilt(6);

  const { ref: showcaseRef, inView: showcaseInView } = useIntersection(0.1);
  const totalCandidatesRef = useCountUp(48, prefersReducedMotion ? 0 : 1.4, showcaseInView);
  const githubVerifiedRef = useCountUp(32, prefersReducedMotion ? 0 : 1.4, showcaseInView);

  const sentence = '"Jordan Rivera is a Mid-Level Software Engineer candidate with a verified background in Bachelor of Technology (B.Tech), demonstrating 2.0 years of experience. Live engineering analytics successfully verified practical usage and competence in React and Python (score: 67/100)."';
  const words = sentence.split(' ');

  const sentenceVariants = {
    hidden: { opacity: 1 },
    visible: {
      opacity: 1,
      transition: {
        delayChildren: 0.4,
        staggerChildren: prefersReducedMotion ? 0 : 0.012,
      }
    }
  };

  const wordVariants = {
    hidden: { opacity: 0, y: prefersReducedMotion ? 0 : 3 },
    visible: {
      opacity: 1,
      y: 0,
      transition: {
        duration: 0.2,
        ease: 'easeOut'
      }
    }
  };

  const badgeContainerVariants = {
    hidden: { opacity: 0 },
    visible: {
      opacity: 1,
      transition: {
        staggerChildren: prefersReducedMotion ? 0 : 0.06,
        delayChildren: 1.0
      }
    }
  };

  const badgeItemVariants = {
    hidden: { opacity: 0, scale: prefersReducedMotion ? 1 : 0.95 },
    visible: { 
      opacity: 1, 
      scale: 1, 
      transition: { 
        type: 'spring', 
        stiffness: 300, 
        damping: 20 
      } 
    }
  };

  const containerVariants = {
    hidden: { opacity: 0 },
    visible: {
      opacity: 1,
      transition: {
        staggerChildren: prefersReducedMotion ? 0 : 0.08
      }
    }
  };

  const itemVariants = {
    hidden: { 
      opacity: 0, 
      y: prefersReducedMotion ? 0 : 16 
    },
    visible: {
      opacity: 1,
      y: 0,
      transition: {
        duration: prefersReducedMotion ? 0.25 : 0.5,
        ease: [0.22, 1, 0.36, 1]
      }
    }
  };
  const titleLineVariants = {
    hidden: { 
      y: prefersReducedMotion ? 0 : "120%"
    },
    visible: {
      y: 0,
      transition: {
        duration: prefersReducedMotion ? 0.25 : 0.9,
        ease: [0.16, 1, 0.3, 1]
      }
    }
  };


  const cardVariants = {
    hidden: { 
      opacity: 0, 
      y: prefersReducedMotion ? 0 : 24, 
      scale: prefersReducedMotion ? 1 : 0.96 
    },
    visible: {
      opacity: 1,
      y: 0,
      scale: 1,
      transition: {
        duration: prefersReducedMotion ? 0.25 : 0.5,
        ease: [0.22, 1, 0.36, 1]
      }
    }
  };

  const skeletonVariants = {
    animate: (i) => ({
      opacity: [0.35, 0.7, 0.35],
      transition: {
        duration: 1.8,
        repeat: Infinity,
        ease: "easeInOut",
        delay: i * 0.15
      }
    })
  };

  const scrollContainerVariants = {
    hidden: { opacity: 0 },
    visible: {
      opacity: 1,
      transition: {
        staggerChildren: prefersReducedMotion ? 0 : 0.1
      }
    }
  };

  const scrollItemVariants = {
    hidden: { 
      opacity: 0, 
      y: prefersReducedMotion ? 0 : 24 
    },
    visible: {
      opacity: 1,
      y: 0,
      transition: {
        duration: 0.5,
        ease: "easeOut"
      }
    }
  };

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

  // Source of truth for public pricing. Must stay in sync with backend
  // PLAN_QUOTAS in backend/api/core/limits.py (free=5 parses, pro=unlimited).
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
      buttonLink: "/signin",
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
      buttonLink: "#about",
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
            <a href="#features" className="hover:text-emerald-400 transition-colors duration-200">Features</a>
            <a href="#pricing" className="hover:text-emerald-400 transition-colors duration-200">Pricing</a>
            <a href="#faq" className="hover:text-emerald-400 transition-colors duration-200">FAQs</a>
            <a href="#about" className="hover:text-emerald-400 transition-colors duration-200">About</a>
          </nav>
          <div className="flex items-center gap-4">
            <Link to="/signin" className="text-sm font-semibold text-gray-400 hover:text-white transition-colors duration-200">
              Sign In
            </Link>
            <MotionLink 
              to="/signin?mode=signup"
              whileHover={prefersReducedMotion ? {} : { scale: 1.02, boxShadow: "0 10px 15px -3px rgba(16, 185, 129, 0.2)" }}
              whileTap={{ scale: 0.95 }}
              transition={{ type: "spring", stiffness: 400, damping: 17 }}
              className="rounded-xl bg-gradient-to-r from-emerald-500 to-cyan-500 px-5 py-2 text-sm font-bold text-white shadow-lg"
            >
              Launch App
            </MotionLink>
          </div>
        </div>
      </header>

      {/* Hero Section */}
      <motion.section 
        variants={containerVariants}
        initial="hidden"
        animate="visible"
        className="relative z-10 flex min-h-screen flex-col items-center justify-center px-6 pt-32 pb-20 max-w-5xl mx-auto text-center"
      >

        <h1 className="mb-6 text-4xl font-black tracking-tight text-white sm:text-6xl md:text-7xl leading-[1.1] text-balance">
          <span className="block overflow-hidden py-2 -my-2">
            <motion.span variants={titleLineVariants} className="block">
              Hire the best,
            </motion.span>
          </span>
          <span className="block overflow-hidden py-2 -my-2">
            <motion.span variants={titleLineVariants} className="block">
              <motion.span 
                animate={prefersReducedMotion ? {} : { backgroundPosition: ["0% center", "200% center"] }}
                transition={prefersReducedMotion ? {} : { duration: 7, ease: "linear", repeat: Infinity }}
                style={prefersReducedMotion ? {} : {
                  background: "linear-gradient(90deg, #2dd4bf, #06b6d4, #2dd4bf)",
                  backgroundSize: "200% auto",
                  WebkitBackgroundClip: "text",
                  WebkitTextFillColor: "transparent",
                  backgroundClip: "text"
                }}
                className={prefersReducedMotion ? "bg-gradient-to-r from-emerald-400 to-cyan-400 bg-clip-text text-transparent block" : "block"}
              >
                faster than ever.
              </motion.span>
            </motion.span>
          </span>
        </h1>

        <motion.p
          variants={itemVariants}
          className="mx-auto mb-10 max-w-2xl text-sm text-gray-400 sm:text-base leading-relaxed text-balance"
        >
          Leverage automated resume parsing, interactive skill graphs, blind bias audits, and live social portfolio footprints to identify and hire elite technical talent.
        </motion.p>

        <motion.div 
          variants={itemVariants}
          className="flex flex-col items-center justify-center gap-4 sm:flex-row mb-16"
        >
          <MotionLink
            to="/signin"
            whileHover={prefersReducedMotion ? {} : { 
              scale: 1.03,
              boxShadow: "0 10px 20px -5px rgba(16, 185, 129, 0.3)"
            }}
            whileTap={{ scale: 0.97 }}
            transition={{ type: "spring", stiffness: 400, damping: 17 }}
            className="group relative inline-flex h-12 items-center justify-center overflow-hidden rounded-xl bg-gradient-to-r from-emerald-500 to-cyan-500 px-8 text-sm font-bold text-white shadow-lg shadow-emerald-500/20"
          >
            Go to Recruiter Dashboard
          </MotionLink>
          <motion.a
            href="#pricing"
            whileHover={prefersReducedMotion ? {} : { 
              scale: 1.02, 
              borderColor: "rgba(255, 255, 255, 0.2)",
              backgroundColor: "rgba(255, 255, 255, 0.08)"
            }}
            whileTap={{ scale: 0.97 }}
            transition={{ type: "spring", stiffness: 400, damping: 17 }}
            className="inline-flex h-12 items-center justify-center rounded-xl border border-white/10 bg-white/5 backdrop-blur-md px-8 text-sm font-semibold text-white"
          >
            Explore B2B Plans
          </motion.a>
        </motion.div>

        {/* Interactive Dashboard Showcase Widget */}
        <motion.div
          ref={showcaseRef}
          variants={cardVariants}
          className="w-full max-w-4xl mx-auto"
        >
          <motion.div
            animate={prefersReducedMotion ? {} : { y: [0, -8, 0] }}
            transition={prefersReducedMotion ? {} : {
              duration: 5,
              repeat: Infinity,
              ease: "easeInOut"
            }}
            className="border border-white/10 rounded-2xl bg-[#131326]/40 backdrop-blur-md p-6 shadow-2xl relative overflow-hidden"
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
                  <span ref={totalCandidatesRef} className="text-[10px] font-black text-white">0</span>
                </div>
                <div className="h-7 bg-cyan-500/10 border border-cyan-500/20 rounded-lg p-2 flex items-center justify-between">
                  <span className="text-[10px] font-bold text-cyan-400">GitHub Verified</span>
                  <span ref={githubVerifiedRef} className="text-[10px] font-black text-white">0</span>
                </div>
              </div>
              <div className="space-y-2 pt-2 border-t border-white/5">
                <div className="h-2 shimmer-bar rounded w-full" />
                <div className="h-2 shimmer-bar rounded w-4/5" />
                <div className="h-2 shimmer-bar rounded w-5/6" />
              </div>
            </div>

            {/* Middle/Right Mock Content (Interactive Candidate Card) */}
            <div 
              ref={tiltConfig.ref}
              onMouseMove={tiltConfig.onMouseMove}
              onMouseLeave={tiltConfig.onMouseLeave}
              className="md:col-span-2 bg-[#19192f] border border-white/10 rounded-xl p-5 relative overflow-hidden flex flex-col justify-between transition-all duration-200 z-10"
            >
              {/* Highlight overlay for cursor glow reflection */}
              <div className="card-highlight absolute inset-0 pointer-events-none z-0" />
              
              <div className="relative z-10">
                <div className="flex justify-between items-start mb-3">
                  <div>
                    <h4 className="text-sm font-bold text-white flex items-center gap-2">
                      Jordan Rivera <span className="text-[9px] px-2 py-0.5 rounded-full bg-cyan-400/10 text-cyan-400 font-semibold border border-cyan-400/20">Mid-Level</span>
                    </h4>
                    <p className="text-[10px] text-gray-500 mt-0.5">Sourced via Resume upload</p>
                  </div>
                  <motion.div 
                    animate={prefersReducedMotion ? {} : { 
                      scale: [1, 1.04, 1],
                      boxShadow: ["0 0 0 0 rgba(16, 185, 129, 0)", "0 0 8px 2px rgba(16, 185, 129, 0.2)", "0 0 0 0 rgba(16, 185, 129, 0)"]
                    }}
                    transition={{
                      duration: 2,
                      repeat: Infinity,
                      ease: "easeInOut"
                    }}
                    className="px-2 py-0.5 rounded-full bg-emerald-500/10 text-emerald-400 text-xs font-bold border border-emerald-500/20"
                  >
                    67/100 Match
                  </motion.div>
                </div>
                
                <motion.p 
                  variants={sentenceVariants}
                  initial="hidden"
                  whileInView="visible"
                  viewport={{ once: true }}
                  className="text-[11px] text-gray-400 leading-relaxed mb-4 flex flex-wrap gap-x-1"
                >
                  {words.map((word, idx) => (
                    <motion.span key={idx} variants={wordVariants} className="inline-block">
                      {word}
                    </motion.span>
                  ))}
                </motion.p>
              </div>

              {/* Mock Badges */}
              <motion.div 
                variants={badgeContainerVariants}
                initial="hidden"
                whileInView="visible"
                viewport={{ once: true }}
                className="flex flex-wrap gap-1.5 pt-3 border-t border-white/5 relative z-10"
              >
                <motion.span variants={badgeItemVariants} className="text-[9px] px-2.5 py-0.5 rounded-full bg-white/5 text-gray-300 border border-white/5">FastAPI</motion.span>
                <motion.span variants={badgeItemVariants} className="text-[9px] px-2.5 py-0.5 rounded-full bg-white/5 text-gray-300 border border-white/5">React</motion.span>
                <motion.span variants={badgeItemVariants} className="text-[9px] px-2.5 py-0.5 rounded-full bg-white/5 text-gray-300 border border-white/5">PostgreSQL</motion.span>
                <motion.span 
                  variants={badgeItemVariants}
                  animate={prefersReducedMotion ? {} : { 
                    borderColor: ["rgba(16,185,129,0.2)", "rgba(16,185,129,0.5)", "rgba(16,185,129,0.2)"]
                  }}
                  transition={{ duration: 2.5, repeat: Infinity, ease: "easeInOut" }}
                  className="text-[9px] px-2.5 py-0.5 rounded-full bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 flex items-center gap-1"
                >
                  <Github size={8} /> GitHub Verified
                </motion.span>
              </motion.div>
            </div>
          </div>
          </motion.div>
        </motion.div>
      </motion.section>

      {/* Features Showcase Section */}
      <section id="features" className="relative z-10 py-28 px-6 max-w-6xl mx-auto border-t border-white/5">
        <h2 className="text-3xl font-black text-white text-center mb-4">Designed for Engineering Sourcing</h2>
        <p className="text-xs text-gray-400 text-center mb-16 max-w-md mx-auto">
          We combine deterministic screening tools with developer social footprints to automate and secure technical sourcing.
        </p>

        <motion.div 
          initial="hidden"
          whileInView="visible"
          viewport={{ once: true, amount: 0.2 }}
          variants={scrollContainerVariants}
          className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6"
        >
          <motion.div variants={scrollItemVariants} className="bg-white/5 border border-white/5 rounded-2xl p-6 hover:border-emerald-500/20 hover:bg-white/10 transition-all duration-300 flex flex-col justify-between min-h-[200px]">
            <div>
              <span className="text-2xl mb-4 block">🤖</span>
              <h3 className="font-bold text-sm text-white mb-2">AI Resume Parsing</h3>
              <p className="text-[11px] text-gray-400 leading-relaxed">
                Scan semantic structures to extract skills, experience years, degrees, and certificates within 5 seconds.
              </p>
            </div>
          </motion.div>
          <motion.div variants={scrollItemVariants} className="bg-white/5 border border-white/5 rounded-2xl p-6 hover:border-cyan-500/20 hover:bg-white/10 transition-all duration-300 flex flex-col justify-between min-h-[200px]">
            <div>
              <span className="text-2xl mb-4 block">📈</span>
              <h3 className="font-bold text-sm text-white mb-2">GitHub Footprint Sync</h3>
              <p className="text-[11px] text-gray-400 leading-relaxed">
                Verify actual commits, star counts, polyglot language frequencies, and test coverage indicators directly.
              </p>
            </div>
          </motion.div>
          <motion.div variants={scrollItemVariants} className="bg-white/5 border border-white/5 rounded-2xl p-6 hover:border-violet/20 hover:bg-white/10 transition-all duration-300 flex flex-col justify-between min-h-[200px]">
            <div>
              <span className="text-2xl mb-4 block">🔒</span>
              <h3 className="font-bold text-sm text-white mb-2">Anonymized Bias Audit</h3>
              <p className="text-[11px] text-gray-400 leading-relaxed">
                Hide demographic data, locations, and names with one click to enforce objective skill-based reviews.
              </p>
            </div>
          </motion.div>
          <motion.div variants={scrollItemVariants} className="bg-white/5 border border-white/5 rounded-2xl p-6 hover:border-yellow-500/20 hover:bg-white/10 transition-all duration-300 flex flex-col justify-between min-h-[200px]">
            <div>
              <span className="text-2xl mb-4 block">📅</span>
              <h3 className="font-bold text-sm text-white mb-2">Greedy Scheduling</h3>
              <p className="text-[11px] text-gray-400 leading-relaxed">
                Schedule technical interviews without conflicts using greedy activity interval optimizations.
              </p>
            </div>
          </motion.div>
        </motion.div>
      </section>

      {/* Testimonials Section */}
      <section className="relative z-10 py-20 px-6 border-y border-white/5 bg-[#0a0a15]/40 backdrop-blur-sm">
        <div className="max-w-4xl mx-auto">
          <h2 className="text-3xl font-bold text-white text-center mb-12 flex items-center justify-center gap-2">
            <Quote className="text-emerald-400" /> What Engineering Teams Say
          </h2>

          <motion.div 
            initial="hidden"
            whileInView="visible"
            viewport={{ once: true, amount: 0.2 }}
            variants={scrollContainerVariants}
            className="grid grid-cols-1 md:grid-cols-3 gap-6"
          >
            {testimonials.map((t, idx) => (
              <motion.div 
                key={idx} 
                variants={scrollItemVariants}
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
              </motion.div>
            ))}
          </motion.div>
        </div>
      </section>

      {/* Pricing Grid Section */}
      <section id="pricing" className="relative z-10 py-24 px-6 max-w-5xl mx-auto">
        <h2 className="text-3xl font-black text-white text-center mb-4">Transparent Recruiter Plans</h2>
        <p className="text-xs text-gray-400 text-center mb-16 max-w-md mx-auto">
          Choose a tier designed to support seed-stage startups through to growing engineering teams.
        </p>

        <motion.div 
          initial="hidden"
          whileInView="visible"
          viewport={{ once: true, amount: 0.2 }}
          variants={scrollContainerVariants}
          className="grid grid-cols-1 md:grid-cols-3 gap-8"
        >
          {pricingPlans.map((plan, idx) => (
            <motion.div
              key={idx}
              variants={scrollItemVariants}
              whileHover={prefersReducedMotion ? {} : { y: -6 }}
              transition={{ type: 'spring', stiffness: 300, damping: 22 }}
              className={`rounded-2xl border p-6 flex flex-col justify-between backdrop-blur-md relative overflow-hidden ${
                plan.popular
                  ? 'border-emerald-500/60 bg-emerald-500/[0.06] shadow-xl shadow-emerald-500/10 md:-translate-y-4 md:scale-[1.03]'
                  : 'border-white/5 bg-white/5 hover:border-white/15'
              }`}
            >
              {plan.popular && (
                <>
                  <div className="absolute -inset-px rounded-2xl bg-gradient-to-b from-emerald-500/20 to-transparent opacity-60 pointer-events-none" />
                  <div className="absolute top-0 right-0 bg-emerald-500 text-[#07070e] text-[8px] font-black tracking-widest px-3 py-1 rounded-bl">
                    MOST POPULAR
                  </div>
                </>
              )}
              <div className="relative z-10">
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
              {plan.buttonLink.startsWith('#') ? (
                <a
                  href={plan.buttonLink}
                  className={`relative z-10 block w-full py-2.5 rounded-xl text-center text-xs font-bold transition-all focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-emerald-400 focus-visible:ring-offset-2 focus-visible:ring-offset-[#07070e] ${
                    plan.popular
                      ? 'bg-gradient-to-r from-emerald-500 to-cyan-500 text-white shadow-lg hover:opacity-95'
                      : 'bg-white/5 hover:bg-white/10 text-white border border-white/10'
                  }`}
                >
                  {plan.buttonText}
                </a>
              ) : (
                <Link
                  to={plan.buttonLink}
                  className={`relative z-10 block w-full py-2.5 rounded-xl text-center text-xs font-bold transition-all focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-emerald-400 focus-visible:ring-offset-2 focus-visible:ring-offset-[#07070e] ${
                    plan.popular
                      ? 'bg-gradient-to-r from-emerald-500 to-cyan-500 text-white shadow-lg hover:opacity-95'
                      : 'bg-white/5 hover:bg-white/10 text-white border border-white/10'
                  }`}
                >
                  {plan.buttonText}
                </Link>
              )}
            </motion.div>
          ))}
        </motion.div>
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

      {/* About & Contact Section */}
      <section id="about" className="relative z-10 py-28 px-6 border-t border-white/5 overflow-hidden">
        {/* Decorative ambient glows */}
        <div className="absolute top-0 left-1/2 -translate-x-1/2 w-[800px] h-[400px] bg-emerald-500/8 rounded-full blur-[180px] pointer-events-none" />
        <div className="absolute bottom-0 right-0 w-[500px] h-[500px] bg-cyan-500/5 rounded-full blur-[150px] pointer-events-none" />

        <div className="max-w-5xl mx-auto relative">
          <motion.div
            initial="hidden"
            whileInView="visible"
            viewport={{ once: true, amount: 0.15 }}
            variants={scrollContainerVariants}
          >
            {/* Section Header with gradient accent line */}
            <motion.div variants={scrollItemVariants} className="text-center mb-20">
              <motion.div 
                className="inline-flex items-center gap-2.5 mb-5 px-4 py-2 rounded-full border border-emerald-500/20 bg-emerald-500/5 backdrop-blur-md"
                whileHover={prefersReducedMotion ? {} : { scale: 1.05, borderColor: "rgba(16, 185, 129, 0.4)" }}
              >
                <Heart size={16} className="text-emerald-400" />
                <span className="text-xs font-bold tracking-widest uppercase text-emerald-400">Our Story</span>
              </motion.div>
              <h2 className="text-4xl md:text-5xl font-black text-white mb-6 leading-tight">
                Built by Recruiters,<br />
                <span className="bg-gradient-to-r from-emerald-400 via-cyan-400 to-emerald-400 bg-clip-text text-transparent">Powered by AI</span>
              </h2>
              <p className="text-sm text-gray-400 leading-relaxed max-w-2xl mx-auto">
                HireiQ was born from a simple frustration — hiring the best engineers shouldn't feel like searching for a needle in a haystack. We built an AI-powered platform that combines resume intelligence, live GitHub analytics, and bias-free evaluation to help teams hire smarter, faster, and fairer.
              </p>
            </motion.div>

            {/* Animated Stats Row */}
            <motion.div variants={scrollItemVariants} className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-20">
              {[
                { value: "10K+", label: "Resumes Analyzed", color: "emerald" },
                { value: "500+", label: "Teams Hiring", color: "cyan" },
                { value: "98%", label: "Match Accuracy", color: "violet" },
                { value: "20hrs", label: "Saved Per Week", color: "amber" },
              ].map((stat, i) => (
                <motion.div
                  key={i}
                  className="relative group text-center py-6 rounded-2xl border border-white/5 bg-white/[0.03] backdrop-blur-md overflow-hidden"
                  whileHover={prefersReducedMotion ? {} : { 
                    y: -4, 
                    borderColor: "rgba(255,255,255,0.15)",
                    transition: { duration: 0.2 }
                  }}
                >
                  <div className={`absolute inset-0 bg-${stat.color}-500/5 opacity-0 group-hover:opacity-100 transition-opacity duration-500`} />
                  <p className={`text-2xl md:text-3xl font-black bg-gradient-to-b from-white to-gray-400 bg-clip-text text-transparent mb-1`}>{stat.value}</p>
                  <p className="text-[10px] text-gray-500 uppercase tracking-wider font-semibold">{stat.label}</p>
                </motion.div>
              ))}
            </motion.div>

            {/* Story Cards — premium glassmorphism with gradient top border */}
            <motion.div variants={scrollItemVariants} className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-20">
              {[
                {
                  icon: <Users size={24} className="text-emerald-400" />,
                  title: "Team-First Design",
                  desc: "Built for recruiting teams of all sizes — from seed-stage startups hiring their first engineer to enterprise teams scaling globally.",
                  gradient: "from-emerald-500 to-teal-500",
                  glow: "emerald"
                },
                {
                  icon: <ShieldCheck size={24} className="text-cyan-400" />,
                  title: "Bias-Free Hiring",
                  desc: "Our blind mode anonymizes candidate data so your team evaluates skills objectively — reducing demographic bias in every hiring decision.",
                  gradient: "from-cyan-500 to-blue-500",
                  glow: "cyan"
                },
                {
                  icon: <Terminal size={24} className="text-violet-400" />,
                  title: "Engineering-Grade",
                  desc: "Open-source at heart, built with React, FastAPI, and Supabase. We believe great tools should be transparent and extensible.",
                  gradient: "from-violet-500 to-purple-500",
                  glow: "violet"
                }
              ].map((card, i) => (
                <motion.div
                  key={i}
                  className="relative group rounded-2xl border border-white/5 bg-white/[0.03] backdrop-blur-md p-7 text-center overflow-hidden"
                  whileHover={prefersReducedMotion ? {} : { 
                    y: -6,
                    transition: { type: "spring", stiffness: 300, damping: 20 }
                  }}
                >
                  {/* Gradient top border accent */}
                  <div className={`absolute top-0 left-0 right-0 h-[2px] bg-gradient-to-r ${card.gradient} opacity-40 group-hover:opacity-100 transition-opacity duration-500`} />
                  {/* Hover glow */}
                  <div className={`absolute -top-20 left-1/2 -translate-x-1/2 w-40 h-40 bg-${card.glow}-500/10 rounded-full blur-[60px] opacity-0 group-hover:opacity-100 transition-opacity duration-700`} />
                  
                  <div className={`relative w-14 h-14 rounded-2xl bg-gradient-to-br ${card.gradient} bg-opacity-10 flex items-center justify-center mx-auto mb-5`} style={{ background: `linear-gradient(135deg, rgba(255,255,255,0.05), rgba(255,255,255,0.02))` }}>
                    {card.icon}
                  </div>
                  <h3 className="relative text-sm font-bold text-white mb-3">{card.title}</h3>
                  <p className="relative text-xs text-gray-400 leading-relaxed">{card.desc}</p>
                </motion.div>
              ))}
            </motion.div>

            {/* Glowing gradient divider */}
            <div className="flex items-center justify-center mb-20">
              <div className="h-px flex-1 bg-gradient-to-r from-transparent via-emerald-500/30 to-transparent" />
              <div className="mx-4 w-2 h-2 rounded-full bg-emerald-400/60 shadow-[0_0_12px_rgba(52,211,153,0.4)]" />
              <div className="h-px flex-1 bg-gradient-to-r from-transparent via-cyan-500/30 to-transparent" />
            </div>

            {/* Contact Section */}
            <motion.div variants={scrollItemVariants} id="contact" className="max-w-3xl mx-auto">
              <div className="text-center mb-10">
                <h3 className="text-2xl font-black text-white mb-3">Get in Touch</h3>
                <p className="text-xs text-gray-500">Have questions? We'd love to hear from you. Reach out through any channel below.</p>
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-3 gap-5">
                {/* Email */}
                <motion.a 
                  href="mailto:contact@hireiq.ai"
                  className="group relative flex flex-col items-center text-center rounded-2xl border border-white/5 bg-white/[0.03] backdrop-blur-md p-6 overflow-hidden"
                  whileHover={prefersReducedMotion ? {} : { 
                    y: -6,
                    borderColor: "rgba(52, 211, 153, 0.3)",
                    transition: { type: "spring", stiffness: 300, damping: 20 }
                  }}
                >
                  <div className="absolute -top-16 left-1/2 -translate-x-1/2 w-32 h-32 bg-emerald-500/10 rounded-full blur-[50px] opacity-0 group-hover:opacity-100 transition-opacity duration-700" />
                  <div className="relative w-12 h-12 rounded-full bg-gradient-to-br from-emerald-500/20 to-emerald-500/5 flex items-center justify-center mb-4 ring-1 ring-emerald-500/20 group-hover:ring-emerald-500/50 transition-all duration-300">
                    <Mail size={20} className="text-emerald-400" />
                  </div>
                  <p className="relative text-[9px] text-gray-500 uppercase tracking-[0.2em] font-bold mb-1.5">Email</p>
                  <p className="relative text-xs text-gray-300 group-hover:text-white transition-colors font-medium">contact@hireiq.ai</p>
                </motion.a>

                {/* Phone */}
                <motion.a 
                  href="tel:+14155550132"
                  className="group relative flex flex-col items-center text-center rounded-2xl border border-white/5 bg-white/[0.03] backdrop-blur-md p-6 overflow-hidden"
                  whileHover={prefersReducedMotion ? {} : { 
                    y: -6,
                    borderColor: "rgba(6, 182, 212, 0.3)",
                    transition: { type: "spring", stiffness: 300, damping: 20 }
                  }}
                >
                  <div className="absolute -top-16 left-1/2 -translate-x-1/2 w-32 h-32 bg-cyan-500/10 rounded-full blur-[50px] opacity-0 group-hover:opacity-100 transition-opacity duration-700" />
                  <div className="relative w-12 h-12 rounded-full bg-gradient-to-br from-cyan-500/20 to-cyan-500/5 flex items-center justify-center mb-4 ring-1 ring-cyan-500/20 group-hover:ring-cyan-500/50 transition-all duration-300">
                    <Phone size={20} className="text-cyan-400" />
                  </div>
                  <p className="relative text-[9px] text-gray-500 uppercase tracking-[0.2em] font-bold mb-1.5">Phone</p>
                  <p className="relative text-xs text-gray-300 group-hover:text-white transition-colors font-medium">+1 (415) 555-0132</p>
                </motion.a>

                {/* LinkedIn */}
                <motion.a 
                  href="https://linkedin.com/company/hireiq-ai"
                  target="_blank"
                  rel="noopener noreferrer"
                  className="group relative flex flex-col items-center text-center rounded-2xl border border-white/5 bg-white/[0.03] backdrop-blur-md p-6 overflow-hidden"
                  whileHover={prefersReducedMotion ? {} : { 
                    y: -6,
                    borderColor: "rgba(59, 130, 246, 0.3)",
                    transition: { type: "spring", stiffness: 300, damping: 20 }
                  }}
                >
                  <div className="absolute -top-16 left-1/2 -translate-x-1/2 w-32 h-32 bg-blue-500/10 rounded-full blur-[50px] opacity-0 group-hover:opacity-100 transition-opacity duration-700" />
                  <div className="relative w-12 h-12 rounded-full bg-gradient-to-br from-blue-500/20 to-blue-500/5 flex items-center justify-center mb-4 ring-1 ring-blue-500/20 group-hover:ring-blue-500/50 transition-all duration-300">
                    <Linkedin size={20} className="text-blue-400" />
                  </div>
                  <p className="relative text-[9px] text-gray-500 uppercase tracking-[0.2em] font-bold mb-1.5">LinkedIn</p>
                  <p className="relative text-xs text-gray-300 group-hover:text-white transition-colors font-medium">linkedin.com/company/hireiq-ai</p>
                </motion.a>
              </div>

              <div className="mt-8 flex items-center gap-3 justify-center text-gray-500">
                <div className="w-1.5 h-1.5 rounded-full bg-emerald-400/60 shadow-[0_0_8px_rgba(52,211,153,0.4)]" />
                <MapPin size={13} />
                <p className="text-xs">Remote-first · Based in India</p>
                <div className="w-1.5 h-1.5 rounded-full bg-cyan-400/60 shadow-[0_0_8px_rgba(6,182,212,0.4)]" />
              </div>
            </motion.div>
          </motion.div>
        </div>
      </section>

      {/* Footer */}
      <footer className="relative z-10 py-12 px-6 border-t border-white/5 text-center text-xs text-gray-500">
        <p className="mb-2">© 2026 HireiQ. Transforming AI recruiting intelligence globally.</p>
        <p className="mb-4">Built with React, FastAPI, Supabase, and Tailwind CSS.</p>
        <div className="flex flex-wrap items-center justify-center gap-x-6 gap-y-2 text-gray-600">
          <a href="#features" className="hover:text-gray-300 transition-colors">Features</a>
          <a href="#pricing" className="hover:text-gray-300 transition-colors">Pricing</a>
          <a href="#faq" className="hover:text-gray-300 transition-colors">FAQs</a>
          <a href="#about" className="hover:text-gray-300 transition-colors">About</a>
          <Link to="/privacy" className="hover:text-gray-300 transition-colors">Privacy Policy</Link>
          <Link to="/terms" className="hover:text-gray-300 transition-colors">Terms of Service</Link>
        </div>
      </footer>
    </div>
  );
}
