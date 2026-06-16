import React, { useState, useEffect, useRef } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Search, Trash2, Cpu, Loader2, Linkedin, Sparkles, Filter, Grid, List, UserPlus, Check } from 'lucide-react';
import { useNavigate } from 'react-router-dom';
import { toast } from 'sonner';
import { getAllCandidates } from '../data/candidates';
import { apiFetch } from '../lib/apiFetch';
import EmptyState from '../components/EmptyState';

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

const getExperienceYears = (candidate) => {
  if (typeof candidate.experience === 'number') return candidate.experience;
  if (typeof candidate.experience_years === 'number') return candidate.experience_years;
  if (Array.isArray(candidate.experience)) {
    let totalYears = 0;
    candidate.experience.forEach(exp => {
      if (exp.date) {
        const parts = exp.date.split(/[-–to]+/i);
        if (parts.length === 2) {
          const startYear = parseInt(parts[0].trim().match(/\d{4}/)?.[0] || '2024');
          const endStr = parts[1].trim().toLowerCase();
          const endYear = (endStr.includes('present') || endStr.includes('current') || endStr.includes('now'))
            ? new Date().getFullYear()
            : parseInt(endStr.match(/\d{4}/)?.[0] || '2024');
          totalYears += Math.max(1, endYear - startYear);
        } else {
          const match = exp.date.match(/\b\d{4}\b/);
          if (match) totalYears += 1;
        }
      }
    });
    return totalYears || 1;
  }
  return 1;
};

const getEducationTier = (candidate) => {
  const text = `${candidate.summary || ''} ${candidate.role || ''} ${candidate.name || ''}`.toLowerCase();
  if (text.includes('ph.d') || text.includes('phd') || text.includes('doctor of philosophy')) {
    return 'phd';
  }
  if (text.includes('master') || text.includes('mtech') || text.includes('m.s') || text.includes('mba') || text.includes('m.tech')) {
    return 'masters';
  }
  return 'bachelors';
};

const getKanbanStage = (candidate) => {
  const s = candidate.status;
  if (!s) return 'Screening';
  if (['Screening', 'Shortlisted', 'Interviewing', 'Offer', 'Hired', 'Rejected'].includes(s)) {
    return s;
  }
  if (s === 'Strong Match') return 'Shortlisted';
  if (s === 'Match') return 'Screening';
  if (s === 'Failed' || s === 'Rejected') return 'Rejected';
  return 'Screening';
};

const KANBAN_STAGES = [
  { key: 'Screening', label: 'Screening', color: 'border-blue-500/20 bg-blue-500/5' },
  { key: 'Shortlisted', label: 'Shortlisted', color: 'border-yellow-500/20 bg-yellow-500/5' },
  { key: 'Interviewing', label: 'Interviewing', color: 'border-orange-500/20 bg-orange-500/5' },
  { key: 'Offer', label: 'Offer Letter', color: 'border-purple-500/20 bg-purple-500/5' },
  { key: 'Hired', label: 'Hired 🎉', color: 'border-emerald-500/20 bg-emerald-500/5' },
  { key: 'Rejected', label: 'Rejected', color: 'border-red-500/20 bg-red-500/5' },
];

