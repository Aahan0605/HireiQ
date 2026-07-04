import React, { useState, useEffect } from 'react';
import { motion, useReducedMotion } from 'framer-motion';
import { AlertCircle, Loader2 } from 'lucide-react';
import { apiFetch } from '../lib/apiFetch';
import EmptyState from '../components/EmptyState';

const API = '/api/v1';

export default function BiasReport() {
  const prefersReducedMotion = useReducedMotion();
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [biasData, setBiasData] = useState([]);
  const [summary, setSummary] = useState({
    flagged_count: 0,
    overall_fair: true,
    unbiased_pct: 100,
    avg_full: 0,
    avg_blind: 0,
  });

  const loadBiasReport = async () => {
    setLoading(true);
    setError('');

    try {
      const res = await apiFetch(`${API}/candidates/bias-audit`);
      if (!res.ok) throw new Error('Unable to load bias report.');

      const data = await res.json();
      const results = data.results || [];
      const formatted = results.map(r => ({
        name: r.candidate_name,
        full: r.full_score,
        blind: r.blind_score,
        role: r.role || 'Software Engineer',
      }));

      setBiasData(formatted);

      if (formatted.length === 0) {
        setSummary({
          flagged_count: 0,
          overall_fair: true,
          unbiased_pct: 100,
          avg_full: 0,
          avg_blind: 0,
        });
        return;
      }

      const biasedCount = formatted.filter(c => Math.abs(c.full - c.blind) > 3).length;
      const unbiasedPct = Math.round(((formatted.length - biasedCount) / formatted.length) * 100);

      setSummary({
        flagged_count: data.flagged_count !== undefined ? data.flagged_count : biasedCount,
        overall_fair: data.overall_fair !== undefined ? data.overall_fair : (biasedCount === 0),
        unbiased_pct: data.flagged_ratio !== undefined ? Math.round((1 - data.flagged_ratio) * 100) : unbiasedPct,
        avg_full: Math.round(formatted.reduce((s, c) => s + c.full, 0) / formatted.length),
        avg_blind: Math.round(formatted.reduce((s, c) => s + c.blind, 0) / formatted.length),
      });
    } catch (err) {
      setBiasData([]);
      setSummary({
        flagged_count: 0,
        overall_fair: true,
        unbiased_pct: 100,
        avg_full: 0,
        avg_blind: 0,
      });
      setError(err.message || 'Unable to load bias report.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadBiasReport();
  }, []);

  const biasedCount = summary.flagged_count;
  const hasBias = biasedCount > 0;
  const unbiasedPct = summary.unbiased_pct;
  const biasedPct = 100 - unbiasedPct;
  const circumference = 2 * Math.PI * 40;
  const biasedDash = (biasedPct / 100) * circumference;

  if (loading) {
    return (
      <div className="min-h-screen bg-[#0d0d1a] flex items-center justify-center">
        <div className="text-center">
          <Loader2 className="h-8 w-8 text-emerald-400 animate-spin mx-auto mb-4" />
          <p className="text-gray-400 text-sm">Evaluating anonymization metrics...</p>
        </div>
      </div>
    );
  }

  return (
    <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ duration: 0.3 }} className="min-h-screen bg-page p-6 lg:p-10">
      <div className="max-w-4xl mx-auto">
        {/* Header */}
        <div className="mb-8 flex justify-between items-start flex-wrap gap-4">
          <div>
            <h1 className="text-3xl font-bold text-white">🛡️ Bias Audit Report</h1>
            <p className="text-gray-400 mt-1 text-sm">Anonymization Engine Analysis — comparing full vs blind scoring</p>
          </div>
          <span className={`text-xs font-bold px-3 py-1.5 rounded-xl border ${
            summary.overall_fair ? 'border-green-500/30 bg-green-500/10 text-green-400' : 'border-amber-500/30 bg-amber-500/10 text-amber-400'
          }`}>
            Status: {summary.overall_fair ? 'Fair/Balanced' : 'Review Required'}
          </span>
        </div>

        {error ? (
          <div className="rounded-xl border border-red-500/30 bg-red-500/10 px-5 py-5 text-red-200">
            <div className="flex items-start gap-3">
              <AlertCircle className="h-5 w-5 text-red-400 flex-shrink-0 mt-0.5" />
              <div className="flex-1">
                <p className="font-semibold text-white">Bias report unavailable</p>
                <p className="mt-1 text-sm text-red-200/80">{error}</p>
                <button
                  onClick={loadBiasReport}
                  className="mt-4 inline-flex h-10 items-center justify-center rounded-xl bg-red-500/20 px-4 text-sm font-semibold text-red-100 hover:bg-red-500/30 transition-colors"
                >
                  Try again
                </button>
              </div>
            </div>
          </div>
        ) : biasData.length === 0 ? (
          <EmptyState
            icon="ShieldCheck"
            title="No candidates yet"
            description="Upload resumes to see your bias audit here."
          />
        ) : (
          <>

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
              {biasData.map((c, i) => {
                const delta = c.blind - c.full;
                const absDelta = Math.abs(delta);
                const isBiased = absDelta > 3;
                return (
                  <motion.div
                    key={c.name + i}
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
              <svg viewBox="0 0 100 100" className="w-28 h-28" role="img" aria-label="Donut chart representing the distribution of unbiased candidates vs candidates with potential bias">
                <circle cx="50" cy="50" r="40" fill="none" stroke="rgba(255,255,255,0.05)" strokeWidth="12" />
                {/* Unbiased arc (draws in on load) */}
                <motion.circle cx="50" cy="50" r="40" fill="none" stroke="#22c55e" strokeWidth="12"
                  initial={{ strokeDasharray: prefersReducedMotion ? `${(unbiasedPct / 100) * circumference} ${circumference}` : `0 ${circumference}` }}
                  animate={{ strokeDasharray: `${(unbiasedPct / 100) * circumference} ${circumference}` }}
                  transition={{ duration: prefersReducedMotion ? 0 : 0.9, ease: 'easeOut', delay: 0.2 }}
                  strokeDashoffset={circumference * 0.25}
                  strokeLinecap="round"
                />
                {/* Biased arc (draws in after the unbiased arc) */}
                <motion.circle cx="50" cy="50" r="40" fill="none" stroke="#f59e0b" strokeWidth="12"
                  initial={{ strokeDasharray: prefersReducedMotion ? `${biasedDash} ${circumference}` : `0 ${circumference}` }}
                  animate={{ strokeDasharray: `${biasedDash} ${circumference}` }}
                  transition={{ duration: prefersReducedMotion ? 0 : 0.7, ease: 'easeOut', delay: 0.9 }}
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
                <span className="text-theme-1 font-medium">{biasedCount} out of {biasData.length}</span> candidates showed score variance &gt;3 points when anonymized, suggesting possible demographic influence in the original scoring.
              </p>
              <div className="mt-4 space-y-2">
                <div className="flex justify-between text-xs">
                  <span className="text-gray-400">Avg full score</span>
                  <span className="text-theme-1 font-medium">{summary.avg_full}</span>
                </div>
                <div className="flex justify-between text-xs">
                  <span className="text-gray-400">Avg blind score</span>
                  <span className="text-cyan-400 font-medium">{summary.avg_blind}</span>
                </div>
              </div>
            </div>
          </div>
        </div>
          </>
        )}
      </div>
    </motion.div>
  );
}
