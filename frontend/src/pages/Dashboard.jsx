import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Link, useNavigate } from 'react-router-dom';
import { Users, FileSearch, TrendingUp, Sparkles, Calendar, Target, Briefcase, Clock, Edit2, Check, X, Plus, Trash2, RefreshCw, Github } from 'lucide-react';
import { toast } from 'sonner';
import { ResponsiveContainer, BarChart, Bar, XAxis, YAxis, Tooltip, PieChart, Pie, Cell } from 'recharts';
import StatCard from '../components/StatCard';
import RecentCandidates from '../components/RecentCandidates';
import { apiFetch } from '../lib/apiFetch';

const API = '/api/v1';

const PIE_COLORS = ['#10b981', '#06b6d4', '#f59e0b', '#6366f1'];

const CustomTooltip = ({ active, payload, label }) => {
  if (active && payload && payload.length) {
    return (
      <div className="bg-black/90 backdrop-blur-md border border-white/10 p-3 rounded-xl shadow-xl">
        <p className="text-gray-400 text-xs font-semibold">{label}</p>
        <p className="text-emerald-400 text-sm font-bold mt-1">
          {payload[0].name}: {payload[0].value}
        </p>
      </div>
    );
  }
  return null;
};

const CustomPieTooltip = ({ active, payload }) => {
  if (active && payload && payload.length) {
    return (
      <div className="bg-black/90 backdrop-blur-md border border-white/10 p-3 rounded-xl shadow-xl">
        <p className="text-gray-400 text-xs font-semibold">{payload[0].name}</p>
        <p className="text-cyan-400 text-sm font-bold mt-1">
          Candidates: {payload[0].value}
        </p>
      </div>
    );
  }
  return null;
};

// DEMO DATA — only used as a fallback when localStorage is empty AND
// the user has zero real candidates. Cleared automatically once real
// candidate data exists (see useEffect above).
const INITIAL_INTERVIEWS = [
  { id: 1, name: 'Alice Chen',      role: 'Frontend Engineer', start: '09:00', end: '10:00', status: 'confirmed' },
  { id: 2, name: 'Bob Martinez',    role: 'Fullstack Engineer', start: '10:00', end: '11:00', status: 'confirmed' },
  { id: 3, name: 'Diana Park',      role: 'ML Engineer',        start: '11:00', end: '12:00', status: 'confirmed' },
  { id: 4, name: 'Frank Liu',       role: 'Backend Engineer',   start: '12:00', end: '13:00', status: 'confirmed' },
];

// DEMO DATA — only used as a fallback when localStorage is empty AND
// the user has zero real candidates. Cleared automatically once real
// candidate data exists (see useEffect above).
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