export default function Candidates() {
  const [candidates, setCandidates] = useState([]);
  const [loading, setLoading]       = useState(true);
  const [error, setError]           = useState('');
  const [search, setSearch]         = useState('');
  const [selected, setSelected]     = useState(new Set());
  const [shortlisted, setShortlisted] = useState(new Set()); // top-3 highlight
  const [deltas, setDeltas]         = useState({});          // rank delta badges
  const blindReview = false;
  
  // Advanced filters state
  const [showFilters, setShowFilters] = useState(false);
  const [minScore, setMinScore] = useState(0);
  const [minExp, setMinExp] = useState(0);
  const [educationFilter, setEducationFilter] = useState('All');
  const [selectedSkills, setSelectedSkills] = useState(new Set());
  const [viewMode, setViewMode] = useState('list'); // 'list' | 'kanban'
  const [activePool, setActivePool] = useState('All');
  const [semanticSearch, setSemanticSearch] = useState(false);
  const [showImportModal, setShowImportModal] = useState(false);
  const [showExportDropdown, setShowExportDropdown] = useState(false);
  const [linkedinUrl, setLinkedinUrl] = useState('');
  const [importLoading, setImportLoading] = useState(false);

  const navigate = useNavigate();
  const deltaTimer = useRef(null);



  useEffect(() => {
    let isMounted = true;
    let timerId = null;

    const fetchCandidates = () => {
      apiFetch(`${API}/candidates?page=1&limit=200`)
        .then(r => { if (!r.ok) throw new Error(); return r.json(); })
        .then(data => {
          if (!isMounted) return;
          
          let list = null;
          if (Array.isArray(data)) {
            list = data;
          } else if (data && Array.isArray(data.data)) {
            list = data.data;
          }

          if (list) {
            setCandidates(list);
            
            // Check if any candidate is still analyzing
            const isAnyAnalyzing = list.some(c => c.status === 'Analyzing');
            if (isAnyAnalyzing) {
              if (!timerId) {
                timerId = setInterval(fetchCandidates, 3000);
              }
            } else {
              if (timerId) {
                clearInterval(timerId);
                timerId = null;
              }
            }
          } else {
            setCandidates(getAllCandidates());
          }
        })
        .catch(() => { 
          if (!isMounted) return;
          setCandidates(getAllCandidates()); 
          setError('Unable to load candidates. Showing demo data.'); 
          if (timerId) {
            clearInterval(timerId);
            timerId = null;
          }
        })
        .finally(() => {
          if (isMounted) setLoading(false);
        });
    };

    fetchCandidates();

    return () => {
      isMounted = false;
      if (timerId) clearInterval(timerId);
    };
  }, []);

  // Extract all unique skills dynamically
  const allSkills = React.useMemo(() => {
    const skillsSet = new Set();
    candidates.forEach(c => {
      if (Array.isArray(c.skills)) {
        c.skills.forEach(s => skillsSet.add(s));
      }
    });
    return Array.from(skillsSet).sort();
  }, [candidates]);

  const filtered = candidates.filter(c => {
    // Search filter
    const matchesSearch = c?.name?.toLowerCase().includes(search.toLowerCase()) ||
                          c?.role?.toLowerCase().includes(search.toLowerCase()) ||
                          (semanticSearch && (c?.skills || []).some(s => s.toLowerCase().includes(search.toLowerCase())));
    
    // Talent pool filter
    const stage = getKanbanStage(c);
    const score = Math.round(c?.final_score || c?.score || 0);
    const expYears = getExperienceYears(c);
    
    let matchesPool = true;
    if (activePool === 'Inbox') {
      matchesPool = stage === 'Screening';
    } else if (activePool === 'Shortlisted') {
      matchesPool = stage === 'Shortlisted';
    } else if (activePool === 'Interviewing') {
      matchesPool = stage === 'Interviewing';
    } else if (activePool === 'Offer') {
      matchesPool = stage === 'Offer';
    } else if (activePool === 'Hired') {
      matchesPool = stage === 'Hired';
    } else if (activePool === 'Rejected') {
      matchesPool = stage === 'Rejected';
    } else if (activePool === 'Silver Medalists') {
      matchesPool = score >= 80 && stage !== 'Hired';
    } else if (activePool === 'Future Pipeline') {
      matchesPool = score < 80 && expYears >= 3;
    }
    
    const matchesScore = score >= minScore;
    const matchesExp = expYears >= minExp;
    const eduTier = getEducationTier(c);
    const matchesEdu = educationFilter === 'All' || eduTier === educationFilter;
    const matchesSkills = selectedSkills.size === 0 || 
                          (Array.isArray(c.skills) && Array.from(selectedSkills).every(s => c.skills.includes(s)));
                          
    return matchesSearch && matchesPool && matchesScore && matchesExp && matchesEdu && matchesSkills;
  });

  const handleImportLinkedIn = async (e) => {
    e.preventDefault();
    if (!linkedinUrl) return;
    setImportLoading(true);
    try {
      const res = await apiFetch(`${API}/features/linkedin-import`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ linkedin_url: linkedinUrl })
      });
      const data = await res.json();
      if (!res.ok) {
        throw new Error(data.detail || "LinkedIn Import failed.");
      }
      toast.success(`Successfully imported ${data.name} profile from LinkedIn!`);
      setLinkedinUrl('');
      setShowImportModal(false);
      
      const refRes = await apiFetch(`${API}/candidates?page=1&limit=200`);
      if (refRes.ok) {
        const refData = await refRes.json();
        setCandidates(Array.isArray(refData) ? refData : (refData.data || []));
      }
    } catch (err) {
      toast.error(err.message || "Error importing from LinkedIn.");
    } finally {
      setImportLoading(false);
    }
  };

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

  const handleDeleteCandidate = async (id, name) => {
    if (!window.confirm(`Delete candidate "${name}"? This action cannot be undone.`)) return;
    try {
      const res = await apiFetch(`${API}/candidates/${id}`, {
        method: 'DELETE',
      });
      if (!res.ok) throw new Error('Delete failed');
      toast.success(`Candidate "${name}" deleted.`);
      setCandidates(prev => prev.filter(c => c.id !== id));
      setSelected(prev => {
        const next = new Set(prev);
        next.delete(id);
        return next;
      });
      // Also remove from localStorage dynamically to maintain consistency if offline
      const STORAGE_KEY = 'hireiq_dynamic_candidates';
      const stored = JSON.parse(localStorage.getItem(STORAGE_KEY) || '[]');
      localStorage.setItem(STORAGE_KEY, JSON.stringify(stored.filter(c => c.id !== id)));
    } catch (err) {
      toast.error(`Failed to delete candidate: ${err.message}`);
    }
  };

  const handleExportCSV = async () => {
    if (filtered.length === 0) {
      toast.error('No candidates to export');
      return;
    }
    try {
      const response = await apiFetch(`${API}/reports/candidates/csv`);
      if (!response.ok) throw new Error('Failed to export CSV');
      const blob = await response.blob();
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = 'HireIQ_Candidates_Report.csv';
      document.body.appendChild(a);
      a.click();
      a.remove();
      window.URL.revokeObjectURL(url);
      toast.success('ATS CSV Export successful!');
    } catch (err) {
      toast.error(err.message || 'Error exporting CSV');
    }
  };

  const handleImportFileChange = async (e) => {
    const files = e.target.files;
    if (!files || files.length === 0) return;

    setLoading(true);
    const fileList = Array.from(files);
    
    // Split into CSVs and PDF/Word Resumes
    const csvFiles = fileList.filter(f => f.name.toLowerCase().endsWith('.csv'));
    const resumeFiles = fileList.filter(f => {
      const ext = f.name.substring(f.name.lastIndexOf('.')).toLowerCase();
      return ['.pdf', '.doc', '.docx'].includes(ext);
    });

    const unsupportedFiles = fileList.filter(f => {
      const ext = f.name.substring(f.name.lastIndexOf('.')).toLowerCase();
      return !['.csv', '.pdf', '.doc', '.docx'].includes(ext);
    });

    if (unsupportedFiles.length > 0) {
      toast.error(`Unsupported files ignored: ${unsupportedFiles.map(f => f.name).join(', ')}`);
    }

    try {
      // 1. Process CSVs
      for (const csvFile of csvFiles) {
        const formData = new FormData();
        formData.append('file', csvFile);
        const response = await apiFetch(`${API}/candidates/upload-csv`, {
          method: 'POST',
          body: formData,
        });
        if (!response.ok) throw new Error(`Failed to upload CSV: ${csvFile.name}`);
        const data = await response.json();
        toast.success(data.message || `${csvFile.name} imported successfully!`);
      }

      // 2. Process Resumes
      if (resumeFiles.length > 0) {
        let successCount = 0;
        let failCount = 0;
        for (const resumeFile of resumeFiles) {
          const formData = new FormData();
          formData.append('file', resumeFile);
          const response = await apiFetch(`${API}/candidates/upload-resume`, {
            method: 'POST',
            body: formData,
          });
          if (response.ok) {
            successCount++;
          } else {
            failCount++;
          }
        }
        if (successCount > 0) {
          toast.success(`Successfully uploaded ${successCount} resume(s) for analysis!`);
        }
        if (failCount > 0) {
          toast.error(`Failed to upload ${failCount} resume(s).`);
        }
      }
      
      // Refresh candidates list
      const r = await apiFetch(`${API}/candidates`);
      const data = await r.json();
      setCandidates(Array.isArray(data) ? data : getAllCandidates());

    } catch (err) {
      toast.error(err.message || 'Error importing candidates');
    } finally {
      setLoading(false);
      e.target.value = null; // reset input
    }
  };

  const handleExport = async () => {
    if (filtered.length === 0) {
      toast.error('No candidates to export');
      return;
    }
    try {
      const response = await apiFetch(`${API}/reports/candidates/pdf`);
      if (!response.ok) throw new Error('Failed to export PDF');
      const blob = await response.blob();
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = 'HireIQ_Candidates_Report.pdf';
      document.body.appendChild(a);
      a.click();
      a.remove();
      window.URL.revokeObjectURL(url);
      toast.success('ATS PDF Export successful!');
    } catch (err) {
      toast.error(err.message || 'Error exporting PDF');
    }
  };

  const handleUpdateStage = async (id, stageKey) => {
    // 1. Update in local memory state
    setCandidates(prev => 
      prev.map(c => c.id === id ? { ...c, status: stageKey } : c)
    );

    // 2. Update in localStorage safely
    try {
      const STORAGE_KEY = 'hireiq_dynamic_candidates';
      const raw = localStorage.getItem(STORAGE_KEY);
      const stored = raw ? JSON.parse(raw) : [];
      if (Array.isArray(stored)) {
        const updatedStored = stored.map(c => c.id === id ? { ...c, status: stageKey } : c);
        localStorage.setItem(STORAGE_KEY, JSON.stringify(updatedStored));
      }
    } catch (e) {
      console.error(e);
    }

    // 3. Make PATCH request to backend
    try {
      const res = await apiFetch(`${API}/candidates/${id}`, {
        method: 'PATCH',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({ status: stageKey })
      });
      if (!res.ok) throw new Error('Backend failed to patch candidate stage');
      toast.success('Candidate status updated successfully.');
    } catch (err) {
      console.error(err);
      // Silent fail if backend offline since local/session is updated
    }
  };

  const handleBulkUpdateStage = async (stageKey) => {
    const selectedIds = Array.from(selected);
    // 1. Update local state
    setCandidates(prev => 
      prev.map(c => selectedIds.includes(c.id) ? { ...c, status: stageKey } : c)
    );

    // 2. Update localStorage safely
    try {
      const STORAGE_KEY = 'hireiq_dynamic_candidates';
      const raw = localStorage.getItem(STORAGE_KEY);
      const stored = raw ? JSON.parse(raw) : [];
      if (Array.isArray(stored)) {
        const updatedStored = stored.map(c => selectedIds.includes(c.id) ? { ...c, status: stageKey } : c);
        localStorage.setItem(STORAGE_KEY, JSON.stringify(updatedStored));
      }
    } catch (e) {
      console.error(e);
    }

    toast.loading(`Updating ${selectedIds.length} candidate(s)...`);
    
    // 3. Concurrently patch backend
    try {
      await Promise.all(selectedIds.map(id => 
        apiFetch(`${API}/candidates/${id}`, {
          method: 'PATCH',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ status: stageKey })
        })
      ));
      toast.dismiss();
      toast.success(`Updated ${selectedIds.length} candidate(s) to ${stageKey}.`);
      setSelected(new Set());
    } catch (err) {
      toast.dismiss();
      console.error(err);
    }
  };

  const handleBulkDelete = async () => {
    const selectedIds = Array.from(selected);
    if (!window.confirm(`Delete ${selectedIds.length} selected candidate(s)? This action cannot be undone.`)) return;
    
    setCandidates(prev => prev.filter(c => !selectedIds.includes(c.id)));
    
    try {
      const STORAGE_KEY = 'hireiq_dynamic_candidates';
      const raw = localStorage.getItem(STORAGE_KEY);
      const stored = raw ? JSON.parse(raw) : [];
      if (Array.isArray(stored)) {
        localStorage.setItem(STORAGE_KEY, JSON.stringify(stored.filter(c => !selectedIds.includes(c.id))));
      }
    } catch (e) {
      console.error(e);
    }

    toast.loading(`Deleting ${selectedIds.length} candidate(s)...`);

    try {
      await Promise.all(selectedIds.map(id => 
        apiFetch(`${API}/candidates/${id}`, { method: 'DELETE' })
      ));
      toast.dismiss();
      toast.success(`Successfully deleted ${selectedIds.length} candidate(s).`);
      setSelected(new Set());
    } catch (err) {
      toast.dismiss();
      console.error(err);
      toast.error("Failed to delete candidate(s). Please try again later.");
    }
  };

  return (
    <motion.div initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.2 }}
      className="min-h-screen bg-page p-6 lg:p-10">
      <div className={`${viewMode === 'kanban' ? 'max-w-7xl' : 'max-w-4xl'} mx-auto transition-all duration-300`}>

        {/* Header */}
        <div className="mb-6 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <h1 className="text-3xl font-bold text-white">Candidates</h1>
            <span className="text-xs px-2.5 py-1 rounded-full bg-white/5 text-gray-400 font-medium">
              {filtered.length} candidates
            </span>
          </div>
          <div className="flex gap-2">
            <button onClick={() => setViewMode(viewMode === 'list' ? 'kanban' : 'list')}
              className="px-4 py-2.5 rounded-xl border border-black/10 dark:border-white/10 bg-card text-sm font-medium text-gray-300 hover:border-emerald-500/40 transition-all flex items-center gap-1.5 shadow-md">
              {viewMode === 'list' ? '📋 Kanban View' : '📋 List View'}
            </button>
            <button onClick={() => setShowFilters(!showFilters)}
              className={`px-4 py-2.5 rounded-xl border text-sm font-medium transition-all shadow-md flex items-center gap-1.5 ${
                showFilters 
                  ? 'border-emerald-500/30 bg-emerald-500/10 text-emerald-400' 
                  : 'border-black/10 dark:border-white/10 bg-card text-gray-300 hover:bg-white/5'
              }`}>
              ⚙️ Filters {showFilters ? '▲' : '▼'}
            </button>
          </div>
        </div>

        {/* Talent Pool Tabs */}
        <div className="mb-6 border-b border-white/5 flex gap-1 overflow-x-auto pb-px scrollbar-none">
          {['All', 'Inbox', 'Shortlisted', 'Interviewing', 'Offer', 'Hired', 'Rejected', 'Silver Medalists', 'Future Pipeline'].map(pool => (
            <button
              key={pool}
              onClick={() => setActivePool(pool)}
              className={`px-4 py-2.5 text-xs font-semibold whitespace-nowrap transition-all border-b-2 -mb-px ${
                activePool === pool
                  ? 'border-emerald-500 text-emerald-400 font-bold'
                  : 'border-transparent text-gray-400 hover:text-white'
              }`}
            >
              {pool}
            </button>
          ))}
        </div>

        {error && (
          <div className="mb-4 rounded-xl border border-amber-500/30 bg-amber-500/10 px-4 py-3 text-amber-400 text-sm">
            ⚠️ {error}
          </div>
        )}

        {/* Controls */}
        <div className="mb-5 flex flex-col xl:flex-row gap-3">
          <div className="relative flex-1 flex gap-2">
            <div className="relative flex-1">
              <Search className="absolute left-4 top-1/2 h-4 w-4 -translate-y-1/2 text-gray-500" />
              <input type="text" placeholder="Search by name or role..."
                value={search} onChange={e => setSearch(e.target.value)}
                className="w-full rounded-xl border border-black/10 dark:border-white/10 bg-card py-2.5 pl-11 pr-4 text-theme-1 text-sm outline-none focus:border-emerald-500/40 transition-colors" />
            </div>
            <button
              onClick={() => setSemanticSearch(!semanticSearch)}
              className={`px-4 py-2.5 rounded-xl border text-xs font-bold transition-all flex items-center gap-1.5 whitespace-nowrap ${
                semanticSearch
                  ? 'border-blue-500/50 bg-blue-500/10 text-blue-300 shadow-glow-blue/20'
                  : 'border-white/10 bg-card text-gray-400 hover:text-white'
              }`}
            >
              <Cpu size={14} className={semanticSearch ? 'text-blue-400 animate-pulse' : ''} />
              Semantic AI
            </button>
          </div>
          <div className="flex flex-wrap gap-2 items-center">
            <button onClick={handleSort}
              className="px-4 py-2.5 rounded-xl border border-black/10 dark:border-white/10 bg-card text-sm font-medium text-gray-300 hover:border-emerald-500/40 transition-all">
              ↓ Sort by Score
            </button>
            <button onClick={handleShortlist}
              className="px-4 py-2.5 rounded-xl border border-yellow-500/30 bg-yellow-500/10 text-sm font-medium text-yellow-300 hover:bg-yellow-500/20 transition-all">
              ⭐ Optimal Shortlist
            </button>
          </div>
          <div className="flex flex-wrap items-center gap-3 xl:ml-auto relative">
            <label className={`px-4 py-2.5 rounded-xl border border-blue-500/30 bg-blue-500/10 text-sm font-medium text-blue-300 hover:bg-blue-500/20 transition-all cursor-pointer m-0 flex items-center gap-1.5 ${loading ? 'opacity-50 pointer-events-none' : ''}`}>
              <UserPlus size={15} />
              {loading ? 'Importing...' : 'Import'}
              <input 
                type="file" 
                accept=".csv,.pdf,.doc,.docx" 
                multiple
                className="hidden" 
                onChange={handleImportFileChange} 
                disabled={loading}
              />
            </label>
            <div className="relative">
              <button 
                onClick={() => setShowExportDropdown(!showExportDropdown)}
                className="px-4 py-2.5 rounded-xl border border-purple-500/30 bg-purple-500/10 text-sm font-medium text-purple-300 hover:bg-purple-500/20 transition-all"
              >
                Export
              </button>
              {showExportDropdown && (
                <div className="absolute right-0 mt-2 w-48 rounded-xl border border-white/10 bg-[#13131f] p-2 shadow-2xl z-20">
                  <button 
                    onClick={() => { handleExport(); setShowExportDropdown(false); }} 
                    className="w-full text-left px-3 py-2 text-xs font-semibold text-gray-300 hover:text-white hover:bg-white/5 rounded-lg transition-colors"
                  >
                    📄 Export as PDF
                  </button>
                  <button 
                    onClick={() => { handleExportCSV(); setShowExportDropdown(false); }} 
                    className="w-full text-left px-3 py-2 text-xs font-semibold text-gray-300 hover:text-white hover:bg-white/5 rounded-lg transition-colors"
                  >
                    📊 Export as CSV
                  </button>
                </div>
              )}
            </div>
          </div>
        </div>

        {/* Expandable Advanced Filters Drawer */}
        <AnimatePresence>
          {showFilters && (
            <motion.div 
              initial={{ opacity: 0, height: 0 }}
              animate={{ opacity: 1, height: 'auto' }}
              exit={{ opacity: 0, height: 0 }}
              className="mb-6 p-6 rounded-xl border border-white/10 bg-surface-2/40 backdrop-blur-xl grid grid-cols-1 md:grid-cols-3 gap-6 overflow-hidden"
            >
              <div className="flex flex-col gap-2">
                <label className="text-xs font-semibold text-gray-400 flex justify-between">
                  <span>Min Match Score</span>
                  <span className="text-emerald-400 font-bold">{minScore}%</span>
                </label>
                <input 
                  type="range" min="0" max="100" value={minScore} 
                  onChange={e => setMinScore(Number(e.target.value))} 
                  className="w-full accent-emerald-500 bg-white/10 rounded-lg appearance-none h-1.5 cursor-pointer"
                />
              </div>

              <div className="flex flex-col gap-2">
                <label className="text-xs font-semibold text-gray-400 flex justify-between">
                  <span>Min Experience (Years)</span>
                  <span className="text-emerald-400 font-bold">{minExp}+ yrs</span>
                </label>
                <input 
                  type="range" min="0" max="15" value={minExp} 
                  onChange={e => setMinExp(Number(e.target.value))} 
                  className="w-full accent-emerald-500 bg-white/10 rounded-lg appearance-none h-1.5 cursor-pointer"
                />
              </div>

              <div className="flex flex-col gap-2">
                <label className="text-xs font-semibold text-gray-400">Education Tier</label>
                <select 
                  value={educationFilter} 
                  onChange={e => setEducationFilter(e.target.value)}
                  className="bg-card border border-white/10 rounded-lg px-3 py-2 text-xs text-theme-1 focus:border-emerald-500/50 outline-none"
                >
                  <option value="All">All Degrees</option>
                  <option value="bachelors">Bachelors</option>
                  <option value="masters">Masters</option>
                  <option value="phd">Ph.D.</option>
                </select>
              </div>

              {allSkills.length > 0 && (
                <div className="md:col-span-3 flex flex-col gap-2">
                  <label className="text-xs font-semibold text-gray-400">Filter by Skill Tags</label>
                  <div className="flex flex-wrap gap-1.5 max-h-24 overflow-y-auto pr-2">
                    {allSkills.map(skill => {
                      const isSelected = selectedSkills.has(skill);
                      return (
                        <button
                          key={skill}
                          onClick={() => {
                            const next = new Set(selectedSkills);
                            if (next.has(skill)) {
                              next.delete(skill);
                            } else {
                              next.add(skill);
                            }
                            setSelectedSkills(next);
                          }}
                          className={`text-[10px] px-2.5 py-1 rounded-full border transition-all ${
                            isSelected 
                              ? 'bg-emerald-500/20 text-emerald-300 border-emerald-500/50 shadow-glow-emerald/15' 
                              : 'bg-white/5 text-gray-400 border-white/5 hover:bg-white/10'
                          }`}
                        >
                          {skill}
                        </button>
                      );
                    })}
                  </div>
                  {selectedSkills.size > 0 && (
                    <button 
                      onClick={() => setSelectedSkills(new Set())} 
                      className="text-[10px] text-red-400 hover:text-red-300 text-left mt-1 underline"
                    >
                      Clear selected skills
                    </button>
                  )}
                </div>
              )}
            </motion.div>
          )}
        </AnimatePresence>

        {/* View Mode Switching */}
        {viewMode === 'kanban' ? (
          /* Kanban View */
          <div className="flex flex-col md:flex-row gap-4 overflow-x-auto md:overflow-x-visible pb-6 pt-2 select-none min-h-[520px]">
            {KANBAN_STAGES.map(stage => {
              const stageCandidates = filtered.filter(c => getKanbanStage(c) === stage.key);

              return (
                <div
                  key={stage.key}
                  onDragOver={(e) => e.preventDefault()}
                  onDrop={(e) => {
                    const id = e.dataTransfer.getData('text/plain');
                    handleUpdateStage(id, stage.key);
                  }}
                  className={`flex-shrink-0 w-full md:w-80 rounded-2xl border p-4 flex flex-col gap-3 min-h-[350px] md:min-h-[450px] transition-all ${stage.color}`}
                >
                  {/* Stage Header */}
                  <div className="flex justify-between items-center mb-1">
                    <h3 className="font-semibold text-sm text-white">{stage.label}</h3>
                    <span className="text-[10px] bg-white/5 text-gray-400 px-2 py-0.5 rounded-full font-bold">
                      {stageCandidates.length}
                    </span>
                  </div>

                  {/* Cards container */}
                  <div className="flex-1 flex flex-col gap-2 overflow-y-auto max-h-[500px] pr-1">
                    {stageCandidates.map(c => {
                      const score = Math.round(c?.final_score || c?.score || 0);
                      const displayName = blindReview 
                        ? `Candidate ${c?.id ? c.id.substring(0, 4).toUpperCase() : 'XXXX'}` 
                        : c?.name;

                      return (
                        <div
                          key={c.id}
                          draggable
                          onDragStart={(e) => {
                            e.dataTransfer.setData('text/plain', c.id);
                          }}
                          onClick={() => navigate(`/candidate/${c.id}`)}
                          className="p-4 rounded-xl border border-white/5 bg-[#0e0e1a]/80 hover:border-emerald-500/30 transition-all cursor-grab active:cursor-grabbing flex flex-col gap-3"
                        >
                          <div>
                            <h4 className="text-xs font-bold text-white truncate">{displayName}</h4>
                            <p className="text-[10px] text-gray-400 truncate">{c.role}</p>
                          </div>

                          <div className="flex justify-between items-center mt-1">
                            <span className={`text-[9px] px-2 py-0.5 rounded-full font-semibold ${
                              score >= 85 ? 'bg-green-500/10 text-green-400' :
                              score >= 60 ? 'bg-yellow-500/10 text-yellow-400' :
                                            'bg-red-500/10 text-red-400'
                            }`}>
                              Score: {score}
                            </span>

                            <span className="text-[10px] text-gray-500">{c.location || 'Remote'}</span>
                          </div>
                        </div>
                      );
                    })}

                    {stageCandidates.length === 0 && (
                      <div className="flex-1 border border-dashed border-white/5 rounded-xl flex items-center justify-center py-10 text-center text-gray-600 text-xs">
                        Drag candidates here
                      </div>
                    )}
                  </div>
                </div>
              );
            })}
          </div>
        ) : (
          /* List View */
          <div className="flex flex-col gap-2">
            {loading ? (
              Array(4).fill(0).map((_, i) => (
                <div key={i} className="h-16 rounded-xl border border-black/10 dark:border-white/10 bg-card animate-pulse" />
              ))
            ) : candidates.length === 0 ? (
              <EmptyState 
                icon="FileSearch"
                title="No candidates uploaded yet"
                description="Upload resumes to start ranking, scoring, and analyzing candidate profiles."
                actionLabel="Analyze Resume"
                onAction={() => navigate('/analyze')}
              />
            ) : filtered.length === 0 ? (
              <EmptyState 
                icon="Search"
                title="No matching candidates"
                description="We couldn't find any candidate profiles matching your search or filters. Try adjusting your settings."
              />
            ) : (
              filtered.map(c => {
                const score = Math.round(c?.final_score || c?.score || 0);
                const isSelected    = selected.has(c?.id);
                const isShortlisted = shortlisted.has(c?.id);
                const delta         = deltas[c?.id];

                const displayName = blindReview 
                  ? `Candidate ${c?.id ? c.id.substring(0, 4).toUpperCase() : 'XXXX'}` 
                  : (c?.name || 'Anonymous Candidate');

                const displayInitials = blindReview ? '🕵️' : (c?.name?.split(' ')?.map(n => n[0])?.join('')?.slice(0, 2) || 'C');

                return (
                  <motion.div key={c?.id} layout
                    onClick={() => {
                      if (c?.status !== 'Analyzing') {
                        navigate(`/candidate/${c?.id}`);
                      }
                    }}
                    className={`flex flex-col sm:flex-row sm:items-center justify-between p-4 bg-card border rounded-xl hover:border-emerald-500/30 transition-all cursor-pointer gap-4 sm:gap-0 ${
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
                        {displayInitials}
                      </div>
                      <div className="min-w-0">
                        <p className="text-theme-1 text-sm font-semibold truncate">{displayName}</p>
                        <p className="text-gray-400 text-xs truncate">{c?.role}</p>
                      </div>
                    </div>

                    {/* Right */}
                    <div className="flex items-center justify-between sm:justify-end gap-3 border-t border-white/5 sm:border-t-0 pt-3 sm:pt-0">
                      {/* Rank delta badge — fades after 3s */}
                      <AnimatePresence>
                        {delta !== undefined && delta !== 0 && (
                          <motion.span initial={{ opacity: 0, scale: 0.8 }} animate={{ opacity: 1, scale: 1 }} exit={{ opacity: 0 }}
                            className={`text-xs font-bold px-1.5 py-0.5 rounded ${delta > 0 ? 'text-green-400' : 'text-red-400'}`}>
                            {delta > 0 ? `+${delta}` : delta}
                          </motion.span>
                        )}
                      </AnimatePresence>

                      {c?.status === 'Analyzing' ? (
                        <span className="text-xs px-3 py-1 rounded-full font-medium bg-blue-500/20 text-blue-400 animate-pulse flex items-center gap-1.5">
                          <Loader2 className="h-3.5 w-3.5 animate-spin" />
                          Analyzing...
                        </span>
                      ) : (
                        <span className={`text-xs px-3 py-1 rounded-full font-medium ${
                          score >= 85 ? 'bg-green-500/20 text-green-400' :
                          score >= 60 ? 'bg-yellow-500/20 text-yellow-400' :
                                        'bg-red-500/20 text-red-400'
                        }`}>
                          {score >= 85 ? 'Strong Match' : score >= 60 ? 'Match' : 'Weak'}
                        </span>
                      )}

                      <span className="font-bold text-theme-1 text-xl w-10 text-right">
                        {c?.status === 'Analyzing' ? '—' : score}
                      </span>
                      
                      <button 
                        onClick={() => navigate(`/candidate/${c?.id}`)}
                        disabled={c?.status === 'Analyzing'}
                        className="text-xs px-3 py-1.5 rounded-lg bg-emerald-600/20 hover:bg-emerald-600/40 text-emerald-300 transition-all active:scale-95 disabled:opacity-50 disabled:pointer-events-none"
                      >
                        View →
                      </button>
                      <button 
                        onClick={(e) => {
                          e.stopPropagation();
                          handleDeleteCandidate(c?.id, c?.name);
                        }}
                        className="p-1.5 rounded-lg bg-red-500/10 hover:bg-red-500/20 text-red-400 transition-all active:scale-95"
                        title="Delete Candidate"
                      >
                        <Trash2 size={13} />
                      </button>
                    </div>
                  </motion.div>
                );
              })
            )}
          </div>
        )}
      </div>

      {/* Bulk actions floating bar */}
      <AnimatePresence>
        {selected.size > 0 && (
          <motion.div initial={{ y: 80, opacity: 0 }} animate={{ y: 0, opacity: 1 }} exit={{ y: 80, opacity: 0 }}
            className="fixed bottom-6 left-1/2 -translate-x-1/2 z-50 bg-card border border-emerald-500/30 rounded-2xl px-6 py-4 flex flex-col sm:flex-row items-center gap-4 shadow-2xl backdrop-blur-xl">
            <span className="text-white text-xs font-bold whitespace-nowrap bg-emerald-500/10 text-emerald-400 px-3 py-1 rounded-full">
              {selected.size} selected
            </span>
            
            <div className="flex flex-wrap items-center gap-2">
              {/* Move Stage Selector */}
              <select 
                onChange={(e) => {
                  if (e.target.value) {
                    handleBulkUpdateStage(e.target.value);
                    e.target.value = '';
                  }
                }}
                className="bg-[#0e0e1a] border border-white/10 rounded-xl px-3 py-1.5 text-xs text-white outline-none cursor-pointer focus:border-emerald-500/40"
              >
                <option value="">Move Stage...</option>
                {KANBAN_STAGES.map(stage => (
                  <option key={stage.key} value={stage.key}>{stage.label}</option>
                ))}
              </select>

              {/* Compare Button */}
              <button 
                disabled={selected.size < 2}
                onClick={() => navigate(`/compare?ids=${Array.from(selected).join(',')}`)}
                className="bg-emerald-600 hover:bg-emerald-700 disabled:opacity-40 disabled:hover:bg-emerald-600 text-white text-xs font-semibold px-4 py-1.5 rounded-xl transition-all active:scale-95 whitespace-nowrap"
              >
                Compare Now →
              </button>

              {/* Delete Button */}
              <button 
                onClick={handleBulkDelete}
                className="bg-red-500/10 hover:bg-red-500/20 text-red-400 text-xs font-semibold px-4 py-1.5 rounded-xl border border-red-500/20 transition-all active:scale-95 whitespace-nowrap flex items-center gap-1"
              >
                <Trash2 size={12} /> Delete
              </button>

              {/* Clear Button */}
              <button onClick={() => setSelected(new Set())} className="text-gray-400 hover:text-white text-xs px-2 py-1">
                Clear
              </button>
            </div>
          </motion.div>
        )}
      </AnimatePresence>

      {/* LinkedIn Import Modal */}
      <AnimatePresence>
        {showImportModal && (
          <div className="fixed inset-0 z-50 flex items-center justify-center p-6 bg-black/60 backdrop-blur-sm">
            <motion.div initial={{ opacity: 0, scale: 0.95 }} animate={{ opacity: 1, scale: 1 }} exit={{ opacity: 0, scale: 0.95 }}
              className="w-full max-w-md bg-[#131324] border border-white/10 rounded-xl p-6 space-y-4 shadow-2xl"
            >
              <div className="flex items-center gap-2 text-blue-400">
                <Linkedin size={20} />
                <h3 className="text-lg font-bold text-white">Import from LinkedIn</h3>
              </div>
              <p className="text-xs text-gray-400">Enter a public LinkedIn profile URL to instantly scrape, parse, score, and import the candidate details into HireIQ.</p>
              
              <form onSubmit={handleImportLinkedIn} className="space-y-4">
                <div>
                  <label className="block text-xs font-semibold text-gray-400 mb-1">LinkedIn Profile URL</label>
                  <input 
                    type="text" 
                    required
                    value={linkedinUrl}
                    onChange={e => setLinkedinUrl(e.target.value)}
                    placeholder="https://linkedin.com/in/username"
                    className="w-full px-3 py-2 bg-white/5 border border-white/10 rounded-lg text-gray-300 text-xs outline-none focus:border-blue-500/50 transition-colors" 
                  />
                </div>

                <div className="flex justify-end gap-2 pt-2 border-t border-white/5">
                  <button type="button" onClick={() => setShowImportModal(false)} className="px-4 py-2 bg-white/5 hover:bg-white/10 border border-white/10 text-white rounded-lg text-xs font-semibold transition-colors">Cancel</button>
                  <button type="submit" disabled={importLoading} className="px-4 py-2 bg-blue-600 hover:bg-blue-700 disabled:opacity-50 text-white rounded-lg text-xs font-semibold transition-colors flex items-center gap-1.5">
                    {importLoading ? (
                      <>
                        <Loader2 size={13} className="animate-spin" />
                        Importing...
                      </>
                    ) : (
                      'Start Import'
                    )}
                  </button>
                </div>
              </form>
            </motion.div>
          </div>
        )}
      </AnimatePresence>
    </motion.div>
  );
}
