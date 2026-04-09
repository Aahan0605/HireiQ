import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Link, useNavigate } from 'react-router-dom';
import { Users, FileSearch, TrendingUp, Sparkles, Calendar, Target, Briefcase, Clock, Edit2, Check, X, Plus, Trash2, RefreshCw } from 'lucide-react';
import StatCard from '../components/StatCard';
import RecentCandidates from '../components/RecentCandidates';

const API = '/api/v1';

// ── Initial interview data ─────────────────────────────────
const INITIAL_INTERVIEWS = [
  { id: 1, name: 'Alice Chen',      role: 'Frontend Engineer', start: '09:00', end: '10:00', status: 'confirmed' },
  { id: 2, name: 'Bob Martinez',    role: 'Fullstack Engineer', start: '10:00', end: '11:00', status: 'confirmed' },
  { id: 3, name: 'Diana Park',      role: 'ML Engineer',        start: '11:00', end: '12:00', status: 'confirmed' },
  { id: 4, name: 'Frank Liu',       role: 'Backend Engineer',   start: '12:00', end: '13:00', status: 'confirmed' },
];

// ── Initial shortlist data ─────────────────────────────────
const ALL_CANDIDATES = [
  { id: 1, name: 'Diana Park',    score: 97, cost: 8  },
  { id: 2, name: 'Charlie Brown', score: 88, cost: 6  },
  { id: 3, name: 'Bob Martinez',  score: 85, cost: 6  },
  { id: 4, name: 'Alice Chen',    score: 94, cost: 9  },
  { id: 5, name: 'Sofia R.',      score: 91, cost: 10 },
  { id: 6, name: 'Marcus J.',     score: 82, cost: 7  },
];

// Format rupees in lakhs — e.g. 8 → "₹8L"
const fmt = (n) => `₹${n}L`;

// 0/1 Knapsack DP — selects candidates maximising score within budget
function knapsack(candidates, budget) {
  const n = candidates.length;
  const dp = Array(n + 1).fill(null).map(() => Array(budget + 1).fill(0));
  for (let i = 1; i <= n; i++) {
    const { score, cost } = candidates[i - 1];
    for (let w = 0; w <= budget; w++) {
      dp[i][w] = dp[i - 1][w];
      if (w >= cost) dp[i][w] = Math.max(dp[i][w], dp[i - 1][w - cost] + score);
    }
  }
  // Backtrack
  const selected = [];
  let w = budget;
  for (let i = n; i > 0; i--) {
    if (dp[i][w] !== dp[i - 1][w]) { selected.push(candidates[i - 1]); w -= candidates[i - 1].cost; }
  }
  return { selected, totalScore: dp[n][budget], budgetUsed: budget - w };
}