// ── Interview Schedule Modal ───────────────────────────────
function InterviewModal({ onClose, onUpdateCount }) {
  const [interviews, setInterviews] = useState([]);
  const [candidates, setCandidates] = useState([]);
  const [optimizing, setOptimizing] = useState(false);
  const [showAdd, setShowAdd] = useState(false);
  const [newForm, setNewForm] = useState({ name: '', role: '', start: '09:00', end: '10:00' });
  const [editingId, setEditingId] = useState(null);
  const [editForm, setEditForm] = useState({});

  useEffect(() => {
    const loadModalData = async () => {
      const [interviewsResult, candidatesResult] = await Promise.allSettled([
        apiFetch(`${API}/candidates/interviews/all`).then(r => r.ok ? r.json() : []),
        apiFetch(`${API}/candidates`).then(r => r.ok ? r.json() : []),
      ]);

      if (interviewsResult.status === 'fulfilled') {
        setInterviews(Array.isArray(interviewsResult.value) ? interviewsResult.value : []);
      } else {
        console.error('Failed to load interviews:', interviewsResult.reason);
      }

      if (candidatesResult.status === 'fulfilled') {
        const data = candidatesResult.value;
        setCandidates(Array.isArray(data) ? data : (data?.data || []));
      } else {
        console.error('Failed to load candidates:', candidatesResult.reason);
      }
    };

    loadModalData();
  }, []);

  const saveInterviews = (updated) => {
    setInterviews(updated);
    if (onUpdateCount) {
      const active = updated.filter(i => i.status === 'confirmed' || i.status === 'rescheduled').length;
      onUpdateCount(active);
    }
  };

  const startEdit = (iv) => {
    setEditingId(iv.id);
    setEditForm({ start: iv.start, end: iv.end });
  };

  const saveEdit = async (id) => {
    if (editForm.start >= editForm.end) {
      toast.error("Start time must be before end time");
      return;
    }
    try {
      const res = await apiFetch(`${API}/candidates/interviews/${id}`, {
        method: 'PATCH',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          start: editForm.start,
          end: editForm.end,
          status: 'rescheduled'
        })
      });
      if (res.ok) {
        const updated = interviews.map(iv => iv.id === id ? { ...iv, ...editForm, status: 'rescheduled' } : iv);
        saveInterviews(updated);
        setEditingId(null);
        toast.success("Time slot updated! Click 'Optimize Schedule' to resolve conflicts.");
      } else {
        toast.error("Failed to update interview slot on server.");
      }
    } catch (err) {
      toast.error("Network error updating interview.");
    }
  };

  const cancelEdit = () => setEditingId(null);

  const removeInterview = async (id) => {
    try {
      const res = await apiFetch(`${API}/candidates/interviews/${id}`, {
        method: 'DELETE'
      });
      if (res.ok) {
        const updated = interviews.filter(iv => iv.id !== id);
        saveInterviews(updated);
        toast.success("Slot removed");
      } else {
        toast.error("Failed to remove interview slot from server.");
      }
    } catch (err) {
      toast.error("Network error removing interview slot.");
    }
  };

  const addInterview = async () => {
    if (!newForm.name) {
      toast.error("Please enter candidate name");
      return;
    }
    if (newForm.start >= newForm.end) {
      toast.error("Start time must be before end time");
      return;
    }

    const cand = candidates.find(c => c.name.toLowerCase() === newForm.name.toLowerCase());
    if (!cand) {
      toast.error("Please select an existing candidate from the list.");
      return;
    }

    const datePart = new Date().toISOString().split('T')[0];
    const scheduled_at = `${datePart}T${newForm.start}:00Z`;

    const [startH, startM] = newForm.start.split(':').map(Number);
    const [endH, endM] = newForm.end.split(':').map(Number);
    const duration_minutes = (endH * 60 + endM) - (startH * 60 + startM);

    const reqData = {
      scheduled_at,
      duration_minutes,
      interviewer_name: 'Senior Interviewer',
      status: 'pending'
    };

    try {
      const res = await apiFetch(`${API}/candidates/${cand.id}/interviews`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(reqData)
      });
      if (res.ok) {
        const saved = await res.json();
        const newIv = {
          id: saved.id,
          candidate_id: cand.id,
          name: cand.name,
          role: cand.role || 'Software Engineer',
          start: newForm.start,
          end: newForm.end,
          status: 'pending',
          scheduled_at: saved.scheduled_at,
          duration_minutes: saved.duration_minutes,
          interviewer_name: saved.interviewer_name
        };
        const updated = [...interviews, newIv];
        saveInterviews(updated);
        setNewForm({ name: '', role: '', start: '09:00', end: '10:00' });
        setShowAdd(false);
        toast.success("Interview slot added. Optimize schedule to verify conflict resolution!");
      } else {
        toast.error("Failed to save interview slot to server.");
      }
    } catch (err) {
      toast.error("Network error adding interview slot.");
    }
  };

  const parseTimeToFloat = (timeStr) => {
    const [h, m] = timeStr.split(':').map(Number);
    return h + m / 60;
  };

  const runGreedyOptimization = async () => {
    if (interviews.length === 0) {
      toast.error("No interview slots to optimize.");
      return;
    }
    setOptimizing(true);
    try {
      const payload = interviews.map(iv => ({
        id: iv.id,
        name: iv.name,
        role: iv.role,
        start_time: parseTimeToFloat(iv.start),
        end_time: parseTimeToFloat(iv.end)
      }));

      const res = await apiFetch(`${API}/candidates/schedule`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ candidates: payload })
      });

      if (!res.ok) throw new Error("Backend optimization failed.");
      const result = await res.json();
      
      const selectedIds = new Set(result.selected_interviews.map(c => c.id));
      const updated = interviews.map(iv => ({
        ...iv,
        status: selectedIds.has(iv.id) ? 'confirmed' : 'conflict'
      }));

      // Update optimized statuses in the database
      await Promise.all(
        updated.map(iv =>
          apiFetch(`${API}/candidates/interviews/${iv.id}`, {
            method: 'PATCH',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ status: iv.status })
          }).catch(err => console.error('Failed to update interview optimized status:', iv.id, err))
        )
      );

      saveInterviews(updated);
      toast.success(`Schedule optimized: ${result.total_slots} slots confirmed!`);
    } catch (err) {
      console.warn("Backend offline or error:", err);
      toast.error("Something went wrong. Running local scheduler.");
      
      const sorted = [...interviews].map(iv => ({
        ...iv,
        start_time: parseTimeToFloat(iv.start),
        end_time: parseTimeToFloat(iv.end)
      })).sort((a, b) => a.end_time - b.end_time);

      const selectedIds = [];
      let lastEnd = -1;
      for (const iv of sorted) {
        if (iv.start_time >= lastEnd) {
          selectedIds.push(iv.id);
          lastEnd = iv.end_time;
        }
      }

      const updated = interviews.map(iv => ({
        ...iv,
        status: selectedIds.includes(iv.id) ? 'confirmed' : 'conflict'
      }));

      // Update optimized statuses in the database for fallback path
      await Promise.all(
        updated.map(iv =>
          apiFetch(`${API}/candidates/interviews/${iv.id}`, {
            method: 'PATCH',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ status: iv.status })
          }).catch(err => console.error('Failed to update interview optimized status fallback:', iv.id, err))
        )
      );

      saveInterviews(updated);
    } finally {
      setOptimizing(false);
    }
  };

  const statusBadge = (s) => {
    if (s === 'confirmed') return 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/20';
    if (s === 'rescheduled') return 'bg-amber-500/10 text-amber-400 border border-amber-500/20';
    if (s === 'conflict') return 'bg-rose-500/10 text-rose-400 border border-rose-500/20';
    return 'bg-gray-500/10 text-gray-400 border border-gray-500/20';
  };

  return (
    <div className="space-y-4">
      {/* Scrollable List of Interviews */}
      <div className="space-y-2 max-h-60 overflow-y-auto pr-1">
        {interviews.length === 0 ? (
          <div className="text-center py-6 text-theme-3 text-xs">
            No interview slots added yet.
          </div>
        ) : (
          interviews.map(iv => (
            <div key={iv.id} className="bg-white/[0.03] dark:bg-white/[0.02] border border-white/5 backdrop-blur-md rounded-xl p-3">
              {editingId === iv.id ? (
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
                    <button onClick={cancelEdit} className="p-1.5 rounded-lg bg-red-500/10 text-rose-400 hover:bg-red-500/20 transition-all"><X size={13} /></button>
                  </div>
                </div>
              ) : (
                <div className="flex items-center justify-between gap-2">
                  <div className="flex-1 min-w-0">
                    <p className="text-theme-1 text-sm font-medium truncate">{iv.name}</p>
                    <p className="text-theme-3 text-xs">{iv.role}</p>
                  </div>
                  <div className="flex items-center gap-2 flex-shrink-0">
                    <span className="text-theme-2 text-xs font-mono bg-black/20 px-2 py-0.5 rounded border border-white/5">{iv.start} – {iv.end}</span>
                    <span className={`text-xs px-2.5 py-0.5 rounded-full font-medium ${statusBadge(iv.status)}`}>
                      {iv.status}
                    </span>
                    <button onClick={() => startEdit(iv)}
                      className="p-1.5 rounded-lg text-gray-400 hover:text-emerald-400 hover:bg-emerald-500/10 transition-all"
                      title="Reschedule">
                      <Clock size={13} />
                    </button>
                    <button onClick={() => removeInterview(iv.id)}
                      className="p-1.5 rounded-lg text-gray-400 hover:text-rose-400 hover:bg-rose-500/10 transition-all"
                      title="Remove">
                      <Trash2 size={13} />
                    </button>
                  </div>
                </div>
              )}
            </div>
          ))
        )}
      </div>

      {/* Add new interview */}
      {showAdd ? (
        <div className="bg-white/[0.03] dark:bg-white/[0.02] border border-white/5 backdrop-blur-md rounded-xl p-3 space-y-2">
          <div className="grid grid-cols-2 gap-2">
            <div className="relative">
              <input 
                placeholder="Candidate name" 
                value={newForm.name}
                list="dashboard-candidates-list"
                onChange={e => {
                  const val = e.target.value;
                  const cand = candidates.find(c => c.name === val);
                  setNewForm(f => ({ 
                    ...f, 
                    name: val,
                    role: cand ? cand.role : f.role
                  }));
                }}
                className="w-full rounded-lg border border-black/10 dark:border-white/10 bg-card px-2 py-1.5 text-theme-1 text-xs outline-none focus:border-emerald-500/40" 
              />
              <datalist id="dashboard-candidates-list">
                {candidates.map(c => <option key={c.id} value={c.name} />)}
              </datalist>
            </div>
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
            <button onClick={addInterview} className="flex-1 py-1.5 rounded-lg bg-emerald-600 hover:bg-emerald-700 text-white text-xs font-semibold transition-all">Add Slot</button>
            <button onClick={() => setShowAdd(false)} className="flex-1 py-1.5 rounded-lg border border-black/10 dark:border-white/10 text-theme-2 text-xs hover:bg-black/5 dark:hover:bg-white/5 transition-all">Cancel</button>
          </div>
        </div>
      ) : (
        <button onClick={() => setShowAdd(true)}
          className="w-full py-2.5 rounded-xl border border-dashed border-emerald-500/30 text-emerald-500 text-xs hover:bg-emerald-500/5 transition-all flex items-center justify-center gap-1.5">
          <Plus size={13} /> Add Interview Slot
        </button>
      )}

      {/* Optimise Button */}
      <button 
        onClick={runGreedyOptimization} 
        disabled={optimizing}
        className="w-full py-2.5 rounded-xl bg-emerald-600 hover:bg-emerald-700 text-white text-sm font-semibold transition-all flex items-center justify-center gap-2 active:scale-95 disabled:opacity-50"
      >
        {optimizing ? (
          <>
            <RefreshCw className="h-4 w-4 animate-spin" /> Resolving Scheduling Conflicts...
          </>
        ) : (
          <>
            📅 Optimize Schedule (Greedy Selection)
          </>
        )}
      </button>

      <div className="flex items-center justify-between pt-1 text-[11px] text-theme-3">
        <span>{interviews.length} slots entered</span>
        <span>{interviews.filter(i => i.status === 'confirmed' || i.status === 'rescheduled').length} active optimized slots</span>
      </div>
    </div>
  );
}

