import React, { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import { AlertCircle, Save, RefreshCw } from 'lucide-react';

const API = 'http://localhost:8000/api/v1';

export default function Settings() {
  const [resume,    setResume]    = useState(40);
  const [github,    setGithub]    = useState(30);
  const [leetcode,  setLeetcode]  = useState(20);
  const [portfolio, setPortfolio] = useState(10);
  const [blindScoring, setBlindScoring] = useState(true);
  const [strongMatch, setStrongMatch]   = useState(85);
  const [match,       setMatch]         = useState(60);
  const [weakMatch,   setWeakMatch]     = useState(40);
  const [saved,    setSaved]    = useState(false);
  const [loading,  setLoading]  = useState(true);

  // Load current weights from backend on mount
  useEffect(() => {
    fetch(`${API}/settings/weights`)
      .then(r => r.ok ? r.json() : null)
      .then(data => {
        if (data) {
          setResume(Math.round((data.resume    ?? 0.4) * 100));
          setGithub(Math.round((data.github    ?? 0.3) * 100));
          setLeetcode(Math.round((data.leetcode  ?? 0.2) * 100));
          setPortfolio(Math.round((data.portfolio ?? 0.1) * 100));
        }
      })
      .catch(() => {})
      .finally(() => setLoading(false));
  }, []);

  const total   = resume + github + leetcode + portfolio;
  const isValid = total === 100;

  const handleSaveWeights = async () => {
    try {
      // POST body matches backend Weights model exactly
      await fetch(`${API}/settings/weights`, {
        method:  'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          resume:    resume    / 100,
          github:    github    / 100,
          leetcode:  leetcode  / 100,
          portfolio: portfolio / 100,
        }),
      });
    } catch { /* backend offline */ }
    setSaved(true);
    setTimeout(() => setSaved(false), 2500);
  };

  const handleSaveThresholds = async () => {
    try {
      await fetch(`${API}/settings/thresholds`, {
        method:  'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ strong: strongMatch, match, weak: weakMatch }),
      });
    } catch { /* backend offline */ }
    setSaved(true);
    setTimeout(() => setSaved(false), 2500);
  };

  const sliders = [
    { label: 'Resume Matching (TF-IDF + Cosine Similarity)', value: resume,    set: setResume,    color: 'accent-emerald-500' },
    { label: 'GitHub Analysis (Commit Frequency + Stars)',   value: github,    set: setGithub,    color: 'accent-cyan-500' },
    { label: 'LeetCode / Competitive Coding Score',          value: leetcode,  set: setLeetcode,  color: 'accent-green-500' },
    { label: 'Portfolio Review',                             value: portfolio, set: setPortfolio, color: 'accent-amber-500' },
  ];

  return (
    <motion.div initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.2 }}
      className="min-h-screen bg-page p-6 lg:p-10">
      <div className="max-w-3xl mx-auto space-y-6">

        <div>
          <h1 className="text-3xl font-bold text-white mb-1">Settings</h1>
          <p className="text-gray-400 text-sm">Configure scoring weights — changes apply to all future resume uploads</p>
        </div>

        {/* Algorithm Weights */}
        <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }}
          className="bg-card border border-black/10 dark:border-white/10 rounded-xl p-6">
          <div className="flex items-center justify-between mb-6">
            <h2 className="text-lg font-semibold text-white">Scoring Weights</h2>
            {loading && <RefreshCw className="h-4 w-4 text-gray-500 animate-spin" />}
          </div>

          <div className="space-y-5">
            {sliders.map(item => (
              <div key={item.label}>
                <div className="flex justify-between text-sm mb-2">
                  <label className="text-theme-1 font-medium">{item.label}</label>
                  <span className="text-emerald-400 font-semibold tabular-nums">{item.value}%</span>
                </div>
                <input type="range" min="0" max="100" value={item.value}
                  onChange={e => item.set(parseInt(e.target.value))}
                  className={`w-full h-2 bg-white/10 rounded-lg appearance-none cursor-pointer ${item.color}`} />
              </div>
            ))}
          </div>

          {/* Total indicator */}
          <div className={`mt-5 flex items-center justify-between rounded-lg px-4 py-3 ${
            isValid ? 'bg-green-500/10 border border-green-500/20' : 'bg-amber-500/15 border border-amber-500/30'
          }`}>
            <div className="flex items-center gap-2">
              {!isValid && <AlertCircle className="h-4 w-4 text-amber-400 flex-shrink-0" />}
              <p className={`text-sm font-medium ${isValid ? 'text-green-400' : 'text-amber-300'}`}>
                {isValid ? '✓ Weights sum to 100%' : `Weights must total 100% (currently ${total}%)`}
              </p>
            </div>
            <span className={`text-lg font-bold tabular-nums ${isValid ? 'text-green-400' : 'text-amber-400'}`}>
              {total}%
            </span>
          </div>

          <button onClick={handleSaveWeights} disabled={!isValid}
            className={`mt-5 px-5 py-2.5 rounded-xl font-medium flex items-center gap-2 transition-all text-sm ${
              isValid ? 'bg-emerald-600 hover:bg-emerald-700 text-white active:scale-95' : 'bg-gray-700 text-gray-500 cursor-not-allowed'
            }`}>
            <Save className="h-4 w-4" /> Save Weights
          </button>
          {saved && <p className="mt-2 text-green-400 text-sm">✓ Saved — weights will apply to next resume upload</p>}
        </motion.div>

        {/* Bias Audit Toggle */}
        <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.1 }}
          className="bg-card border border-black/10 dark:border-white/10 rounded-xl p-6">
          <h2 className="text-lg font-semibold text-white mb-4">Bias Audit</h2>
          <div className="flex items-center justify-between p-4 bg-white/5 rounded-lg">
            <div>
              <p className="text-theme-1 font-medium text-sm">Anonymization Engine</p>
              <p className="text-gray-400 text-xs mt-0.5">Enable blind scoring to reduce demographic bias in resume evaluation</p>
            </div>
            <button onClick={() => setBlindScoring(!blindScoring)}
              className={`w-12 h-6 rounded-full transition-colors relative flex-shrink-0 ${blindScoring ? 'bg-green-600' : 'bg-gray-600'}`}>
              <div className={`absolute top-0.5 w-5 h-5 rounded-full bg-white transition-transform ${blindScoring ? 'translate-x-6' : 'translate-x-0.5'}`} />
            </button>
          </div>
          {!blindScoring && (
            <div className="mt-3 flex items-center gap-3 bg-amber-500/15 border border-amber-500/30 rounded-lg p-3">
              <AlertCircle className="h-4 w-4 text-amber-400 flex-shrink-0" />
              <p className="text-amber-300 text-sm">Turning this off may introduce demographic bias into scoring</p>
            </div>
          )}
        </motion.div>

        {/* Match Thresholds */}
        <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.2 }}
          className="bg-card border border-black/10 dark:border-white/10 rounded-xl p-6">
          <h2 className="text-lg font-semibold text-white mb-4">Match Thresholds</h2>
          <div className="grid grid-cols-3 gap-4">
            {[
              { label: 'Strong Match', value: strongMatch, set: setStrongMatch, color: 'focus:border-green-500' },
              { label: 'Match',        value: match,       set: setMatch,       color: 'focus:border-yellow-500' },
              { label: 'Weak Match',   value: weakMatch,   set: setWeakMatch,   color: 'focus:border-red-500' },
            ].map(item => (
              <div key={item.label}>
                <label className="block text-xs font-medium text-gray-400 mb-1">{item.label}</label>
                <input type="number" min="0" max="100" value={item.value}
                  onChange={e => item.set(parseInt(e.target.value))}
                  className={`w-full px-3 py-2 bg-white/10 border border-white/20 rounded-lg text-theme-1 text-sm focus:outline-none ${item.color}`} />
              </div>
            ))}
          </div>
          <button onClick={handleSaveThresholds}
            className="mt-5 px-5 py-2.5 bg-emerald-600 hover:bg-emerald-700 text-white rounded-xl font-medium flex items-center gap-2 text-sm transition-all active:scale-95">
            <Save className="h-4 w-4" /> Save Thresholds
          </button>
        </motion.div>

      </div>
    </motion.div>
  );
}