// ── Interview Schedule Modal ───────────────────────────────
function InterviewModal({ onClose }) {
  const [interviews, setInterviews] = useState(INITIAL_INTERVIEWS);
  const [editingId, setEditingId]   = useState(null);
  const [editForm, setEditForm]     = useState({});
  const [showAdd, setShowAdd]       = useState(false);
  const [newForm, setNewForm]       = useState({ name: '', role: '', start: '', end: '' });

  const startEdit = (iv) => { setEditingId(iv.id); setEditForm({ start: iv.start, end: iv.end }); };
  const saveEdit  = (id) => {
    setInterviews(prev => prev.map(iv => iv.id === id ? { ...iv, ...editForm, status: 'rescheduled' } : iv));
    setEditingId(null);
  };
  const cancelEdit = () => setEditingId(null);
  const removeInterview = (id) => setInterviews(prev => prev.filter(iv => iv.id !== id));

  const addInterview = () => {
    if (!newForm.name || !newForm.start || !newForm.end) return;
    setInterviews(prev => [...prev, { id: Date.now(), ...newForm, status: 'confirmed' }]);
    setNewForm({ name: '', role: '', start: '', end: '' });
    setShowAdd(false);
  };

  const statusBadge = (s) => s === 'rescheduled'
    ? 'bg-amber-500/20 text-amber-400'
    : 'bg-green-500/20 text-green-400';

  return (
    <div className="space-y-3">
      {/* Interview rows */}
      {interviews.map(iv => (
        <div key={iv.id} className="bg-black/20 dark:bg-black/30 rounded-xl p-3">
          {editingId === iv.id ? (
            // ── Edit row ──
            <div className="space-y-2">
              <p className="text-theme-1 text-sm font-medium">{iv.name} <span className="text-theme-3 text-xs">— {iv.role}</span></p>
              <div className="flex gap-2 items-center">
                <input type="time" value={editForm.start}
                  onChange={e => setEditForm(f => ({ ...f, start: e.target.value }))}
                  className="flex-1 rounded-lg border border-black/10 dark:border-white/10 bg-card px-2 py-1.5 text-theme-1 text-xs outline-none focus:border-emerald-500/40" />
                <span className="text-theme-3 text-xs">to</span>
                <input type="time" value={editForm.end}
                  onChange={e => setEditForm(f => ({ ...f, end: e.target.value }))}
                  className="flex-1 rounded-lg border border-black/10 dark:border-white/10 bg-card px-2 py-1.5 text-theme-1 text-xs outline-none focus:border-emerald-500/40" />
                <button onClick={() => saveEdit(iv.id)} className="p-1.5 rounded-lg bg-emerald-500/20 text-emerald-400 hover:bg-emerald-500/30 transition-all"><Check size={13} /></button>
                <button onClick={cancelEdit} className="p-1.5 rounded-lg bg-red-500/10 text-red-400 hover:bg-red-500/20 transition-all"><X size={13} /></button>
              </div>
            </div>
          ) : (
            // ── Display row ──
            <div className="flex items-center justify-between gap-2">
              <div className="flex-1 min-w-0">
                <p className="text-theme-1 text-sm font-medium truncate">{iv.name}</p>
                <p className="text-theme-3 text-xs">{iv.role}</p>
              </div>
              <div className="flex items-center gap-2 flex-shrink-0">
                <span className="text-theme-2 text-xs font-mono">{iv.start} – {iv.end}</span>
                <span className={`text-xs px-2 py-0.5 rounded-full font-medium ${statusBadge(iv.status)}`}>
                  {iv.status}
                </span>
                {/* Reschedule */}
                <button onClick={() => startEdit(iv)}
                  className="p-1.5 rounded-lg text-gray-400 hover:text-emerald-400 hover:bg-emerald-500/10 transition-all"
                  title="Reschedule">
                  <Clock size={13} />
                </button>
                {/* Remove */}
                <button onClick={() => removeInterview(iv.id)}
                  className="p-1.5 rounded-lg text-gray-400 hover:text-red-400 hover:bg-red-500/10 transition-all"
                  title="Remove">
                  <Trash2 size={13} />
                </button>
              </div>
            </div>
          )}
        </div>
      ))}

      {/* Add new interview */}
      {showAdd ? (
        <div className="bg-black/20 dark:bg-black/30 rounded-xl p-3 space-y-2">
          <div className="grid grid-cols-2 gap-2">
            <input placeholder="Candidate name" value={newForm.name}
              onChange={e => setNewForm(f => ({ ...f, name: e.target.value }))}
              className="rounded-lg border border-black/10 dark:border-white/10 bg-card px-2 py-1.5 text-theme-1 text-xs outline-none focus:border-emerald-500/40" />
            <input placeholder="Role" value={newForm.role}
              onChange={e => setNewForm(f => ({ ...f, role: e.target.value }))}
              className="rounded-lg border border-black/10 dark:border-white/10 bg-card px-2 py-1.5 text-theme-1 text-xs outline-none focus:border-emerald-500/40" />
          </div>
          <div className="flex gap-2 items-center">
            <input type="time" value={newForm.start}
              onChange={e => setNewForm(f => ({ ...f, start: e.target.value }))}
              className="flex-1 rounded-lg border border-black/10 dark:border-white/10 bg-card px-2 py-1.5 text-theme-1 text-xs outline-none focus:border-emerald-500/40" />
            <span className="text-theme-3 text-xs">to</span>
            <input type="time" value={newForm.end}
              onChange={e => setNewForm(f => ({ ...f, end: e.target.value }))}
              className="flex-1 rounded-lg border border-black/10 dark:border-white/10 bg-card px-2 py-1.5 text-theme-1 text-xs outline-none focus:border-emerald-500/40" />
          </div>
          <div className="flex gap-2">
            <button onClick={addInterview} className="flex-1 py-1.5 rounded-lg bg-emerald-600 hover:bg-emerald-700 text-white text-xs font-medium transition-all">Add</button>
            <button onClick={() => setShowAdd(false)} className="flex-1 py-1.5 rounded-lg border border-black/10 dark:border-white/10 text-theme-2 text-xs hover:bg-black/5 dark:hover:bg-white/5 transition-all">Cancel</button>
          </div>
        </div>
      ) : (
        <button onClick={() => setShowAdd(true)}
          className="w-full py-2 rounded-xl border border-dashed border-emerald-500/30 text-emerald-500 text-xs hover:bg-emerald-500/5 transition-all flex items-center justify-center gap-1.5">
          <Plus size={13} /> Add Interview Slot
        </button>
      )}

      <div className="flex items-center justify-between pt-1 text-xs text-theme-3">
        <span>{interviews.length} interview{interviews.length !== 1 ? 's' : ''} scheduled</span>
        <span>{interviews.filter(i => i.status === 'rescheduled').length} rescheduled</span>
      </div>

      <button onClick={onClose} className="w-full py-2 rounded-xl bg-emerald-600 hover:bg-emerald-700 text-white text-sm font-medium transition-all active:scale-95">
        Done
      </button>
    </div>
  );
}

