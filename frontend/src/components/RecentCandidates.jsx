import React from 'react';
import { motion } from 'framer-motion';
import { Link } from 'react-router-dom';
import { fadeUp } from '../lib/animations';
import { getAllCandidates } from '../data/candidates';

export default function RecentCandidates() {
  const candidates = getAllCandidates().slice(0, 5);

  return (
    <motion.div
      variants={fadeUp}
      initial="initial"
      animate="animate"
      className="col-span-1 overflow-hidden lg:col-span-2 rounded-2xl border border-border bg-surface/50 p-6 backdrop-blur-md"
    >
      <div className="mb-6 flex items-center justify-between">
        <h2 className="text-xl font-semibold text-white">Recent Analyses</h2>
        <Link to="/analyze" className="text-sm font-medium text-violet transition-colors hover:text-mint">
          View all
        </Link>
      </div>

      <div className="flex flex-col gap-3">
        {candidates.map((c, i) => (
          <motion.div
            key={c.id}
            initial={{ opacity: 0, x: -10 }}
            animate={{ opacity: 1, x: 0, transition: { delay: i * 0.1 } }}
          >
            <Link
              to={`/candidate/${c.id}`}
              className="group flex items-center justify-between rounded-xl border border-border/50 bg-surface-2 p-4 transition-colors hover:border-violet/30 hover:bg-surface-3"
            >
              <div className="flex items-center gap-4">
                <div className="flex h-10 w-10 items-center justify-center rounded-full bg-surface-3 text-sm font-bold text-violet group-hover:bg-violet group-hover:text-bg transition-colors">
                  {c.name.split(' ').map(n => n[0]).join('')}
                </div>
                <div>
                  <h3 className="font-medium text-text-1 group-hover:text-white transition-colors">{c.name}</h3>
                  <p className="text-xs text-text-3">{c.role}</p>
                </div>
              </div>

              <div className="flex items-center gap-4 text-right">
                <div className="hidden sm:block">
                  <span className={`inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium ${
                    c.score >= 90 ? 'bg-mint/10 text-mint' :
                    c.score >= 80 ? 'bg-violet/10 text-violet' :
                    'bg-amber/10 text-amber'
                  }`}>
                    {c.status}
                  </span>
                </div>
                
                <div className="flex flex-col items-end">
                  <span className="font-display text-lg font-bold text-white tracking-tight">{c.score}</span>
                  <span className="text-[10px] uppercase text-text-3">Score</span>
                </div>
              </div>
            </Link>
          </motion.div>
        ))}
      </div>
    </motion.div>
  );
}
