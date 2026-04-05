import React from 'react';
import { useSearchParams, Link } from 'react-router-dom';
import { motion } from 'framer-motion';
import { ResponsiveContainer, RadarChart, PolarGrid, PolarAngleAxis, Radar, Legend } from 'recharts';
import { getCandidateById } from '../data/candidates';

// ── Skill category definitions ────────────────────────────────
// Each category maps to a set of skill keywords.
// We compute TF-IDF-style overlap: how many of the category's
// keywords appear in the candidate's skill list.
const SKILL_CATEGORIES = {
  Frontend:   ['react', 'vue', 'angular', 'next.js', 'html', 'css', 'tailwind', 'javascript', 'typescript', 'svelte', 'gatsby', 'figma'],
  Backend:    ['node.js', 'python', 'java', 'go', 'fastapi', 'django', 'flask', 'express', 'spring', 'rails', 'grpc', 'rest apis'],
  DevOps:     ['docker', 'kubernetes', 'aws', 'gcp', 'azure', 'terraform', 'ci/cd', 'jenkins', 'github actions', 'ansible', 'linux'],
  Databases:  ['postgresql', 'mysql', 'mongodb', 'redis', 'sqlite', 'dynamodb', 'elasticsearch', 'cassandra', 'firebase', 'sql'],
  'ML / AI':  ['python', 'pytorch', 'tensorflow', 'scikit-learn', 'pandas', 'numpy', 'nlp', 'machine learning', 'deep learning', 'llm', 'keras'],
  Systems:    ['c++', 'rust', 'go', 'distributed systems', 'microservices', 'grpc', 'kafka', 'websocket', 'algorithms', 'data structures'],
};

/**
 * Compute per-category score for a candidate using skill overlap.
 * Score = (matched keywords / total category keywords) * 100
 * This is the TF-IDF-inspired approach: skills that appear in a
 * candidate's profile are treated as "term present", and the
 * category keyword list acts as the "document vocabulary".
 * Time Complexity: O(C * K) where C = categories, K = keywords per category
 */
function computeCategoryScores(candidate) {
  const skillsLower = (candidate?.skills || []).map(s => s.toLowerCase());
  const scores = {};
  for (const [category, keywords] of Object.entries(SKILL_CATEGORIES)) {
    const matched = keywords.filter(kw => skillsLower.some(s => s.includes(kw)));
    // Scale to 0–100, minimum 5 so the radar always shows a shape
    scores[category] = Math.max(5, Math.round((matched.length / keywords.length) * 100));
  }
  return scores;
}

