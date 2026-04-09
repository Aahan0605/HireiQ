import React, { useState, useEffect, useRef } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Search } from 'lucide-react';
import { useNavigate } from 'react-router-dom';
import { toast } from 'sonner';
import { getAllCandidates } from '../data/candidates';

const API = '/api/v1';

// Client-side merge sort — returns sorted array + rank delta map
function mergeSort(arr) {
  if (arr.length <= 1) return arr;
  const mid = Math.floor(arr.length / 2);
  return merge(mergeSort(arr.slice(0, mid)), mergeSort(arr.slice(mid)));
}
function merge(left, right) {
  const result = [];
  let i = 0, j = 0;
  while (i < left.length && j < right.length) {
    const scoreL = left[i]?.score || left[i]?.final_score || 0;
    const scoreR = right[j]?.score || right[j]?.final_score || 0;
    result.push(scoreL >= scoreR ? left[i++] : right[j++]);
  }
  return [...result, ...left.slice(i), ...right.slice(j)];
}

export default function Candidates() {
  const [candidates, setCandidates] = useState([]);
  const [loading, setLoading]       = useState(true);
  const [error, setError]           = useState('');
  const [search, setSearch]         = useState('');
  const [selected, setSelected]     = useState(new Set());
  const [shortlisted, setShortlisted] = useState(new Set()); // top-3 highlight
  const [deltas, setDeltas]         = useState({});          // rank delta badges
  const navigate = useNavigate();
  const deltaTimer = useRef(null);

  useEffect(() => {
    fetch(`${API}/candidates`)
      .then(r => { if (!r.ok) throw new Error(); return r.json(); })
      .then(data => setCandidates(Array.isArray(data) ? data : getAllCandidates()))
      .catch(() => { setCandidates(getAllCandidates()); setError('Backend offline — showing local data.'); })
      .finally(() => setLoading(false));
  }, []);

  const filtered = candidates.filter(c =>
    c?.name?.toLowerCase().includes(search.toLowerCase()) ||
    c?.role?.toLowerCase().includes(search.toLowerCase())
  );

  // Sort by score using merge sort, compute rank deltas
  const handleSort = () => {
    const before = filtered.map((c, i) => ({ id: c.id, rank: i }));
    const sorted = mergeSort([...filtered]);
    const deltaMap = {};
    sorted.forEach((c, newRank) => {
      const old = before.find(b => b.id === c.id);
      if (old) deltaMap[c.id] = old.rank - newRank; // positive = moved up
    });
    setCandidates(prev => {
      const rest = prev.filter(c => !filtered.find(f => f.id === c.id));
      return [...sorted, ...rest];
    });
    setDeltas(deltaMap);
    clearTimeout(deltaTimer.current);
    deltaTimer.current = setTimeout(() => setDeltas({}), 3000);
  };

  // Highlight top 3 by score
  const handleShortlist = () => {
    const top3 = [...filtered].sort((a, b) => (b.score || 0) - (a.score || 0)).slice(0, 3);
    setShortlisted(new Set(top3.map(c => c.id)));
  };

  const toggleSelect = (id) => {
    const next = new Set(selected);
    next.has(id) ? next.delete(id) : next.add(id);
    setSelected(next);
  };

  const handleFileUpload = async (e) => {
    const file = e.target.files?.[0];
    if (!file) return;

    setLoading(true);
    const formData = new FormData();
    formData.append('file', file);

    try {
      const response = await fetch(`${API}/candidates/upload-csv`, {
        method: 'POST',
        body: formData,
      });
      if (!response.ok) throw new Error('Failed to upload CSV');
      
      const data = await response.json();
      toast.success(data.message || 'CSV imported successfully!');
      
      // Refresh candidates list
      fetch(`${API}/candidates`)
        .then(r => r.json())
        .then(data => setCandidates(Array.isArray(data) ? data : getAllCandidates()))
        .catch(console.error);
        
    } catch (err) {
      toast.error(err.message || 'Error uploading CSV');
    } finally {
      setLoading(false);
      e.target.value = null; // reset input
    }
  };

  const handleExport = () => {
    if (filtered.length === 0) {
      toast.error('No candidates to export');
      return;
    }

    // We use the backend URL directly which provides proper Content-Disposition headers.
    // This is much more reliable for preserving file names and extensions.
    window.location.href = `${API}/reports/candidates/pdf`;
    toast.success('ATS PDF Export started!');
  };

  return (
    <motion.div initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.2 }}
      className="min-h-screen bg-page p-6 lg:p-10">
      <div className="max-w-4xl mx-auto">

        {/* Header */}
        <div className="mb-6 flex items-center gap-3">
          <h1 className="text-3xl font-bold text-white">Candidates</h1>
          <span className="text-xs px-2.5 py-1 rounded-full bg-white/5 text-gray-400 font-medium">
            {filtered.length} candidates
          </span>
        </div>

        {error && (
          <div className="mb-4 rounded-xl border border-amber-500/30 bg-amber-500/10 px-4 py-3 text-amber-400 text-sm">
            ⚠️ {error}
          </div>
        )}

        {/* Controls */}
        <div className="mb-5 flex flex-col sm:flex-row gap-3">
          <div className="relative flex-1">
            <Search className="absolute left-4 top-1/2 h-4 w-4 -translate-y-1/2 text-gray-500" />
            <input type="text" placeholder="Search by name or role..."
              value={search} onChange={e => setSearch(e.target.value)}
              className="w-full rounded-xl border border-black/10 dark:border-white/10 bg-card py-2.5 pl-11 pr-4 text-theme-1 text-sm outline-none focus:border-emerald-500/40 transition-colors" />
          </div>
          <button onClick={handleSort}
            className="px-4 py-2.5 rounded-xl border border-black/10 dark:border-white/10 bg-card text-sm font-medium text-gray-300 hover:border-emerald-500/40 transition-all">
            ↓ Sort by Score
          </button>
          <button onClick={handleShortlist}
            className="px-4 py-2.5 rounded-xl border border-yellow-500/30 bg-yellow-500/10 text-sm font-medium text-yellow-300 hover:bg-yellow-500/20 transition-all">
            ⭐ Optimal Shortlist
          </button>
          <div className="flex items-center gap-3 ml-auto">
            <label className={`px-4 py-2.5 rounded-xl border border-blue-500/30 bg-blue-500/10 text-sm font-medium text-blue-300 hover:bg-blue-500/20 transition-all cursor-pointer m-0 ${loading ? 'opacity-50 pointer-events-none' : ''}`}>
              Import CSV
              <input 
                type="file" 
                accept=".csv" 
                className="hidden" 
                onChange={handleFileUpload} 
                disabled={loading}
              />
            </label>
            <button onClick={handleExport}
              className="px-4 py-2.5 rounded-xl border border-purple-500/30 bg-purple-500/10 text-sm font-medium text-purple-300 hover:bg-purple-500/20 transition-all">
              Export (PDF)
            </button>
          </div>
        </div>

        {/* List */}
        <div className="flex flex-col gap-2">
          {loading ? (
            Array(4).fill(0).map((_, i) => (
              <div key={i} className="h-16 rounded-xl border border-black/10 dark:border-white/10 bg-card animate-pulse" />
            ))
          ) : filtered.length === 0 ? (
            <div className="py-20 text-center">
              <p className="text-4xl mb-3">🔍</p>
              <p className="text-gray-400">No candidates match your search</p>
            </div>
          ) : (
            filtered.map(c => {
              const score = Math.round(c?.final_score || c?.score || 0);
              const isSelected    = selected.has(c?.id);
              const isShortlisted = shortlisted.has(c?.id);
              const delta         = deltas[c?.id];

              return (
                <motion.div key={c?.id} layout
                  className={`flex items-center justify-between p-4 bg-card border rounded-xl hover:border-emerald-500/30 transition-all cursor-pointer ${
                    isShortlisted ? 'ring-2 ring-yellow-400 ring-offset-1 ring-offset-[#0d0d1a] border-yellow-500/30' :
                    isSelected    ? 'border-emerald-500/50 bg-emerald-500/5' : 'border-black/10 dark:border-white/10'
                  }`}>

                  {/* Left */}
                  <div className="flex items-center gap-4">
                    <input type="checkbox" checked={isSelected}
                      onChange={() => toggleSelect(c?.id)}
                      onClick={e => e.stopPropagation()}
                      className="w-4 h-4 accent-emerald-500 cursor-pointer" />
                    <div className="w-10 h-10 rounded-full bg-gradient-to-br from-emerald-500 to-cyan-500 flex items-center justify-center text-theme-1 text-sm font-bold flex-shrink-0">
                      {c?.name?.split(' ')?.map(n => n[0])?.join('')?.slice(0, 2)}
                    </div>
                    <div>
                      <p className="text-theme-1 text-sm font-semibold">{c?.name}</p>
                      <p className="text-gray-400 text-xs">{c?.role}</p>
                    </div>
                  </div>

                  {/* Right */}
                  <div className="flex items-center gap-3">
                    {/* Rank delta badge — fades after 3s */}
                    <AnimatePresence>
                      {delta !== undefined && delta !== 0 && (
                        <motion.span initial={{ opacity: 0, scale: 0.8 }} animate={{ opacity: 1, scale: 1 }} exit={{ opacity: 0 }}
                          className={`text-xs font-bold px-1.5 py-0.5 rounded ${delta > 0 ? 'text-green-400' : 'text-red-400'}`}>
                          {delta > 0 ? `+${delta}` : delta}
                        </motion.span>
                      )}
                    </AnimatePresence>

                    <span className={`text-xs px-3 py-1 rounded-full font-medium hidden sm:inline ${
                      score >= 85 ? 'bg-green-500/20 text-green-400' :
                      score >= 60 ? 'bg-yellow-500/20 text-yellow-400' :
                                    'bg-red-500/20 text-red-400'
                    }`}>
                      {score >= 85 ? 'Strong Match' : score >= 60 ? 'Match' : 'Weak'}
                    </span>
                    <span className="font-bold text-theme-1 text-xl w-10 text-right">{score}</span>
                    <button onClick={() => navigate(`/candidate/${c?.id}`)}
                      className="text-xs px-3 py-1.5 rounded-lg bg-emerald-600/20 hover:bg-emerald-600/40 text-emerald-300 transition-all active:scale-95">
                      View →
                    </button>
                  </div>
                </motion.div>
              );
            })
          )}
        </div>
      </div>

      {/* Compare floating bar — appears when exactly 2 selected */}
      <AnimatePresence>
        {selected.size >= 2 && (
          <motion.div initial={{ y: 80, opacity: 0 }} animate={{ y: 0, opacity: 1 }} exit={{ y: 80, opacity: 0 }}
            className="fixed bottom-6 left-1/2 -translate-x-1/2 z-50 bg-card border border-emerald-500/40 rounded-2xl px-6 py-3 flex items-center gap-4 shadow-2xl">
            <span className="text-theme-1 text-sm">Comparing {selected.size} candidates</span>
            <button onClick={() => navigate(`/compare?ids=${Array.from(selected).join(',')}`)}
              className="bg-emerald-600 hover:bg-emerald-700 text-theme-1 text-sm px-4 py-2 rounded-xl transition-all active:scale-95">
              Compare Now →
            </button>
            <button onClick={() => setSelected(new Set())} className="text-gray-400 hover:text-theme-1 text-sm">✕</button>
          </motion.div>
        )}
      </AnimatePresence>
    </motion.div>
  );
}
