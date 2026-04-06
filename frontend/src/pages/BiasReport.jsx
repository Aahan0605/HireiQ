import React from 'react';
import { motion } from 'framer-motion';

const BIAS_DATA = [
  { name: 'Alice Chen', full: 94, blind: 96, role: 'Frontend Engineer' },
  { name: 'Marcus Jones', full: 88, blind: 91, role: 'Fullstack Engineer' },
  { name: 'Sofia Rodriguez', full: 97, blind: 97, role: 'Backend Lead' },
  { name: 'Tirth Patel', full: 98, blind: 95, role: 'Web3 Engineer' },
  { name: 'Diana Park', full: 76, blind: 82, role: 'ML Engineer' },
];

export default function BiasReport() {
  const biasedCount = BIAS_DATA.filter(c => Math.abs(c.full - c.blind) > 3).length;
  const hasBias = biasedCount > 0;

  // CSS donut: 80% unbiased
  const biasedPct = Math.round((biasedCount / BIAS_DATA.length) * 100);
  const unbiasedPct = 100 - biasedPct;
  const circumference = 2 * Math.PI * 40;
  const biasedDash = (biasedPct / 100) * circumference;

  return (
    <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ duration: 0.3 }} className="min-h-screen bg-page p-6 lg:p-10">
      <div className="max-w-4xl mx-auto">
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-white">🛡️ Bias Audit Report</h1>
          <p className="text-gray-400 mt-1 text-sm">Anonymization Engine Analysis — comparing full vs blind scoring</p>
        </div>

        {/* Bias detected banner */}
        {hasBias && (
          <motion.div
            initial={{ opacity: 0, y: -10 }} animate={{ opacity: 1, y: 0 }}
            className="mb-6 flex items-center gap-3 bg-amber-500/15 border border-amber-500/30 rounded-xl px-5 py-4"
          >
            <span className="text-2xl">⚠️</span>
            <div>
              <p className="text-amber-300 font-semibold">Potential Bias Detected</p>
              <p className="text-amber-400/70 text-sm">{biasedCount} candidate(s) showed score variance &gt;3 points when anonymized</p>
            </div>
          </motion.div>
        )}

        <div className="grid gap-6 lg:grid-cols-3">
          {/* Comparison Table */}
          <div className="lg:col-span-2 bg-card border border-black/10 dark:border-white/10 rounded-xl p-6">
            <div className="grid grid-cols-4 text-xs text-gray-500 font-medium mb-4 px-2">
              <span>Candidate</span>
              <span className="text-center">Full Score</span>
              <span className="text-center">Blind Score</span>
              <span className="text-center">Delta</span>
            </div>
            <div className="space-y-3">
              {BIAS_DATA.map((c, i) => {
                const delta = c.blind - c.full;
                const absDelta = Math.abs(delta);
                const isBiased = absDelta > 3;
                return (
                  <motion.div
                    key={c.name}
                    initial={{ opacity: 0, x: -10 }}
                    animate={{ opacity: 1, x: 0, transition: { delay: i * 0.08 } }}
                    className={`grid grid-cols-4 items-center rounded-lg px-3 py-3 ${isBiased ? 'bg-amber-500/5 border border-amber-500/20' : 'bg-white/5'}`}
                  >
                    <div>
                      <p className="text-theme-1 text-sm font-medium">{c.name}</p>
                      <p className="text-gray-500 text-xs">{c.role}</p>
                    </div>
                    <div className="text-center">
                      <span className="font-bold text-theme-1">{c.full}</span>
                    </div>
                    <div className="text-center">
                      <span className="text-cyan-400 font-bold">{c.blind}</span>
                    </div>
                    <div className="text-center">
                      <span className={`text-xs px-2 py-1 rounded-full font-semibold ${
                        delta > 0 ? 'bg-red-500/20 text-red-400' :
                        delta < 0 ? 'bg-green-500/20 text-green-400' :
                        'bg-gray-500/20 text-gray-400'
                      }`}>
                        {delta > 0 ? `+${delta}` : delta === 0 ? '0' : delta}
                      </span>
                    </div>
                  </motion.div>
                );
              })}
            </div>
            <p className="text-gray-500 text-xs mt-4">
              Red delta = blind score higher (original may have been biased downward)
            </p>
          </div>

          {/* Donut + Summary */}
          <div className="flex flex-col gap-4">
            {/* CSS Donut */}
            <div className="bg-card border border-black/10 dark:border-white/10 rounded-xl p-6 flex flex-col items-center">
              <h3 className="text-theme-1 font-semibold mb-4 text-sm">Bias Distribution</h3>
              <svg viewBox="0 0 100 100" className="w-28 h-28">
                <circle cx="50" cy="50" r="40" fill="none" stroke="rgba(255,255,255,0.05)" strokeWidth="12" />
                {/* Unbiased arc */}
                <circle cx="50" cy="50" r="40" fill="none" stroke="#22c55e" strokeWidth="12"
                  strokeDasharray={`${(unbiasedPct / 100) * circumference} ${circumference}`}
                  strokeDashoffset={circumference * 0.25}
                  strokeLinecap="round"
                />
                {/* Biased arc */}
                <circle cx="50" cy="50" r="40" fill="none" stroke="#f59e0b" strokeWidth="12"
                  strokeDasharray={`${biasedDash} ${circumference}`}
                  strokeDashoffset={circumference * 0.25 - (unbiasedPct / 100) * circumference}
                  strokeLinecap="round"
                />
                <text x="50" y="54" textAnchor="middle" fill="white" fontSize="14" fontWeight="bold">{unbiasedPct}%</text>
              </svg>
              <div className="flex gap-4 mt-3 text-xs">
                <span className="flex items-center gap-1 text-green-400"><span className="w-2 h-2 rounded-full bg-green-500 inline-block" />Unbiased</span>
                <span className="flex items-center gap-1 text-amber-400"><span className="w-2 h-2 rounded-full bg-amber-500 inline-block" />Potential Bias</span>
              </div>
            </div>

            {/* Summary Card */}
            <div className="bg-card border border-black/10 dark:border-white/10 rounded-xl p-5">
              <h3 className="text-theme-1 font-semibold text-sm mb-3">Summary</h3>
              <p className="text-gray-400 text-xs leading-relaxed">
                <span className="text-theme-1 font-medium">{biasedCount} out of {BIAS_DATA.length}</span> candidates showed score variance &gt;3 points when anonymized, suggesting possible demographic influence in the original scoring.
              </p>
              <div className="mt-4 space-y-2">
                <div className="flex justify-between text-xs">
                  <span className="text-gray-400">Avg full score</span>
                  <span className="text-theme-1 font-medium">{Math.round(BIAS_DATA.reduce((s, c) => s + c.full, 0) / BIAS_DATA.length)}</span>
                </div>
                <div className="flex justify-between text-xs">
                  <span className="text-gray-400">Avg blind score</span>
                  <span className="text-cyan-400 font-medium">{Math.round(BIAS_DATA.reduce((s, c) => s + c.blind, 0) / BIAS_DATA.length)}</span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </motion.div>
  );
}
