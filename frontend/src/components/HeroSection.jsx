import React from 'react';
import { motion } from 'framer-motion';
import { Link } from 'react-router-dom';
import { usePrefersReducedMotion } from '../lib/hooks';
import MagneticCard from './MagneticCard';

export default function HeroSection() {
  const prefersReducedMotion = usePrefersReducedMotion();
  const MotionLink = motion(Link);

  const customStagger = {
    hidden: { opacity: 0 },
    visible: {
      opacity: 1,
      transition: {
        staggerChildren: prefersReducedMotion ? 0 : 0.08,
      },
    },
  };

  const customFadeUp = {
    hidden: { opacity: 0, y: prefersReducedMotion ? 0 : 16 },
    visible: { 
      opacity: 1, 
      y: 0, 
      transition: { 
        duration: prefersReducedMotion ? 0.25 : 0.5, 
        ease: [0.22, 1, 0.36, 1] 
      } 
    },
  };

  const floatEntrance1 = {
    hidden: { opacity: 0, y: prefersReducedMotion ? 0 : 50 },
    visible: {
      opacity: 1,
      y: 0,
      transition: {
        delay: prefersReducedMotion ? 0.1 : 0.6,
        duration: prefersReducedMotion ? 0.25 : 1
      }
    }
  };

  const floatEntrance2 = {
    hidden: { opacity: 0, y: prefersReducedMotion ? 0 : 50 },
    visible: {
      opacity: 1,
      y: 0,
      transition: {
        delay: prefersReducedMotion ? 0.15 : 0.8,
        duration: prefersReducedMotion ? 0.25 : 1
      }
    }
  };

  return (
    <section className="relative flex min-h-screen flex-col items-center justify-center overflow-hidden px-6 pt-20">
      
      {/* Decorative background glows */}
      <div className="absolute top-1/2 left-1/2 -z-10 h-[600px] w-[800px] -translate-x-1/2 -translate-y-1/2 rounded-full bg-violet/20 opacity-50 blur-[120px] mix-blend-screen animate-pulseGlow" />
      <div className="absolute top-1/3 left-1/3 -z-10 h-[400px] w-[400px] -translate-x-1/2 -translate-y-1/2 rounded-full bg-mint/20 opacity-40 blur-[90px] mix-blend-screen animate-pulseGlow" style={{ animationDelay: '1s' }} />

      <motion.div
        variants={customStagger}
        initial="hidden"
        animate="visible"
        className="relative z-10 mx-auto max-w-4xl text-center"
      >
        <motion.div variants={customFadeUp} className="mb-6 inline-flex items-center gap-2 rounded-full border border-border bg-surface-2 px-4 py-1.5 text-sm font-medium text-text-2">
          <span className="flex h-2 w-2 rounded-full bg-mint animate-blink" />
          Intelligent Hiring Platform
        </motion.div>

        <h1 className="mb-8 font-display text-5xl font-bold tracking-tight text-white sm:text-7xl">
          <motion.span variants={customFadeUp} className="block">Hire the best,</motion.span>
          <motion.span variants={customFadeUp} className="block">
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
              className={prefersReducedMotion ? "gradient-text block" : "block"}
            >
              faster than ever.
            </motion.span>
          </motion.span>
        </h1>

        <motion.p
          variants={customFadeUp}
          className="mx-auto mb-10 max-w-2xl text-lg text-text-2 sm:text-xl text-balance"
        >
          Leverage AI-driven insights to analyze candidate resumes and social footprints. Build exceptional teams without the guesswork.
        </motion.p>

        <motion.div variants={customFadeUp} className="flex flex-col items-center justify-center gap-4 sm:flex-row">
          <MotionLink
            to="/dashboard"
            whileHover={prefersReducedMotion ? {} : { 
              scale: 1.03,
              boxShadow: "0 10px 20px -5px rgba(16, 185, 129, 0.3)"
            }}
            whileTap={{ scale: 0.97 }}
            transition={{ type: "spring", stiffness: 400, damping: 17 }}
            className="group relative inline-flex h-12 items-center justify-center overflow-hidden rounded-full bg-white px-8 font-medium text-bg"
          >
            <span className="absolute inset-0 bg-gradient-to-r from-mint to-sky opacity-0 transition-opacity group-hover:opacity-100" />
            <span className="relative z-10 group-hover:text-bg">Get Started</span>
          </MotionLink>

          <MotionLink
            to="/analyze"
            whileHover={prefersReducedMotion ? {} : { 
              scale: 1.02, 
              borderColor: "rgba(255, 255, 255, 0.2)",
              backgroundColor: "rgba(255, 255, 255, 0.08)"
            }}
            whileTap={{ scale: 0.97 }}
            transition={{ type: "spring", stiffness: 400, damping: 17 }}
            className="group running-border inline-flex h-12 items-center justify-center rounded-full border border-border bg-surface-2 px-8 font-medium text-text-1"
          >
            Try Demo
          </MotionLink>
        </motion.div>
      </motion.div>

      {/* Floating abstract elements */}
      <motion.div 
        variants={floatEntrance1}
        initial="hidden"
        animate="visible"
        className="pointer-events-none absolute top-1/4 right-[10%] -z-10 hidden lg:block animate-float"
      >
        <MagneticCard className="h-40 w-40 rounded-3xl border border-white/10 bg-gradient-to-br from-violet/10 to-transparent p-6 shadow-glow-violet backdrop-blur-md">
          <div className="h-full w-full rounded-full border border-violet/20 bg-violet/5" />
        </MagneticCard>
      </motion.div>

      <motion.div 
        variants={floatEntrance2}
        initial="hidden"
        animate="visible"
        className="pointer-events-none absolute bottom-1/4 left-[10%] -z-10 hidden lg:block animate-floatSlow"
      >
        <MagneticCard className="h-32 w-32 rounded-full border border-white/10 bg-gradient-to-tr from-mint/10 to-transparent p-4 shadow-glow-mint backdrop-blur-md" maxTilt={15}>
          <div className="h-full w-full rounded-2xl border border-mint/20 bg-mint/5" />
        </MagneticCard>
      </motion.div>

    </section>
  );
}