import React, { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import { Link, useParams, useNavigate } from 'react-router-dom';
import { ArrowLeft } from 'lucide-react';

const API = 'http://localhost:8000/api/v1';

// Gold / silver / bronze / gray rank colours
const rankStyle = (i) => {
  if (i === 0) return 'bg-yellow-400/20 text-yellow-300 border-yellow-400/30';
  if (i === 1) return 'bg-gray-300/20 text-gray-300 border-gray-300/30';
  if (i === 2) return 'bg-amber-600/20 text-amber-400 border-amber-600/30';
  return 'bg-white/5 text-gray-500 border-white/10';
};

const scoreStyle = (s) =>
  s >= 80 ? 'bg-green-500/20 text-green-400' :
  s >= 60 ? 'bg-yellow-500/20 text-yellow-400' :
             'bg-red-500/20 text-red-400';

export default function JobMatches() {
  const { id } = useParams();
  const navigate = useNavigate();
  const [job, setJob]         = useState(null);
  const [matches, setMatches] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError]     = useState('');

  useEffect(() => {
    Promise.all([
      fetch(`${API}/jobs/${id}`).then(r => { if (!r.ok) throw new Error(); return r.json(); }),
      fetch(`${API}/jobs/${id}/matches`).then(r => { if (!r.ok) throw new Error(); return r.json(); }),
    ])
      .then(([jobData, matchData]) => { setJob(jobData); setMatches(matchData); })
      .catch(() => setError('Failed to load. Is the backend running?'))
      .finally(() => setLoading(false));
  }, [id]);

  return (
    <motion.div initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.2 }}
      className="min-h-screen bg-[#0d0d1a] p-6 lg:p-10">
      <div className="max-w-4xl mx-auto">

        {/* Back */}
        <Link to="/jobs" className="inline-flex items-center gap-2 text-gray-400 hover:text-white text-sm mb-6 transition-colors">
          <ArrowLeft size={16} /> Back to Jobs
        </Link>

        {/* Error */}
        {error && (
          <div className="mb-5 rounded-xl border border-red-500/30 bg-red-500/10 px-4 py-3 text-red-400 text-sm">⚠️ {error}</div>
        )}

        {/* Header */}
        {job && (
          <div className="mb-8">
            <h1 className="text-3xl font-bold text-white mb-2">{job.title}</h1>
            <div className="flex flex-wrap gap-2 mb-1">
              <span className="text-xs px-2.5 py-1 rounded-full bg-white/5 text-gray-400">{job.department}</span>
              <span className="text-xs px-2.5 py-1 rounded-full bg-white/5 text-gray-400">{job.location}</span>
            </div>
          </div>
        )}

        {/* Skeleton */}
        {loading && (
          <div className="space-y-3">
            {Array(5).fill(0).map((_, i) => (
              <div key={i} className="h-20 rounded-xl border border-white/10 bg-[#13131f] animate-pulse" />
            ))}
          </div>
        )}

        {/* Empty */}
        {!loading && !error && matches.length === 0 && (
          <div className="py-20 text-center">
            <p className="text-4xl mb-3">📭</p>
            <p className="text-gray-400 text-sm">No candidates analyzed yet. Upload resumes to see matches.</p>
          </div>
        )}

        {/* Ranked list */}
        {!loading && matches.length > 0 && (
          <div className="space-y-3 mb-6">
            {matches.map((c, i) => (
              <motion.div key={c.id}
                initial={{ opacity: 0, x: -10 }} animate={{ opacity: 1, x: 0, transition: { delay: i * 0.05 } }}
                className="bg-[#13131f] border border-white/10 rounded-xl p-4 flex items-start gap-4 hover:border-purple-500/30 transition-all">

                {/* Rank badge */}
                <div className={`flex-shrink-0 w-9 h-9 rounded-full border flex items-center justify-center text-xs font-bold ${rankStyle(i)}`}>
                  #{i + 1}
                </div>

                {/* Avatar */}
                <div className="flex-shrink-0 w-10 h-10 rounded-full bg-gradient-to-br from-purple-500 to-cyan-500 flex items-center justify-center text-white text-sm font-bold">
                  {c.name?.split(' ').map(n => n[0]).join('').slice(0, 2)}
                </div>

                {/* Info */}
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2 flex-wrap">
                    <p className="text-white font-semibold text-sm">{c.name}</p>
                    <p className="text-gray-400 text-xs">{c.role}</p>
                    <span className={`text-xs px-2.5 py-0.5 rounded-full font-medium ${scoreStyle(c.match_score)}`}>
                      {c.match_score}% match
                    </span>
                  </div>

                  {/* Matched skills */}
                  {c.matched_skills?.length > 0 && (
                    <div className="flex flex-wrap gap-1 mt-2">
                      {c.matched_skills.map(s => (
                        <span key={s} className="text-xs px-2 py-0.5 rounded-full bg-green-500/15 text-green-400">{s}</span>
                      ))}
                    </div>
                  )}

                  {/* Missing skills */}
                  {c.missing_skills?.length > 0 && (
                    <div className="flex flex-wrap gap-1 mt-1">
                      {c.missing_skills.map(s => (
                        <span key={s} className="text-xs px-2 py-0.5 rounded-full bg-red-500/10 text-red-400 line-through">{s}</span>
                      ))}
                    </div>
                  )}
                </div>

                {/* View profile */}
                <button onClick={() => navigate(`/candidate/${c.id}`)}
                  className="flex-shrink-0 text-xs px-3 py-1.5 rounded-lg bg-purple-600/25 hover:bg-purple-600/45 text-purple-300 transition-all">
                  View Profile →
                </button>
              </motion.div>
            ))}
          </div>
        )}

      </div>
    </motion.div>
  );
}