// ── Optimal Shortlist Modal ────────────────────────────────
function ShortlistModal({ onClose, onUpdateCount }) {
  const [budget, setBudget]         = useState(20);
  const [pool, setPool]             = useState([]);
  const [loading, setLoading]       = useState(true);
  const [calculating, setCalculating] = useState(false);
  const [result, setResult]         = useState({ selected_candidates: [], total_score: 0, budget_used: 0, budget_remaining: 0 });
  const [showAdd, setShowAdd]       = useState(false);
  const [newName, setNewName]       = useState('');
  const [newScore, setNewScore]     = useState('');
  const [newCost, setNewCost]       = useState('');

  // 0/1 Knapsack DP local fallback
  const knapsackLocal = (candidates, budget) => {
    const n = candidates.length;
    const dp = Array(n + 1).fill(null).map(() => Array(budget + 1).fill(0));
    for (let i = 1; i <= n; i++) {
      const { score, cost } = candidates[i - 1];
      for (let w = 0; w <= budget; w++) {
        dp[i][w] = dp[i - 1][w];
        if (w >= cost) dp[i][w] = Math.max(dp[i][w], dp[i - 1][w - cost] + score);
      }
    }
    const selected = [];
    let w = budget;
    for (let i = n; i > 0; i--) {
      if (dp[i][w] !== dp[i - 1][w]) {
        selected.push(candidates[i - 1]);
        w -= candidates[i - 1].cost;
      }
    }
    return { selected_candidates: selected, total_score: dp[n][budget], budget_used: budget - w, budget_remaining: w };
  };

  const runKnapsack = async (currentPool, currentBudget) => {
    setCalculating(true);
    try {
      const payload = currentPool.map(c => ({
        id: c.id,
        name: c.name,
        score: c.score,
        cost: c.cost
      }));

      const res = await apiFetch(`${API}/candidates/shortlist`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ candidates: payload, budget: currentBudget })
      });

      if (!res.ok) throw new Error("Shortlisting backend request failed.");
      const data = await res.json();
      setResult(data);
      localStorage.setItem('hireiq_shortlist_result', JSON.stringify(data));
      if (onUpdateCount) onUpdateCount(data.selected_candidates.length);
    } catch (err) {
      console.warn("Backend shortlist error:", err);
      const localResult = knapsackLocal(currentPool, currentBudget);
      setResult(localResult);
      localStorage.setItem('hireiq_shortlist_result', JSON.stringify(localResult));
      if (onUpdateCount) onUpdateCount(localResult.selected_candidates.length);
    } finally {
      setCalculating(false);
    }
  };

  useEffect(() => {
    const savedBudget = localStorage.getItem('hireiq_shortlist_budget');
    const initialBudget = savedBudget ? Number(savedBudget) : 20;
    setBudget(initialBudget);

    setLoading(true);
    apiFetch(`${API}/candidates`)
      .then(r => r.ok ? r.json() : [])
      .then(data => {
        let list = data;
        if (list.length === 0) {
          list = ALL_CANDIDATES;
        }

        const mapped = list.map(c => ({
          id: c.id,
          name: c.name,
          score: Math.round(c.final_score || c.score || 0),
          cost: c.cost || Math.max(2, Math.min(25, Math.round(((c.final_score || c.score || 70) / 10) + (c.experience?.length || 2) * 1.5)))
        }));

        setPool(mapped);
        localStorage.setItem('hireiq_shortlist_pool', JSON.stringify(mapped));
        runKnapsack(mapped, initialBudget);
      })
      .catch(() => {
        setPool(ALL_CANDIDATES);
        localStorage.setItem('hireiq_shortlist_pool', JSON.stringify(ALL_CANDIDATES));
        runKnapsack(ALL_CANDIDATES, initialBudget);
      })
      .finally(() => setLoading(false));
  }, []);

  const handleBudgetChange = (val) => {
    const b = Math.max(1, Math.min(100, Number(val)));
    setBudget(b);
    localStorage.setItem('hireiq_shortlist_budget', String(b));
    runKnapsack(pool, b);
  };

  const removeCandidate = (id) => {
    const next = pool.filter(c => c.id !== id);
    setPool(next);
    localStorage.setItem('hireiq_shortlist_pool', JSON.stringify(next));
    runKnapsack(next, budget);
    toast.success("Candidate removed from pool");
  };

  const addCandidate = () => {
    if (!newName || !newScore || !newCost) {
      toast.error("Please fill in candidate details");
      return;
    }
    const newCand = {
      id: Date.now(),
      name: newName,
      score: Number(newScore),
      cost: Number(newCost)
    };
    const next = [...pool, newCand];
    setPool(next);
    localStorage.setItem('hireiq_shortlist_pool', JSON.stringify(next));
    runKnapsack(next, budget);
    setNewName(''); setNewScore(''); setNewCost('');
    setShowAdd(false);
    toast.success("Candidate added & shortlist re-calculated!");
  };

  const isSelected = (id) => result.selected_candidates?.some(c => c.id === id);

  return (
    <div className="space-y-4">
      {/* Budget control */}
      <div className="bg-white/[0.03] dark:bg-white/[0.02] border border-white/5 backdrop-blur-md rounded-xl p-3">
        <div className="flex items-center justify-between mb-2">
          <span className="text-theme-2 text-xs font-medium">Hiring Budget (₹ Lakhs)</span>
          <div className="flex items-center gap-2">
            <button onClick={() => handleBudgetChange(budget - 1)}
              className="w-6 h-6 rounded-md bg-white/5 text-theme-1 text-sm flex items-center justify-center hover:bg-emerald-500/20 transition-all">−</button>
            <div className="flex items-center gap-0.5">
              <span className="text-theme-2 text-sm font-bold">₹</span>
              <input type="number" min="1" max="100" value={budget}
                onChange={e => handleBudgetChange(e.target.value)}
                className="w-14 text-center rounded-lg border border-black/10 dark:border-white/10 bg-card px-1 py-1 text-theme-1 text-sm font-bold outline-none focus:border-emerald-500/40" />
              <span className="text-theme-2 text-sm font-bold">L</span>
            </div>
            <button onClick={() => handleBudgetChange(budget + 1)}
              className="w-6 h-6 rounded-md bg-white/5 text-theme-1 text-sm flex items-center justify-center hover:bg-emerald-500/20 transition-all">+</button>
          </div>
        </div>
        {/* Budget bar */}
        <div className="h-1.5 w-full rounded-full bg-white/5">
          <div className="h-full rounded-full bg-gradient-to-r from-emerald-400 to-cyan-400 transition-all duration-300"
            style={{ width: `${Math.min(100, ((result.budget_used || 0) / budget) * 100)}%` }} />
        </div>
        <div className="flex justify-between text-[11px] text-theme-3 mt-1.5">
          <span>Used: {fmt(result.budget_used || 0)}</span>
          <span>Remaining: {fmt(Math.max(0, budget - (result.budget_used || 0)))}</span>
        </div>
      </div>

      {/* Result summary */}
      <div className="grid grid-cols-3 gap-2 text-center">
        {[
          { label: 'Selected Candidates',    value: result.selected_candidates?.length || 0,              color: 'text-emerald-400' },
          { label: 'Cumulative Score',  value: result.total_score || 0,                   color: 'text-cyan-400' },
          { label: 'Budget Allocation',  value: `${fmt(result.budget_used || 0)} / ${fmt(budget)}`, color: 'text-amber-400' },
        ].map(({ label, value, color }) => (
          <div key={label} className="bg-white/[0.02] border border-white/5 rounded-xl p-2.5 backdrop-blur-sm">
            <p className={`text-base font-bold ${color}`}>{value}</p>
            <p className="text-theme-3 text-[10px] leading-tight mt-0.5">{label}</p>
          </div>
        ))}
      </div>

      {/* Candidate pool */}
      <div className="space-y-1.5 max-h-40 overflow-y-auto pr-1">
        {loading ? (
          <div className="flex items-center justify-center py-8">
            <RefreshCw className="h-5 w-5 text-emerald-400 animate-spin" />
            <span className="text-xs text-theme-3 ml-2">Loading candidates...</span>
          </div>
        ) : pool.length === 0 ? (
          <div className="text-center py-6 text-theme-3 text-xs">No candidates available.</div>
        ) : (
          pool.map(c => {
            const selected = isSelected(c.id);
            return (
              <div key={c.id}
                className={`flex items-center justify-between rounded-lg px-3 py-2 transition-all border ${
                  selected
                    ? 'bg-emerald-500/10 border-emerald-500/20'
                    : 'bg-white/[0.01] border-white/5'
                }`}>
                <div className="flex items-center gap-2 min-w-0">
                  {selected
                    ? <Check size={13} className="text-emerald-400 flex-shrink-0" />
                    : <div className="w-3.5 h-3.5 rounded-full border border-gray-500 flex-shrink-0" />}
                  <span className="text-theme-1 text-xs font-medium truncate">{c.name}</span>
                </div>
                <div className="flex items-center gap-3 flex-shrink-0">
                  <span className="text-theme-2 text-[10px]">Score: <b className="text-theme-1">{c.score}</b></span>
                  <span className="text-theme-2 text-[10px]">CTC: <b className="text-theme-1">{fmt(c.cost)}</b></span>
                  <button onClick={() => removeCandidate(c.id)}
                    className="p-1 rounded text-gray-500 hover:text-rose-400 hover:bg-rose-500/10 transition-all">
                    <Trash2 size={11} />
                  </button>
                </div>
              </div>
            );
          })
        )}
      </div>

      {/* Add candidate */}
      {showAdd ? (
        <div className="bg-white/[0.03] dark:bg-white/[0.02] border border-white/5 backdrop-blur-md rounded-xl p-3 space-y-2">
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
            <button onClick={addCandidate} className="flex-1 py-1.5 rounded-lg bg-emerald-600 hover:bg-emerald-700 text-white text-xs font-semibold transition-all">Add Candidate</button>
            <button onClick={() => setShowAdd(false)} className="flex-1 py-1.5 rounded-lg border border-black/10 dark:border-white/10 text-theme-2 text-xs hover:bg-black/5 dark:hover:bg-white/5 transition-all">Cancel</button>
          </div>
        </div>
      ) : (
        <button onClick={() => setShowAdd(true)}
          className="w-full py-2 rounded-xl border border-dashed border-emerald-500/30 text-emerald-500 text-xs hover:bg-emerald-500/5 transition-all flex items-center justify-center gap-1.5">
          <Plus size={13} /> Add Candidate to Pool
        </button>
      )}

      {/* Recalculate */}
      <button 
        onClick={() => runKnapsack(pool, budget)} 
        disabled={calculating}
        className="w-full py-2.5 rounded-xl border border-white/5 text-theme-2 text-xs bg-white/5 hover:bg-white/10 transition-all flex items-center justify-center gap-1.5 disabled:opacity-50"
      >
        <RefreshCw size={12} className={calculating ? "animate-spin" : ""} /> Recalculate Shortlist
      </button>

      <button onClick={onClose} className="w-full py-2.5 rounded-xl bg-emerald-600 hover:bg-emerald-700 text-white text-sm font-semibold transition-all active:scale-95">
        Close
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
  const [scheduledCount, setScheduledCount] = useState(4);
  const [shortlistCount, setShortlistCount] = useState(3);
  const navigate = useNavigate();

  const refreshDashboardStats = async () => {
    const [jobsResult, analyticsResult, interviewsResult] = await Promise.allSettled([
      apiFetch(`${API}/jobs`).then(r => r.ok ? r.json() : []),
      apiFetch(`${API}/settings/analytics`).then(r => r.ok ? r.json() : {}),
      apiFetch(`${API}/candidates/interviews/all`).then(r => r.ok ? r.json() : []),
    ]);

    if (jobsResult.status === 'fulfilled') {
      const jobsData = jobsResult.value;
      setOpenJobs(Array.isArray(jobsData) ? jobsData.filter(j => j.status === 'Open').length : 0);
    } else {
      setOpenJobs(0);
    }

    if (analyticsResult.status === 'fulfilled') {
      const data = analyticsResult.value || {};
      setAnalytics(data);
      if (data?.total_candidates === 0) {
        localStorage.removeItem('hireiq_interviews');
        localStorage.removeItem('hireiq_shortlist_result');
        localStorage.removeItem('hireiq_shortlist_pool');
        setScheduledCount(0);
        setShortlistCount(0);
      }
    } else {
      setAnalytics({});
    }

    if (interviewsResult.status === 'fulfilled' && Array.isArray(interviewsResult.value)) {
      const active = interviewsResult.value.filter(i => i && (i.status === 'confirmed' || i.status === 'rescheduled')).length;
      setScheduledCount(active);
    } else if (interviewsResult.status === 'rejected') {
      console.error(interviewsResult.reason);
    }
  };

  useEffect(() => {
    refreshDashboardStats();

    // Load shortlist count from localStorage safely
    try {
      const rawShortlist = localStorage.getItem('hireiq_shortlist_result');
      const storedShortlist = rawShortlist ? JSON.parse(rawShortlist) : null;
      if (storedShortlist && Array.isArray(storedShortlist.selected_candidates)) {
        setShortlistCount(storedShortlist.selected_candidates.length);
      } else {
        setShortlistCount(3);
      }
    } catch (e) {
      console.error(e);
      setShortlistCount(3);
    }
  }, []);

  const [seeding, setSeeding] = useState(false);

  // Sub-navigation state
  const [dashboardTab, setDashboardTab] = useState('Overview');

  // Executive Analytics states
  const [execData, setExecData] = useState(null);
  const [execLoading, setExecLoading] = useState(false);

  // Workforce Planning states
  const [workforceData, setWorkforceData] = useState(null);
  const [workforceLoading, setWorkforceLoading] = useState(false);

  // Talent Discovery states
  const [discoveryQuery, setDiscoveryQuery] = useState('');
  const [discoveryResults, setDiscoveryResults] = useState([]);
  const [discoveryLoading, setDiscoveryLoading] = useState(false);
  const [discoveryIsDemo, setDiscoveryIsDemo] = useState(false);

  const fetchExecAnalytics = async () => {
    setExecLoading(true);
    try {
      const res = await apiFetch(`${API}/features/analytics/executive`);
      const data = await res.json();
      if (res.ok) setExecData(data);
    } catch (err) {
      console.error(err);
    } finally {
      setExecLoading(false);
    }
  };

  const fetchWorkforcePlanning = async () => {
    setWorkforceLoading(true);
    try {
      const res = await apiFetch(`${API}/features/analytics/workforce`);
      const data = await res.json();
      if (res.ok) setWorkforceData(data);
    } catch (err) {
      console.error(err);
    } finally {
      setWorkforceLoading(false);
    }
  };

  const handleDiscoverySearch = async (query = '') => {
    setDiscoveryLoading(true);
    try {
      const res = await apiFetch(`${API}/features/outreach/discover?query=${encodeURIComponent(query)}`);
      const data = await res.json();
      if (res.ok) {
        setDiscoveryResults(data.results || []);
        setDiscoveryIsDemo(!!data.is_demo_data);
      }
    } catch (err) {
      console.error(err);
    } finally {
      setDiscoveryLoading(false);
    }
  };

  useEffect(() => {
    if (dashboardTab === 'Executive Analytics') {
      fetchExecAnalytics();
    } else if (dashboardTab === 'Workforce Planning') {
      fetchWorkforcePlanning();
    } else if (dashboardTab === 'Talent Discovery & Sourcing') {
      handleDiscoverySearch('');
    }
  }, [dashboardTab]);

  const handleSeedDemo = async () => {
    setSeeding(true);
    try {
      const res = await apiFetch(`${API}/candidates/seed-demo`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' }
      });
      if (!res.ok) throw new Error("Backend seeder failed.");
      toast.success("Successfully seeded 5 high-fidelity candidates! 🎉");
      await refreshDashboardStats();
    } catch (err) {
      console.error(err);
      toast.error("Error seeding workspace demo data.");
    } finally {
      setSeeding(false);
    }
  };

  const openModal = (type) => { setModalType(type); setShowModal(true); };
  const closeModal = () => { setShowModal(false); setModalType(null); };

  const modalTitle = modalType === 'interviews' ? '📅 Interview Schedule' : '🎯 Optimal Shortlist';
  const isLoading = analytics === null;

  return (
    <motion.div initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.2 }}
      className="min-h-screen bg-page px-6 py-8 sm:px-10 lg:py-12">
      <div className="mx-auto max-w-5xl">

        {/* Header */}
        <motion.header initial={{ opacity: 0, y: -20 }} animate={{ opacity: 1, y: 0 }}
          className="mb-6 flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
          <div>
            <h1 className="font-display text-3xl font-bold text-theme-1">Dashboard</h1>
            <p className="text-theme-2 mt-1">Here's what's happening today.</p>
          </div>
          <Link to="/analyze"
            className="inline-flex h-11 items-center justify-center rounded-xl bg-emerald-500 px-5 font-semibold text-white transition-transform hover:scale-105 shadow-glow-mint">
            <Sparkles className="mr-2 h-4 w-4" /> Analyze Candidate
          </Link>
        </motion.header>

        {/* Sub-navigation Tabs */}
        <div className="mb-8 border-b border-white/5 flex gap-1 overflow-x-auto pb-px scrollbar-none">
          {['Overview', 'Executive Analytics', 'Workforce Planning', 'Talent Discovery & Sourcing'].map(tab => (
            <button
              key={tab}
              onClick={() => setDashboardTab(tab)}
              className={`px-4 py-2.5 text-xs font-semibold whitespace-nowrap transition-all border-b-2 -mb-px ${
                dashboardTab === tab
                  ? 'border-emerald-500 text-emerald-400 font-bold'
                  : 'border-transparent text-gray-400 hover:text-white'
              }`}
            >
              {tab}
            </button>
          ))}
        </div>

        {dashboardTab === 'Overview' && (
          <>
            {/* 4 Stat Cards / Skeletons */}
            <div className="grid gap-6 sm:grid-cols-2 lg:grid-cols-4 mb-8">
          {isLoading ? (
            Array(4).fill(0).map((_, idx) => (
              <div key={idx} className="h-32 rounded-2xl border border-black/10 dark:border-white/10 bg-card animate-pulse flex flex-col justify-between p-6">
                <div className="flex justify-between items-center">
                  <div className="h-4 w-24 bg-white/10 rounded" />
                  <div className="h-8 w-8 bg-white/10 rounded-lg" />
                </div>
                <div className="h-8 w-16 bg-white/10 rounded mt-4" />
              </div>
            ))
          ) : (
            <>
              <StatCard title="Total Candidates" value={analytics?.total_candidates ?? 0} icon={<Users className="h-5 w-5" />}    trend={analytics?.recent_uploads_7d ?? 0}  trendLabel="this week" delay={0.1} />
              <StatCard title="Strong Matches"   value={analytics?.strong_matches ?? 0}  icon={<FileSearch className="h-5 w-5" />} trend={analytics?.matches ?? 0}   trendLabel="good matches" delay={0.2} />
              <StatCard title="Avg Match Score"   value={analytics?.average_score ?? 0}   icon={<TrendingUp className="h-5 w-5" />} trend={0}  trendLabel="overall" delay={0.3} />
              <motion.div initial={{ opacity: 0, y: 28 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.4, duration: 0.6 }}
                onClick={() => navigate('/jobs')}
                className="cursor-pointer rounded-2xl border border-black/10 dark:border-white/10 bg-card p-6 hover:border-cyan-500/40 transition-all flex flex-col justify-between">
                <div className="flex items-start justify-between">
                  <p className="text-sm font-medium text-theme-2">Open Positions</p>
                  <div className="rounded-lg bg-cyan-500/10 p-2 text-cyan-400"><Briefcase className="h-5 w-5" /></div>
                </div>
                <div>
                  <p className="font-display text-4xl font-bold text-theme-1 mt-4 tracking-tight">
                    {openJobs === null ? '—' : openJobs}
                  </p>
                  <p className="text-xs text-theme-3 mt-2">Active job listings</p>
                </div>
              </motion.div>
            </>
          )}
        </div>

        {/* Main Workspace Content */}
        {!isLoading && analytics?.total_candidates === 0 ? (
          <motion.div
            initial={{ opacity: 0, scale: 0.98 }}
            animate={{ opacity: 1, scale: 1 }}
            className="rounded-3xl border border-emerald-500/20 bg-emerald-500/5 p-8 text-center max-w-2xl mx-auto space-y-6 mt-6"
          >
            <div className="mx-auto flex h-16 w-16 items-center justify-center rounded-2xl bg-emerald-500/10 text-emerald-400">
              <Sparkles className="h-8 w-8" />
            </div>
            <div className="space-y-2">
              <h2 className="font-display text-2xl font-bold text-white">Welcome to your HireIQ Workspace! 🚀</h2>
              <p className="text-sm text-gray-400 max-w-md mx-auto leading-relaxed">
                Get started by analyzing your candidates' resumes or load a sample recruiter workspace to immediately explore candidate profiles, dynamic skill graphs, and bias audits.
              </p>
            </div>
            <div className="flex flex-col sm:flex-row justify-center gap-4 pt-2">
              {import.meta.env.DEV && (
                <button
                  onClick={handleSeedDemo}
                  disabled={seeding}
                  className="inline-flex h-12 items-center justify-center rounded-xl bg-gradient-to-r from-emerald-500 to-cyan-500 px-8 font-bold text-white shadow-lg shadow-emerald-500/20 hover:scale-[1.02] active:scale-95 transition-all duration-200 disabled:opacity-50"
                >
                  {seeding ? "Loading Demo Workspace..." : "Load Demo Candidates (1-Click)"}
                </button>
              )}
              <Link
                to="/analyze"
                className="inline-flex h-12 items-center justify-center rounded-xl border border-white/10 bg-surface/30 backdrop-blur-md px-8 font-semibold text-white hover:bg-white/5 active:scale-95 transition-all duration-200"
              >
                Upload Candidate Resume
              </Link>
            </div>
          </motion.div>
        ) : (
          <>
            {/* Algorithm Action Cards */}
            <div className="grid gap-6 sm:grid-cols-2 mb-8">
              <motion.button initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.5 }}
                onClick={() => openModal('interviews')}
                className="rounded-2xl border border-black/10 dark:border-white/10 bg-card p-6 hover:border-green-500/40 transition-all cursor-pointer text-left">
                <div className="flex items-start justify-between mb-4">
                  <div>
                    <p className="text-sm font-medium text-theme-2">Interviews Scheduled Today</p>
                    <p className="text-3xl font-bold text-theme-1 mt-2">{scheduledCount}</p>
                    <p className="text-xs text-theme-3 mt-1">Click to view & reschedule</p>
                  </div>
                  <div className="flex h-12 w-12 items-center justify-center rounded-xl bg-green-500/15 text-green-400">
                    <Calendar className="h-6 w-6" />
                  </div>
                </div>
                <div className="h-1 w-full rounded-full bg-black/5 dark:bg-white/5">
                  <div className="h-full rounded-full bg-gradient-to-r from-green-400 to-green-500" style={{ width: `${Math.min(100, (scheduledCount / 6) * 100)}%` }} />
                </div>
              </motion.button>

              <motion.button initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.6 }}
                onClick={() => openModal('shortlist')}
                className="rounded-2xl border border-black/10 dark:border-white/10 bg-card p-6 hover:border-emerald-500/40 transition-all cursor-pointer text-left">
                <div className="flex items-start justify-between mb-4">
                  <div>
                    <p className="text-sm font-medium text-theme-2">Optimal Shortlist Size</p>
                    <p className="text-3xl font-bold text-theme-1 mt-2">{shortlistCount}</p>
                    <p className="text-xs text-theme-3 mt-1">Click to edit budget & candidates</p>
                  </div>
                  <div className="flex h-12 w-12 items-center justify-center rounded-xl bg-emerald-500/15 text-emerald-400">
                    <Target className="h-6 w-6" />
                  </div>
                </div>
                <div className="h-1 w-full rounded-full bg-black/5 dark:bg-white/5">
                  <div className="h-full rounded-full bg-gradient-to-r from-emerald-400 to-emerald-600" style={{ width: `${Math.min(100, (shortlistCount / 5) * 100)}%` }} />
                </div>
              </motion.button>
            </div>

            {/* Analytics Section */}
            <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3 mb-8">
              {/* Hiring Funnel Bar Chart */}
              <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.5 }}
                className="bg-card border border-black/10 dark:border-white/10 rounded-2xl p-6 flex flex-col justify-between h-96">
                <div>
                  <h3 className="text-theme-1 font-semibold text-base">Hiring Funnel</h3>
                  <p className="text-theme-3 text-xs">Candidates by pipeline stage</p>
                </div>
                <div className="h-64 mt-4">
                  <ResponsiveContainer width="100%" height="100%">
                    <BarChart data={analytics?.pipeline_stages || []} margin={{ top: 10, right: 10, left: -25, bottom: 0 }}>
                      <XAxis dataKey="stage" stroke="#6b7280" fontSize={10} tickLine={false} axisLine={false} />
                      <YAxis stroke="#6b7280" fontSize={10} tickLine={false} axisLine={false} allowDecimals={false} />
                      <Tooltip content={<CustomTooltip />} cursor={{ fill: 'rgba(255,255,255,0.05)' }} />
                      <Bar dataKey="count" name="Candidates" fill="url(#funnelGradient)" radius={[4, 4, 0, 0]} />
                      <defs>
                        <linearGradient id="funnelGradient" x1="0" y1="0" x2="0" y2="1">
                          <stop offset="0%" stopColor="#10b981" stopOpacity={0.8} />
                          <stop offset="100%" stopColor="#059669" stopOpacity={0.2} />
                        </linearGradient>
                      </defs>
                    </BarChart>
                  </ResponsiveContainer>
                </div>
              </motion.div>

              {/* Match Score Distribution Bar Chart */}
              <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.6 }}
                className="bg-card border border-black/10 dark:border-white/10 rounded-2xl p-6 flex flex-col justify-between h-96">
                <div>
                  <h3 className="text-theme-1 font-semibold text-base">Score Distribution</h3>
                  <p className="text-theme-3 text-xs">Candidate counts by match score range</p>
                </div>
                <div className="h-64 mt-4">
                  <ResponsiveContainer width="100%" height="100%">
                    <BarChart data={analytics?.score_distribution || []} margin={{ top: 10, right: 10, left: -25, bottom: 0 }}>
                      <XAxis dataKey="range" stroke="#6b7280" fontSize={10} tickLine={false} axisLine={false} />
                      <YAxis stroke="#6b7280" fontSize={10} tickLine={false} axisLine={false} allowDecimals={false} />
                      <Tooltip content={<CustomTooltip />} cursor={{ fill: 'rgba(255,255,255,0.05)' }} />
                      <Bar dataKey="count" name="Candidates" fill="url(#scoreGradient)" radius={[4, 4, 0, 0]} />
                      <defs>
                        <linearGradient id="scoreGradient" x1="0" y1="0" x2="0" y2="1">
                          <stop offset="0%" stopColor="#06b6d4" stopOpacity={0.8} />
                          <stop offset="100%" stopColor="#0891b2" stopOpacity={0.2} />
                        </linearGradient>
                      </defs>
                    </BarChart>
                  </ResponsiveContainer>
                </div>
              </motion.div>

              {/* Education Breakdown Pie Chart */}
              <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.7 }}
                className="bg-card border border-black/10 dark:border-white/10 rounded-2xl p-6 flex flex-col justify-between h-96">
                <div>
                  <h3 className="text-theme-1 font-semibold text-base">Education Tiers</h3>
                  <p className="text-theme-3 text-xs">Breakdown of academic qualifications</p>
                </div>
                <div className="h-52 mt-4 relative flex items-center justify-center">
                  <ResponsiveContainer width="100%" height="100%">
                    <PieChart>
                      <Pie
                        data={analytics?.education_breakdown || []}
                        cx="50%"
                        cy="50%"
                        innerRadius={60}
                        outerRadius={80}
                        paddingAngle={4}
                        dataKey="count"
                        nameKey="tier"
                      >
                        {(analytics?.education_breakdown || []).map((entry, index) => (
                          <Cell key={`cell-${index}`} fill={PIE_COLORS[index % PIE_COLORS.length]} />
                        ))}
                      </Pie>
                      <Tooltip content={<CustomPieTooltip />} />
                    </PieChart>
                  </ResponsiveContainer>
                  {/* Center Text */}
                  <div className="absolute flex flex-col items-center justify-center">
                    <span className="text-theme-3 text-[10px] uppercase tracking-wider font-semibold">Total</span>
                    <span className="text-theme-1 text-2xl font-bold">{analytics?.total_candidates ?? 0}</span>
                  </div>
                </div>
                {/* Custom Legend */}
                <div className="flex flex-wrap justify-center gap-x-4 gap-y-1 mt-2 text-[11px] text-theme-2">
                  {(analytics?.education_breakdown || []).map((entry, index) => (
                    <div key={entry.tier} className="flex items-center gap-1.5 font-medium">
                      <span className="w-2.5 h-2.5 rounded-full" style={{ backgroundColor: PIE_COLORS[index % PIE_COLORS.length] }} />
                      <span>{entry.tier}: {entry.count}</span>
                    </div>
                  ))}
                </div>
              </motion.div>
            </div>

            {/* Recent Analyses */}
            <div className="grid gap-6 lg:grid-cols-2">
              <RecentCandidates />
            </div>
          </>
        )}
      </>
    )}

      {dashboardTab === 'Executive Analytics' && (
        <div className="space-y-8 animate-fadeIn">
          <div className="flex items-center gap-3">
            <h2 className="text-xl font-bold text-white">Executive Analytics</h2>
            {execData?.is_demo_data && (
              <span className="inline-flex items-center gap-1 rounded-full bg-amber-500/10 border border-amber-500/20 px-2.5 py-0.5 text-[10px] font-semibold text-amber-400 uppercase tracking-wide">
                Demo Data
              </span>
            )}
          </div>
          {execLoading || !execData ? (
            <div className="h-64 rounded-2xl bg-white/5 animate-pulse flex flex-col items-center justify-center text-gray-500 text-xs">
              <RefreshCw className="animate-spin mr-2 h-4 w-4" /> Loading Executive Analytics...
            </div>
          ) : (
            <>
              {/* Executive Metrics Cards */}
              <div className="grid gap-6 sm:grid-cols-2 lg:grid-cols-4">
                <StatCard title="Time-to-Hire" value={`${execData.time_to_hire} days`} icon={<Clock className="h-5 w-5" />} trend={-12} trendLabel="vs last month" delay={0.1} />
                <StatCard title="Cost-per-Hire" value={`$${execData.cost_per_hire.toLocaleString()}`} icon={<Target className="h-5 w-5" />} trend={-5} trendLabel="optimized" delay={0.2} />
                <StatCard title="Funnel Conversion" value={`${execData.funnel_conversion}%`} icon={<TrendingUp className="h-5 w-5" />} trend={8} trendLabel="improvement" delay={0.3} />
                <StatCard title="Offer Acceptance" value={`${execData.offer_acceptance}%`} icon={<Users className="h-5 w-5" />} trend={2} trendLabel="positive" delay={0.4} />
              </div>

              <div className="grid gap-6 md:grid-cols-2">
                {/* Funnel Conversion Chart */}
                <div className="bg-card border border-black/10 dark:border-white/10 rounded-2xl p-6 h-96 flex flex-col justify-between">
                  <div>
                    <h3 className="text-white font-semibold text-base">Funnel Stage Yields</h3>
                    <p className="text-gray-500 text-xs">Total applicants surviving at each stage</p>
                  </div>
                  <div className="h-64 mt-4">
                    <ResponsiveContainer width="100%" height="100%">
                      <BarChart data={execData.conversion_stages} margin={{ top: 10, right: 10, left: -25, bottom: 0 }}>
                        <XAxis dataKey="stage" stroke="#6b7280" fontSize={10} tickLine={false} axisLine={false} />
                        <YAxis stroke="#6b7280" fontSize={10} tickLine={false} axisLine={false} />
                        <Tooltip cursor={{ fill: 'rgba(255,255,255,0.05)' }} />
                        <Bar dataKey="count" name="Applicants" fill="#8b5cf6" radius={[4, 4, 0, 0]} />
                      </BarChart>
                    </ResponsiveContainer>
                  </div>
                </div>

                {/* Monthly Hiring Trend */}
                <div className="bg-card border border-black/10 dark:border-white/10 rounded-2xl p-6 h-96 flex flex-col justify-between">
                  <div>
                    <h3 className="text-white font-semibold text-base">Monthly Hires</h3>
                    <p className="text-gray-500 text-xs">Successful additions per month</p>
                  </div>
                  <div className="h-64 mt-4">
                    <ResponsiveContainer width="100%" height="100%">
                      <BarChart data={execData.monthly_hiring} margin={{ top: 10, right: 10, left: -25, bottom: 0 }}>
                        <XAxis dataKey="month" stroke="#6b7280" fontSize={10} tickLine={false} axisLine={false} />
                        <YAxis stroke="#6b7280" fontSize={10} tickLine={false} axisLine={false} />
                        <Tooltip cursor={{ fill: 'rgba(255,255,255,0.05)' }} />
                        <Bar dataKey="hires" name="Hires" fill="#10b981" radius={[4, 4, 0, 0]} />
                      </BarChart>
                    </ResponsiveContainer>
                  </div>
                </div>
              </div>
            </>
          )}
        </div>
      )}

      {dashboardTab === 'Workforce Planning' && (
        <div className="space-y-6 animate-fadeIn">
          <div className="flex items-center gap-3">
            <h2 className="text-xl font-bold text-white">Workforce Planning</h2>
            {workforceData?.is_demo_data && (
              <span className="inline-flex items-center gap-1 rounded-full bg-amber-500/10 border border-amber-500/20 px-2.5 py-0.5 text-[10px] font-semibold text-amber-400 uppercase tracking-wide">
                Demo Data
              </span>
            )}
          </div>
          {workforceLoading || !workforceData ? (
            <div className="h-64 rounded-2xl bg-white/5 animate-pulse flex flex-col items-center justify-center text-gray-500 text-xs">
              <RefreshCw className="animate-spin mr-2 h-4 w-4" /> Loading Workforce Forecasts...
            </div>
          ) : (
            <div className="grid gap-6 md:grid-cols-2">
              {/* Skill Shortage Heatmap */}
              <div className="bg-card border border-black/10 dark:border-white/10 rounded-2xl p-6">
                <h3 className="text-white font-semibold text-base mb-2">Talent Skill Gaps & Shortages</h3>
                <p className="text-gray-500 text-xs mb-6">Percentage deficit in organizational capability across core tech stacks</p>
                <div className="space-y-4">
                  {workforceData.skill_shortages.map(item => (
                    <div key={item.skill} className="bg-white/5 border border-white/5 rounded-xl p-4 space-y-2">
                      <div className="flex justify-between items-center text-xs">
                        <span className="text-white font-semibold">{item.skill}</span>
                        <span className={`px-2 py-0.5 rounded text-[10px] font-bold ${
                          item.status === 'Critical' ? 'bg-red-500/20 text-red-400 border border-red-500/35' :
                          item.status === 'Moderate' ? 'bg-yellow-500/20 text-yellow-400 border border-yellow-500/35' :
                                                       'bg-emerald-500/20 text-emerald-400 border border-emerald-500/35'
                        }`}>{item.status}</span>
                      </div>
                      <div className="flex justify-between items-center text-xs text-gray-400">
                        <span>Deficit Gap</span>
                        <span className="font-bold text-white">{item.gap_percentage}%</span>
                      </div>
                      <div className="w-full bg-white/10 h-1.5 rounded-full overflow-hidden">
                        <div className={`h-full rounded-full ${
                          item.status === 'Critical' ? 'bg-red-500' :
                          item.status === 'Moderate' ? 'bg-yellow-500' : 'bg-emerald-500'
                        }`} style={{ width: `${item.gap_percentage}%` }} />
                      </div>
                    </div>
                  ))}
                </div>
              </div>

              {/* Hiring Demand Forecast */}
              <div className="bg-[#13131f] border border-black/10 dark:border-white/10 rounded-2xl p-6 flex flex-col justify-between h-[450px]">
                <div>
                  <h3 className="text-white font-semibold text-base">Hiring Demand Forecast</h3>
                  <p className="text-gray-500 text-xs">Projected headcounts required to support future product roadmap quarters</p>
                </div>
                <div className="h-72 mt-4">
                  <ResponsiveContainer width="100%" height="100%">
                    <BarChart data={workforceData.demand_forecast} margin={{ top: 10, right: 10, left: -25, bottom: 0 }}>
                      <XAxis dataKey="quarter" stroke="#6b7280" fontSize={10} tickLine={false} axisLine={false} />
                      <YAxis stroke="#6b7280" fontSize={10} tickLine={false} axisLine={false} />
                      <Tooltip cursor={{ fill: 'rgba(255,255,255,0.05)' }} />
                      <Bar dataKey="demand" name="Required Hires" fill="#3b82f6" radius={[4, 4, 0, 0]} />
                    </BarChart>
                  </ResponsiveContainer>
                </div>
              </div>
            </div>
          )}
        </div>
      )}

      {dashboardTab === 'Talent Discovery & Sourcing' && (
        <div className="space-y-6 animate-fadeIn">
          <div className="bg-card border border-black/10 dark:border-white/10 rounded-2xl p-6 space-y-4">
            <div className="flex items-center gap-3">
              <div className="flex items-center gap-3">
              <h3 className="text-white font-semibold text-base">Outreach & Talent Discovery</h3>
              {discoveryIsDemo && (
                <span className="inline-flex items-center gap-1 rounded-full bg-amber-500/10 border border-amber-500/20 px-2.5 py-0.5 text-[10px] font-semibold text-amber-400 uppercase tracking-wide">
                  Demo Data
                </span>
              )}
            </div>
              {discoveryIsDemo && (
                <span className="inline-flex items-center gap-1 rounded-full bg-amber-500/10 border border-amber-500/20 px-2.5 py-0.5 text-[10px] font-semibold text-amber-400 uppercase tracking-wide">
                  Demo Data
                </span>
              )}
            </div>
            <p className="text-gray-500 text-xs">Search and discover public software engineering profiles. Instantly trigger automated recruiter outreach campaigns.</p>
            
            <div className="flex gap-2">
              <input
                type="text"
                placeholder="Search discovered profiles by keyword, headline, or skill (e.g. Python, React)..."
                value={discoveryQuery}
                onChange={e => {
                  setDiscoveryQuery(e.target.value);
                  handleDiscoverySearch(e.target.value);
                }}
                className="flex-1 px-4 py-2.5 bg-white/5 border border-white/10 rounded-xl text-gray-300 text-xs outline-none focus:border-emerald-500/40"
              />
              <button
                onClick={() => handleDiscoverySearch(discoveryQuery)}
                className="px-5 py-2.5 bg-emerald-600 hover:bg-emerald-700 text-white rounded-xl text-xs font-semibold transition-all active:scale-95"
              >
                Search
              </button>
            </div>
          </div>

          <div className="flex justify-between items-center">
            <span className="text-xs text-gray-400 font-semibold">{discoveryResults.length} discovered profiles</span>
            {discoveryResults.length > 0 && (
              <button
                onClick={() => toast.success("Automated outreach sequences queued for all matching profiles! 🚀")}
                className="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white text-xs font-semibold rounded-xl transition-all active:scale-95 shadow-md"
              >
                Bulk Trigger Outreach
              </button>
            )}
          </div>

          <div className="space-y-3">
            {discoveryLoading ? (
              Array(3).fill(0).map((_, i) => (
                <div key={i} className="h-24 rounded-xl border border-white/5 bg-white/5 animate-pulse" />
              ))
            ) : discoveryResults.length === 0 ? (
              <div className="text-center py-12 bg-[#13131f] border border-white/5 rounded-xl text-gray-500 text-xs">
                No profiles discovered yet. Type a query above to search public candidate databases.
              </div>
            ) : discoveryResults.map((profile, idx) => (
              <div key={idx} className="p-4 bg-[#13131f] border border-white/5 rounded-xl flex flex-col sm:flex-row sm:items-center justify-between gap-4">
                <div className="space-y-1 min-w-0">
                  <div className="flex items-center gap-2">
                    <h4 className="text-sm font-bold text-white">{profile.name}</h4>
                    <span className="text-[10px] text-gray-400 font-mono bg-white/5 px-2 py-0.5 rounded">{profile.location}</span>
                  </div>
                  <p className="text-xs text-gray-300 truncate">{profile.headline}</p>
                  <div className="flex flex-wrap gap-1.5 pt-1.5">
                    {profile.skills.map(s => (
                      <span key={s} className="text-[10px] bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 px-2 py-0.5 rounded">
                        {s}
                      </span>
                    ))}
                  </div>
                </div>
                <div className="flex items-center gap-3 flex-shrink-0 self-end sm:self-center">
                  <span className="text-xs text-gray-400">{profile.experience} years exp</span>
                  {profile.github && (
                    <a href={`https://${profile.github}`} target="_blank" rel="noopener noreferrer" className="text-gray-400 hover:text-white">
                      <Github className="h-4 w-4" />
                    </a>
                  )}
                  <button
                    onClick={() => toast.success(`Personalized outreach email drafted and sent to ${profile.name.split(' ')[0]} via Gmail!`)}
                    className="px-3.5 py-1.5 bg-emerald-600/20 hover:bg-emerald-600/35 border border-emerald-500/20 text-emerald-300 rounded-lg text-xs font-semibold transition-all active:scale-95"
                  >
                    Reach Out
                  </button>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>

      {/* Modal */}
      <AnimatePresence>
        {showModal && (
          <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}
            className="fixed inset-0 bg-black/60 backdrop-blur-sm z-50 flex items-center justify-center p-4"
            onClick={closeModal}>
            <motion.div initial={{ scale: 0.95, opacity: 0 }} animate={{ scale: 1, opacity: 1 }} exit={{ scale: 0.95, opacity: 0 }}
              onClick={e => e.stopPropagation()}
              className="bg-card border border-black/10 dark:border-white/10 rounded-2xl p-6 w-full max-w-md max-h-[85vh] overflow-y-auto shadow-2xl relative">
              <div className="flex items-center justify-between mb-5">
                <h3 className="text-theme-1 font-semibold text-lg">{modalTitle}</h3>
                <button onClick={closeModal} className="text-theme-3 hover:text-theme-1 transition-colors"><X size={18} /></button>
              </div>
              {modalType === 'interviews'
                ? <InterviewModal onClose={closeModal} onUpdateCount={setScheduledCount} />
                : <ShortlistModal onClose={closeModal} onUpdateCount={setShortlistCount} />}
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>
    </motion.div>
  );
}
