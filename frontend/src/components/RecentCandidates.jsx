import React, { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import { Link } from 'react-router-dom';
import { fadeUp } from '../lib/animations';
import { getAllCandidates } from '../data/candidates';

const API = '/api/v1';

// Find the job whose required_skills has the most keyword overlap with the candidate's role
function getBestJobMatch(candidate, jobs) {
  if (!jobs?.length) return null;
  const roleWords = (candidate?.role || '').toLowerCase().split(/\s+/);
  let best = null, bestScore = -1;
  for (const job of jobs) {
    const skillWords = (job.required_skills || '').toLowerCase().split(/[,\s]+/);
    const overlap = roleWords.filter(w => w.length > 2 && skillWords.some(s => s.includes(w))).length;
    if (overlap > bestScore) { bestScore = overlap; best = job; }
  }
  return best;
}

export default function RecentCandidates() {
  const [jobs, setJobs] = useState([]);

  useEffect(() => {
    fetch(`${API}/jobs`)
      .then(r => r.ok ? r.json() : [])
      .then(data => setJobs(Array.isArray(data) ? data : []))
      .catch(() => {});
  }, []);

  // Deduplicate by name, take top 5
  const allCandidates = getAllCandidates();
  const candidates = [...new Map(allCandidates.map(c => [c?.name?.toLowerCase(), c])).values()].slice(0, 5);

  return (
    <motion.div variants={fadeUp} initial="initial" animate="animate"
      className="col-span-1 overflow-hidden lg:col-span-2 rounded-2xl border border-black/10 dark:border-white/10 bg-card p-6">

      <div className="mb-6 flex items-center justify-between">
        <h2 className="text-xl font-semibold text-white">Recent Analyses</h2>
        <Link to="/candidates" className="text-sm font-medium text-emerald-500 transition-colors hover:text-emerald-400">
          View all
        </Link>
      </div>

      <div className="flex flex-col gap-3">
        {candidates.map((c, i) => {
          const bestJob = getBestJobMatch(c, jobs);
          return (
            <motion.div key={c.id} initial={{ opacity: 0, x: -10 }} animate={{ opacity: 1, x: 0, transition: { delay: i * 0.08 } }}>
              <Link to={`/candidate/${c.id}`}
                className="group flex items-center justify-between rounded-xl border border-white/5 bg-white/5 p-4 transition-colors hover:border-emerald-500/30 hover:bg-white/10">

                <div className="flex items-center gap-4">
                  <div className="flex h-10 w-10 items-center justify-center rounded-full bg-card-2 text-sm font-bold text-emerald-500 group-hover:bg-emerald-500 group-hover:text-bg transition-colors">
                    {c.name?.split(' ').map(n => n[0]).join('')}
                  </div>
                  <div>
                    <h3 className="font-medium text-gray-100 group-hover:text-white transition-colors text-sm">{c.name}</h3>
                    <p className="text-xs text-gray-500">{c.role}</p>
                    {/* Best job match line */}
                    <p className="text-xs text-gray-600 mt-0.5">
                      Best fit: {bestJob?.title ?? 'No open positions'}
                    </p>
                  </div>
                </div>

                <div className="flex items-center gap-3 text-right">
                  <span className={`hidden sm:inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium ${
                    c.score >= 90 ? 'bg-green-500/15 text-green-400' :
                    c.score >= 80 ? 'bg-emerald-500/15 text-emerald-500' :
                                    'bg-amber-500/15 text-amber-400'
                  }`}>
                    {c.status}
                  </span>
                  <div className="flex flex-col items-end">
                    <span className="font-display text-lg font-bold text-white tracking-tight">{c.score}</span>
                    <span className="text-[10px] uppercase text-gray-600">Score</span>
                  </div>
                </div>
              </Link>
            </motion.div>
          );
        })}
      </div>
    </motion.div>
  );
}