// ── Optimal Shortlist Modal ────────────────────────────────
function ShortlistModal({ onClose }) {
  const [budget, setBudget]         = useState(20);
  const [pool, setPool]             = useState(ALL_CANDIDATES);
  const [result, setResult]         = useState(() => knapsack(ALL_CANDIDATES, 20));
  const [newName, setNewName]       = useState('');
  const [newScore, setNewScore]     = useState('');
  const [newCost, setNewCost]       = useState('');
  const [showAdd, setShowAdd]       = useState(false);

  const recalculate = (b, p) => setResult(knapsack(p, b));

  const handleBudgetChange = (val) => {
    const b = Math.max(1, Math.min(100, Number(val)));
    setBudget(b);
    recalculate(b, pool);
  };

  const removeCandidate = (id) => {
    const next = pool.filter(c => c.id !== id);
    setPool(next);
    recalculate(budget, next);
  };

  const addCandidate = () => {
    if (!newName || !newScore || !newCost) return;
    const next = [...pool, { id: Date.now(), name: newName, score: Number(newScore), cost: Number(newCost) }];
    setPool(next);
    recalculate(budget, next);
    setNewName(''); setNewScore(''); setNewCost('');
    setShowAdd(false);
  };

  const isSelected = (id) => result.selected.some(c => c.id === id);

  return (
    <div className="space-y-4">
      {/* Budget control */}
      <div className="bg-black/20 dark:bg-black/30 rounded-xl p-3">
        <div className="flex items-center justify-between mb-2">
          <span className="text-theme-2 text-xs font-medium">Hiring Budget (₹ Lakhs)</span>
          <div className="flex items-center gap-2">
            <button onClick={() => handleBudgetChange(budget - 1)}
              className="w-6 h-6 rounded-md bg-black/10 dark:bg-white/10 text-theme-1 text-sm flex items-center justify-center hover:bg-emerald-500/20 transition-all">−</button>
            <div className="flex items-center gap-0.5">
              <span className="text-theme-2 text-sm font-bold">₹</span>
              <input type="number" min="1" max="100" value={budget}
                onChange={e => handleBudgetChange(e.target.value)}
                className="w-14 text-center rounded-lg border border-black/10 dark:border-white/10 bg-card px-1 py-1 text-theme-1 text-sm font-bold outline-none focus:border-emerald-500/40" />
              <span className="text-theme-2 text-sm font-bold">L</span>
            </div>
            <button onClick={() => handleBudgetChange(budget + 1)}
              className="w-6 h-6 rounded-md bg-black/10 dark:bg-white/10 text-theme-1 text-sm flex items-center justify-center hover:bg-emerald-500/20 transition-all">+</button>
          </div>
        </div>
        {/* Budget bar */}
        <div className="h-1.5 w-full rounded-full bg-black/10 dark:bg-white/10">
          <div className="h-full rounded-full bg-gradient-to-r from-emerald-400 to-emerald-600 transition-all"
            style={{ width: `${Math.min(100, (result.budgetUsed / budget) * 100)}%` }} />
        </div>
        <div className="flex justify-between text-xs text-theme-3 mt-1">
          <span>Used: {fmt(result.budgetUsed)}</span>
          <span>Remaining: {fmt(budget - result.budgetUsed)}</span>
        </div>
      </div>

      {/* Result summary */}
      <div className="grid grid-cols-3 gap-2 text-center">
        {[
          { label: 'Selected',    value: result.selected.length,              color: 'text-emerald-400' },
          { label: 'Total Score',  value: result.totalScore,                   color: 'text-cyan-400' },
          { label: 'Budget Used',  value: `${fmt(result.budgetUsed)} / ${fmt(budget)}`, color: 'text-amber-400' },
        ].map(({ label, value, color }) => (
          <div key={label} className="bg-black/20 dark:bg-black/30 rounded-xl p-2">
            <p className={`text-lg font-bold ${color}`}>{value}</p>
            <p className="text-theme-3 text-xs">{label}</p>
          </div>
        ))}
      </div>

      {/* Candidate pool */}
      <div className="space-y-1.5 max-h-48 overflow-y-auto pr-1">
        {pool.map(c => (
          <div key={c.id}
            className={`flex items-center justify-between rounded-lg px-3 py-2 transition-all ${
              isSelected(c.id)
                ? 'bg-emerald-500/15 border border-emerald-500/30'
                : 'bg-black/10 dark:bg-white/5 border border-transparent'
            }`}>
            <div className="flex items-center gap-2">
              {isSelected(c.id)
                ? <Check size={13} className="text-emerald-400 flex-shrink-0" />
                : <div className="w-3.5 h-3.5 rounded-full border border-gray-500 flex-shrink-0" />}
              <span className="text-theme-1 text-xs font-medium">{c.name}</span>
            </div>
            <div className="flex items-center gap-3">
              <span className="text-theme-2 text-xs">Score: <b className="text-theme-1">{c.score}</b></span>
              <span className="text-theme-2 text-xs">CTC: <b className="text-theme-1">{fmt(c.cost)}</b></span>
              <button onClick={() => removeCandidate(c.id)}
                className="p-1 rounded text-gray-500 hover:text-red-400 hover:bg-red-500/10 transition-all">
                <Trash2 size={11} />
              </button>
            </div>
          </div>
        ))}
      </div>

      {/* Add candidate */}
      {showAdd ? (
        <div className="bg-black/20 dark:bg-black/30 rounded-xl p-3 space-y-2">
          <input placeholder="Candidate name" value={newName}
            onChange={e => setNewName(e.target.value)}
            className="w-full rounded-lg border border-black/10 dark:border-white/10 bg-card px-2 py-1.5 text-theme-1 text-xs outline-none focus:border-emerald-500/40" />
          <div className="grid grid-cols-2 gap-2">
            <input type="number" placeholder="Score (0-100)" value={newScore}
              onChange={e => setNewScore(e.target.value)}
              className="rounded-lg border border-black/10 dark:border-white/10 bg-card px-2 py-1.5 text-theme-1 text-xs outline-none focus:border-emerald-500/40" />
            <input type="number" placeholder="CTC in Lakhs (e.g. 8)" value={newCost}
              onChange={e => setNewCost(e.target.value)}
              className="rounded-lg border border-black/10 dark:border-white/10 bg-card px-2 py-1.5 text-theme-1 text-xs outline-none focus:border-emerald-500/40" />
          </div>
          <div className="flex gap-2">
            <button onClick={addCandidate} className="flex-1 py-1.5 rounded-lg bg-emerald-600 hover:bg-emerald-700 text-white text-xs font-medium transition-all">Add & Recalculate</button>
            <button onClick={() => setShowAdd(false)} className="flex-1 py-1.5 rounded-lg border border-black/10 dark:border-white/10 text-theme-2 text-xs hover:bg-black/5 dark:hover:bg-white/5 transition-all">Cancel</button>
          </div>
        </div>
      ) : (
        <button onClick={() => setShowAdd(true)}
          className="w-full py-2 rounded-xl border border-dashed border-emerald-500/30 text-emerald-500 text-xs hover:bg-emerald-500/5 transition-all flex items-center justify-center gap-1.5">
          <Plus size={13} /> Add Candidate to Pool
        </button>
      )}

      <button onClick={() => recalculate(budget, pool)}
        className="w-full py-2 rounded-xl border border-black/10 dark:border-white/10 text-theme-2 text-xs hover:bg-black/5 dark:hover:bg-white/5 transition-all flex items-center justify-center gap-1.5">
        <RefreshCw size={12} /> Recalculate Shortlist
      </button>

      <button onClick={onClose} className="w-full py-2 rounded-xl bg-emerald-600 hover:bg-emerald-700 text-white text-sm font-medium transition-all active:scale-95">
        Done
      </button>
    </div>
  );
}

