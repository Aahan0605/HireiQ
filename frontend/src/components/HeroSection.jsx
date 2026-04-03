import React from 'react';
import { motion } from 'framer-motion';
import { Link } from 'react-router-dom';
import { fadeUp, staggerContainer, softSpring } from '../lib/animations';
import MagneticCard from './MagneticCard';

export default function HeroSection() {
  return (
    <section className="relative flex min-h-screen flex-col items-center justify-center overflow-hidden px-6 pt-20">
      
      {/* Decorative background glows */}
      <div className="absolute top-1/2 left-1/2 -z-10 h-[600px] w-[800px] -translate-x-1/2 -translate-y-1/2 rounded-full bg-violet/20 opacity-50 blur-[120px] mix-blend-screen animate-pulseGlow" />
      <div className="absolute top-1/3 left-1/3 -z-10 h-[400px] w-[400px] -translate-x-1/2 -translate-y-1/2 rounded-full bg-mint/20 opacity-40 blur-[90px] mix-blend-screen animate-pulseGlow" style={{ animationDelay: '1s' }} />

      <motion.div
        variants={staggerContainer}
        initial="initial"
        animate="animate"
        className="relative z-10 mx-auto max-w-4xl text-center"
      >
        <motion.div variants={fadeUp} className="mb-6 inline-flex items-center gap-2 rounded-full border border-border bg-surface-2 px-4 py-1.5 text-sm font-medium text-text-2">
          <span className="flex h-2 w-2 rounded-full bg-mint animate-blink" />
          Intelligent Hiring Platform
        </motion.div>

        <motion.h1
          variants={fadeUp}
          className="mb-8 font-display text-5xl font-bold tracking-tight text-white sm:text-7xl"
        >
          Hire the best, <br />
          <span className="gradient-text">faster than ever.</span>
        </motion.h1>

        <motion.p
          variants={fadeUp}
          className="mx-auto mb-10 max-w-2xl text-lg text-text-2 sm:text-xl text-balance"
        >
          Leverage AI-driven insights to analyze candidate resumes and social footprints. Build exceptional teams without the guesswork.
        </motion.p>

        <motion.div variants={fadeUp} className="flex flex-col items-center justify-center gap-4 sm:flex-row">
          <Link
            to="/dashboard"
            className="group relative inline-flex h-12 items-center justify-center overflow-hidden rounded-full bg-white px-8 font-medium text-bg transition-transform hover:scale-105"
          >
            <span className="absolute inset-0 bg-gradient-to-r from-mint to-sky opacity-0 transition-opacity group-hover:opacity-100" />
            <span className="relative z-10 group-hover:text-bg">Get Started</span>
          </Link>

          <Link
            to="/analyze"
            className="group running-border inline-flex h-12 items-center justify-center rounded-full border border-border bg-surface-2 px-8 font-medium text-text-1 transition-colors hover:bg-surface-3"
          >
            Try Demo
          </Link>
        </motion.div>
      </motion.div>

      {/* Floating abstract elements */}
      <motion.div 
        initial={{ opacity: 0, y: 50 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.6, duration: 1 }}
        className="pointer-events-none absolute top-1/4 right-[10%] -z-10 hidden lg:block animate-float"
      >
        <MagneticCard className="h-40 w-40 rounded-3xl border border-white/10 bg-gradient-to-br from-violet/10 to-transparent p-6 shadow-glow-violet backdrop-blur-md">
          <div className="h-full w-full rounded-full border border-violet/20 bg-violet/5" />
        </MagneticCard>
      </motion.div>

      <motion.div 
        initial={{ opacity: 0, y: 50 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.8, duration: 1 }}
        className="pointer-events-none absolute bottom-1/4 left-[10%] -z-10 hidden lg:block animate-floatSlow"
      >
        <MagneticCard className="h-32 w-32 rounded-full border border-white/10 bg-gradient-to-tr from-mint/10 to-transparent p-4 shadow-glow-mint backdrop-blur-md" maxTilt={15}>
          <div className="h-full w-full rounded-2xl border border-mint/20 bg-mint/5" />
        </MagneticCard>
      </motion.div>

    </section>
  );
}
