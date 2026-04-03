import React from 'react';
import { motion } from 'framer-motion';
import { useIntersection } from '../lib/hooks';
import MagneticCard from './MagneticCard';
import { ShieldCheck, Zap, Network, Sparkles, Binary } from 'lucide-react';
import { staggerContainer, fadeUp } from '../lib/animations';

const FEATURES = [
  {
    icon: <Zap className="h-6 w-6 text-mint" />,
    title: 'Instant Analysis',
    desc: 'Extract and analyze relevant skills in milliseconds, leaving human bias behind.'
  },
  {
    icon: <Network className="h-6 w-6 text-violet" />,
    title: 'Social Graphing',
    desc: 'Correlate GitHub, LinkedIn, and portfolios to form a holistic candidate profile.'
  },
  {
    icon: <ShieldCheck className="h-6 w-6 text-sky" />,
    title: 'Verified Competence',
    desc: 'Cross-reference stated experience with actual public contributions.'
  },
  {
    icon: <Sparkles className="h-6 w-6 text-amber" />,
    title: 'AI Matches',
    desc: 'Get smart compatibility scores based on job descriptions and parsed data.'
  },
  {
    icon: <Binary className="h-6 w-6 text-rose" />,
    title: 'Code Analysis',
    desc: 'Automatically evaluate structural quality and maintainability of public repos.'
  }
];

export default function FeaturesSection() {
  const { ref, inView } = useIntersection(0.15);

  return (
    <section id="features" className="relative py-24 px-6">
      <div className="mx-auto max-w-6xl">
        <div className="mb-16 text-center">
          <h2 className="font-display text-4xl font-semibold tracking-tight text-white sm:text-5xl">
            Smarter infrastructure for<br />
            <span className="shimmer-text">modern recruitment</span>
          </h2>
        </div>

        <motion.div
          ref={ref}
          variants={staggerContainer}
          initial="initial"
          animate={inView ? "animate" : "initial"}
          className="grid gap-6 sm:grid-cols-2 lg:grid-cols-3"
        >
          {FEATURES.map((feat, i) => (
            <motion.div key={i} variants={fadeUp} className="h-full">
              <MagneticCard className="flex h-full flex-col p-8 transition-colors hover:border-border-glow hover:bg-surface-3">
                <div className="mb-6 inline-flex rounded-xl bg-surface p-3 shadow-inner">
                  {feat.icon}
                </div>
                <h3 className="mb-3 text-xl font-medium text-text-1">
                  {feat.title}
                </h3>
                <p className="text-text-2 leading-relaxed">
                  {feat.desc}
                </p>
              </MagneticCard>
            </motion.div>
          ))}

          {/* Callout Card */}
          <motion.div variants={fadeUp} className="h-full sm:col-span-2 lg:col-span-1">
            <MagneticCard className="flex h-full flex-col p-8 bg-gradient-to-br from-violet/20 to-surface-2 border-violet/30">
              <h3 className="mb-4 text-2xl font-bold text-white content-end h-full">
                Ready to transform your hiring workflow?
              </h3>
            </MagneticCard>
          </motion.div>
        </motion.div>
      </div>
    </section>
  );
}