// ── Main Dashboard ─────────────────────────────────────────
export default function Dashboard() {
  const [showModal, setShowModal] = useState(false);
  const [modalType, setModalType] = useState(null);
  const [openJobs, setOpenJobs]   = useState(null);
  const [analytics, setAnalytics] = useState(null);
  const navigate = useNavigate();

  useEffect(() => {
    fetch(`${API}/jobs`)
      .then(r => r.ok ? r.json() : [])
      .then(data => setOpenJobs(Array.isArray(data) ? data.filter(j => j.status === 'Open').length : 0))
      .catch(() => setOpenJobs(0));

    fetch(`${API}/settings/analytics`)
      .then(r => r.ok ? r.json() : null)
      .then(data => setAnalytics(data))
      .catch(() => setAnalytics(null));
  }, []);

  const openModal = (type) => { setModalType(type); setShowModal(true); };
  const closeModal = () => { setShowModal(false); setModalType(null); };

  const modalTitle = modalType === 'interviews' ? '📅 Interview Schedule' : '🎯 Optimal Shortlist';

  return (
    <motion.div initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.2 }}
      className="min-h-screen bg-page px-6 py-8 sm:px-10 lg:py-12">
      <div className="mx-auto max-w-5xl">

        {/* Header */}
        <motion.header initial={{ opacity: 0, y: -20 }} animate={{ opacity: 1, y: 0 }}
          className="mb-10 flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
          <div>
            <h1 className="font-display text-3xl font-bold text-theme-1">Dashboard</h1>
            <p className="text-theme-2 mt-1">Here's what's happening today.</p>
          </div>
          <Link to="/analyze"
            className="inline-flex h-11 items-center justify-center rounded-xl bg-emerald-500 px-5 font-semibold text-white transition-transform hover:scale-105 shadow-glow-mint">
            <Sparkles className="mr-2 h-4 w-4" /> Analyze Candidate
          </Link>
        </motion.header>

        {/* 4 Stat Cards */}
        <div className="grid gap-6 sm:grid-cols-2 lg:grid-cols-4 mb-8">
          <StatCard title="Total Candidates" value={analytics?.total_candidates ?? 0} icon={<Users className="h-5 w-5" />}    trend={analytics?.recent_uploads_7d ?? 0}  trendLabel="this week" delay={0.1} />
          <StatCard title="Strong Matches"   value={analytics?.strong_matches ?? 0}  icon={<FileSearch className="h-5 w-5" />} trend={analytics?.matches ?? 0}   trendLabel="good matches" delay={0.2} />
          <StatCard title="Avg Match Score"   value={analytics?.average_score ?? 0}   icon={<TrendingUp className="h-5 w-5" />} trend={0}  trendLabel="overall" delay={0.3} />
          <motion.div initial={{ opacity: 0, y: 28 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.4, duration: 0.6 }}
            onClick={() => navigate('/jobs')}
            className="cursor-pointer rounded-2xl border border-black/10 dark:border-white/10 bg-card p-6 hover:border-cyan-500/40 transition-all">
            <div className="flex items-start justify-between">
              <p className="text-sm font-medium text-theme-2">Open Positions</p>
              <div className="rounded-lg bg-cyan-500/10 p-2 text-cyan-400"><Briefcase className="h-5 w-5" /></div>
            </div>
            <p className="font-display text-4xl font-bold text-theme-1 mt-4 tracking-tight">
              {openJobs === null ? '—' : openJobs}
            </p>
            <p className="text-xs text-theme-3 mt-2">Active job listings</p>
          </motion.div>
        </div>

        {/* Algorithm Action Cards */}
        <div className="grid gap-6 sm:grid-cols-2 mb-8">
          <motion.button initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.5 }}
            onClick={() => openModal('interviews')}
            className="rounded-2xl border border-black/10 dark:border-white/10 bg-card p-6 hover:border-green-500/40 transition-all cursor-pointer text-left">
            <div className="flex items-start justify-between mb-4">
              <div>
                <p className="text-sm font-medium text-theme-2">Interviews Scheduled Today</p>
                <p className="text-3xl font-bold text-theme-1 mt-2">4</p>
                <p className="text-xs text-theme-3 mt-1">Click to view & reschedule</p>
              </div>
              <div className="flex h-12 w-12 items-center justify-center rounded-xl bg-green-500/15 text-green-400">
                <Calendar className="h-6 w-6" />
              </div>
            </div>
            <div className="h-1 w-full rounded-full bg-black/5 dark:bg-white/5">
              <div className="h-full w-4/5 rounded-full bg-gradient-to-r from-green-400 to-green-500" />
            </div>
          </motion.button>

          <motion.button initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.6 }}
            onClick={() => openModal('shortlist')}
            className="rounded-2xl border border-black/10 dark:border-white/10 bg-card p-6 hover:border-emerald-500/40 transition-all cursor-pointer text-left">
            <div className="flex items-start justify-between mb-4">
              <div>
                <p className="text-sm font-medium text-theme-2">Optimal Shortlist Size</p>
                <p className="text-3xl font-bold text-theme-1 mt-2">3</p>
                <p className="text-xs text-theme-3 mt-1">Click to edit budget & candidates</p>
              </div>
              <div className="flex h-12 w-12 items-center justify-center rounded-xl bg-emerald-500/15 text-emerald-400">
                <Target className="h-6 w-6" />
              </div>
            </div>
            <div className="h-1 w-full rounded-full bg-black/5 dark:bg-white/5">
              <div className="h-full w-3/5 rounded-full bg-gradient-to-r from-emerald-400 to-emerald-600" />
            </div>
          </motion.button>
        </div>

        {/* Recent Analyses */}
        <div className="grid gap-6 lg:grid-cols-2">
          <RecentCandidates />
        </div>
      </div>

      {/* Modal */}
      <AnimatePresence>
        {showModal && (
          <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}
            className="fixed inset-0 bg-black/60 backdrop-blur-sm z-50 flex items-center justify-center p-4"
            onClick={closeModal}>
            <motion.div initial={{ scale: 0.95, opacity: 0 }} animate={{ scale: 1, opacity: 1 }} exit={{ scale: 0.95, opacity: 0 }}
              onClick={e => e.stopPropagation()}
              className="bg-card border border-black/10 dark:border-white/10 rounded-2xl p-6 w-full max-w-md max-h-[85vh] overflow-y-auto shadow-2xl">
              <div className="flex items-center justify-between mb-5">
                <h3 className="text-theme-1 font-semibold text-lg">{modalTitle}</h3>
                <button onClick={closeModal} className="text-theme-3 hover:text-theme-1 transition-colors"><X size={18} /></button>
              </div>
              {modalType === 'interviews'
                ? <InterviewModal onClose={closeModal} />
                : <ShortlistModal onClose={closeModal} />}
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>
    </motion.div>
  );
}