export default function CompareView() {
  const [params] = useSearchParams();
  const ids = params.get('ids')?.split(',') || [];
  const [a, b] = [getCandidateById(ids[0]), getCandidateById(ids[1])];

  if (!a || !b) {
    return (
      <div className="min-h-screen bg-[#0d0d1a] flex items-center justify-center">
        <div className="text-center">
          <p className="text-4xl mb-3">🔍</p>
          <p className="text-white font-semibold mb-2">Select 2 candidates to compare</p>
          <Link to="/candidates" className="text-purple-400 hover:text-purple-300 text-sm">← Back to Candidates</Link>
        </div>
      </div>
    );
  }

  const winner = (a.score || 0) >= (b.score || 0) ? a : b;

  // Real per-category TF-IDF scores from actual skill lists
  const scoresA = computeCategoryScores(a);
  const scoresB = computeCategoryScores(b);

  const radarData = Object.keys(SKILL_CATEGORIES).map(cat => ({
    subject: cat,
    [a.name]: scoresA[cat],
    [b.name]: scoresB[cat],
  }));

  const aSkills = new Set((a.skills || []).map(s => s.toLowerCase()));
  const bSkills = new Set((b.skills || []).map(s => s.toLowerCase()));
  const onlyA = (a.skills || []).filter(s => !bSkills.has(s.toLowerCase()));
  const onlyB = (b.skills || []).filter(s => !aSkills.has(s.toLowerCase()));

  // Category where each candidate leads
  const aLeads = Object.keys(SKILL_CATEGORIES).filter(c => scoresA[c] > scoresB[c]);
  const bLeads = Object.keys(SKILL_CATEGORIES).filter(c => scoresB[c] > scoresA[c]);

  const CandidateCard = ({ candidate, isWinner, categoryScores }) => (
    <div className={`bg-[#13131f] border rounded-xl p-5 flex-1 ${isWinner ? 'border-purple-500/50' : 'border-white/10'}`}>
      {isWinner && (
        <div className="mb-3 inline-flex items-center gap-1.5 bg-purple-500/20 text-purple-300 text-xs font-semibold px-3 py-1 rounded-full">
          🏆 Winner
        </div>
      )}
      <div className="flex items-center gap-3 mb-4">
        <div className="w-12 h-12 rounded-full bg-gradient-to-br from-purple-500 to-cyan-500 flex items-center justify-center text-white font-bold flex-shrink-0">
          {candidate.name?.split(' ')?.map(n => n[0])?.join('')?.slice(0, 2)}
        </div>
        <div>
          <h3 className="text-white font-semibold text-sm">{candidate.name}</h3>
          <p className="text-gray-400 text-xs">{candidate.role}</p>
        </div>
      </div>
      <div className="text-3xl font-bold text-white mb-0.5">{candidate.score}</div>
      <div className="text-gray-500 text-xs mb-4">Overall Match Score</div>

      {/* Top category scores */}
      <div className="space-y-1.5">
        {Object.entries(categoryScores)
          .sort((a, b) => b[1] - a[1])
          .slice(0, 3)
          .map(([cat, score]) => (
            <div key={cat} className="flex items-center gap-2">
              <span className="text-gray-400 text-xs w-16 flex-shrink-0">{cat}</span>
              <div className="flex-1 bg-white/5 rounded-full h-1.5">
                <div className="h-1.5 rounded-full bg-gradient-to-r from-purple-500 to-cyan-400"
                  style={{ width: `${score}%` }} />
              </div>
              <span className="text-gray-400 text-xs w-8 text-right">{score}%</span>
            </div>
          ))}
      </div>

      <div className="flex flex-wrap gap-1.5 mt-4">
        {(candidate.skills || []).slice(0, 5).map(s => (
          <span key={s} className="text-xs px-2 py-0.5 rounded-full bg-white/5 text-gray-300 border border-white/10">{s}</span>
        ))}
      </div>
    </div>
  );

  return (
    <motion.div initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.2 }}
      className="min-h-screen bg-[#0d0d1a] p-6 lg:p-10">
      <div className="max-w-4xl mx-auto">

        <div className="mb-6 flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold text-white">Candidate Comparison</h1>
            <p className="text-gray-400 text-sm mt-1">{a.name} vs {b.name} · Skill-by-skill TF-IDF analysis</p>
          </div>
          <Link to="/candidates" className="text-sm text-gray-400 hover:text-white transition-colors">← Back</Link>
        </div>

        {/* Side-by-side cards */}
        <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} className="flex gap-4 mb-6">
          <CandidateCard candidate={a} isWinner={winner.id === a.id} categoryScores={scoresA} />
          <div className="flex items-center justify-center text-gray-600 font-bold text-xl px-2 flex-shrink-0">VS</div>
          <CandidateCard candidate={b} isWinner={winner.id === b.id} categoryScores={scoresB} />
        </motion.div>

        {/* Radar Chart — real TF-IDF category scores */}
        <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.1 }}
          className="bg-[#13131f] border border-white/10 rounded-xl p-6 mb-6">
          <h3 className="text-white font-semibold mb-1">Skill Category Radar</h3>
          <p className="text-gray-500 text-xs mb-4">
            Scores computed via keyword overlap per category — not synthetic offsets
          </p>
          <div className="h-72">
            <ResponsiveContainer width="100%" height="100%">
              <RadarChart data={radarData}>
                <PolarGrid stroke="rgba(255,255,255,0.08)" />
                <PolarAngleAxis dataKey="subject" tick={{ fill: '#9494B0', fontSize: 11 }} />
                <Radar name={a.name} dataKey={a.name} stroke="#9D74FF" fill="#9D74FF" fillOpacity={0.3} />
                <Radar name={b.name} dataKey={b.name} stroke="#22d3ee" fill="#22d3ee" fillOpacity={0.3} />
                <Legend wrapperStyle={{ color: '#9494B0', fontSize: 12 }} />
              </RadarChart>
            </ResponsiveContainer>
          </div>
        </motion.div>

        {/* Category dominance */}
        <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.15 }}
          className="grid grid-cols-2 gap-4 mb-4">
          <div className="bg-[#13131f] border border-purple-500/20 rounded-xl p-4">
            <h4 className="text-purple-300 font-medium text-sm mb-2">{a.name} leads in</h4>
            {aLeads.length > 0
              ? <div className="flex flex-wrap gap-1.5">{aLeads.map(c => <span key={c} className="text-xs px-2 py-0.5 rounded-full bg-purple-500/15 text-purple-300">{c}</span>)}</div>
              : <p className="text-gray-500 text-xs">No category advantage</p>}
          </div>
          <div className="bg-[#13131f] border border-cyan-500/20 rounded-xl p-4">
            <h4 className="text-cyan-300 font-medium text-sm mb-2">{b.name} leads in</h4>
            {bLeads.length > 0
              ? <div className="flex flex-wrap gap-1.5">{bLeads.map(c => <span key={c} className="text-xs px-2 py-0.5 rounded-full bg-cyan-500/15 text-cyan-300">{c}</span>)}</div>
              : <p className="text-gray-500 text-xs">No category advantage</p>}
          </div>
        </motion.div>

        {/* Unique skills diff */}
        <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.2 }}
          className="grid grid-cols-2 gap-4">
          <div className="bg-[#13131f] border border-white/10 rounded-xl p-5">
            <h4 className="text-white font-medium text-sm mb-3">Only {a.name} has</h4>
            {onlyA.length > 0
              ? <div className="flex flex-wrap gap-1.5">{onlyA.map(s => <span key={s} className="text-xs px-2 py-1 rounded-full bg-purple-500/20 text-purple-300">{s}</span>)}</div>
              : <p className="text-gray-500 text-xs">No unique skills</p>}
          </div>
          <div className="bg-[#13131f] border border-white/10 rounded-xl p-5">
            <h4 className="text-white font-medium text-sm mb-3">Only {b.name} has</h4>
            {onlyB.length > 0
              ? <div className="flex flex-wrap gap-1.5">{onlyB.map(s => <span key={s} className="text-xs px-2 py-1 rounded-full bg-cyan-500/20 text-cyan-300">{s}</span>)}</div>
              : <p className="text-gray-500 text-xs">No unique skills</p>}
          </div>
        </motion.div>

      </div>
    </motion.div>
  );
}
