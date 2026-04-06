import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Link, useNavigate } from 'react-router-dom';
import { Users, FileSearch, TrendingUp, Sparkles, Calendar, Target, Briefcase } from 'lucide-react';
import StatCard from '../components/StatCard';
import RecentCandidates from '../components/RecentCandidates';

const API = 'http://localhost:8000/api/v1';

export default function Dashboard() {
  const [showModal, setShowModal] = useState(false);
  const [modalType, setModalType] = useState(null);
  const [openJobs, setOpenJobs]   = useState(null); // null = loading
  const navigate = useNavigate();

  // Fetch open job count for 4th metric card
  useEffect(() => {
    fetch(`${API}/jobs`)
      .then(r => r.ok ? r.json() : [])
      .then(data => setOpenJobs(Array.isArray(data) ? data.filter(j => j.status === 'Open').length : 0))
      .catch(() => setOpenJobs(0));
  }, []);

  const openModal = (type) => { setModalType(type); setShowModal(true); };

  const getModalContent = () => {
    if (modalType === 'interviews') {
      return {
        title: '📅 Interview Schedule',
        content: (
          <div className="font-mono text-xs text-green-400 bg-black/30 rounded-xl p-4 whitespace-pre">
            {`Alice    →  9:00 AM – 10:00 AM\nBob      →  10:00 AM – 11:00 AM\nDiana    →  11:00 AM – 12:00 PM\nFrank    →  12:00 PM – 1:00 PM`}
          </div>
        ),
      };
    }
    if (modalType === 'shortlist') {
      return {
        title: '🎯 Optimal Shortlist',
        content: (
          <div className="font-mono text-xs text-green-400 bg-black/30 rounded-xl p-4 whitespace-pre">
            {`Selected: Diana, Charlie, Bob\nTotal Score: 253\nBudget Used: 6 / 6`}
          </div>
        ),
      };
    }
    return { title: '', content: null };
  };

  const { title, content } = getModalContent();

  return (
    <motion.div initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.2 }}
      className="min-h-screen bg-page px-6 py-8 sm:px-10 lg:py-12">
      <div className="mx-auto max-w-5xl">

        {/* Header */}
        <motion.header initial={{ opacity: 0, y: -20 }} animate={{ opacity: 1, y: 0 }}
          className="mb-10 flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
          <div>
            <h1 className="font-display text-3xl font-bold text-white">Dashboard</h1>
            <p className="text-gray-400 mt-1">Here's what's happening today.</p>
          </div>
          <Link to="/analyze"
            className="inline-flex h-11 items-center justify-center rounded-xl bg-emerald-500 px-5 font-semibold text-bg transition-transform hover:scale-105 shadow-glow-mint">
            <Sparkles className="mr-2 h-4 w-4" /> Analyze Candidate
          </Link>
        </motion.header>

        {/* ── 4 Stat Cards ── */}
        <div className="grid gap-6 sm:grid-cols-2 lg:grid-cols-4 mb-8">
          <StatCard title="Total Candidates" value={1284} icon={<Users className="h-5 w-5" />}    trend={12}  trendLabel="vs last month" delay={0.1} />
          <StatCard title="Resumes Parsed"   value={459}  icon={<FileSearch className="h-5 w-5" />} trend={8}   trendLabel="vs last month" delay={0.2} />
          <StatCard title="Avg Match Rate"   value={78}   icon={<TrendingUp className="h-5 w-5" />} trend={-2}  trendLabel="vs last month" delay={0.3} />

          {/* 4th card — live open positions count */}
          <motion.div
            initial={{ opacity: 0, y: 28 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.4, duration: 0.6 }}
            onClick={() => navigate('/jobs')}
            className="cursor-pointer rounded-2xl border border-black/10 dark:border-white/10 bg-card p-6 hover:border-cyan-500/40 transition-all">
            <div className="flex items-start justify-between">
              <p className="text-sm font-medium text-gray-400">Open Positions</p>
              <div className="rounded-lg bg-cyan-500/10 p-2 text-cyan-400">
                <Briefcase className="h-5 w-5" />
              </div>
            </div>
            <p className="font-display text-4xl font-bold text-white mt-4 tracking-tight">
              {openJobs === null ? '—' : openJobs}
            </p>
            <p className="text-xs text-gray-500 mt-2">Active job listings</p>
          </motion.div>
        </div>

        {/* ── Algorithm Action Cards ── */}
        <div className="grid gap-6 sm:grid-cols-2 mb-8">
          <motion.button initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.5 }}
            onClick={() => openModal('interviews')}
            className="rounded-2xl border border-black/10 dark:border-white/10 bg-card p-6 hover:border-green-500/40 transition-all cursor-pointer text-left">
            <div className="flex items-start justify-between mb-4">
              <div>
                <p className="text-sm font-medium text-gray-400">Interviews Scheduled Today</p>
                <p className="text-3xl font-bold text-white mt-2">4</p>
                <p className="text-xs text-gray-500 mt-1">Click to view schedule</p>
              </div>
              <div className="flex h-12 w-12 items-center justify-center rounded-xl bg-green-500/15 text-green-400">
                <Calendar className="h-6 w-6" />
              </div>
            </div>
            <div className="h-1 w-full rounded-full bg-white/5">
              <div className="h-full w-4/5 rounded-full bg-gradient-to-r from-green-400 to-green-500" />
            </div>
          </motion.button>

          <motion.button initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.6 }}
            onClick={() => openModal('shortlist')}
            className="rounded-2xl border border-black/10 dark:border-white/10 bg-card p-6 hover:border-emerald-500/40 transition-all cursor-pointer text-left">
            <div className="flex items-start justify-between mb-4">
              <div>
                <p className="text-sm font-medium text-gray-400">Optimal Shortlist Size</p>
                <p className="text-3xl font-bold text-white mt-2">3</p>
                <p className="text-xs text-gray-500 mt-1">Click to view shortlist</p>
              </div>
              <div className="flex h-12 w-12 items-center justify-center rounded-xl bg-emerald-500/15 text-emerald-400">
                <Target className="h-6 w-6" />
              </div>
            </div>
            <div className="h-1 w-full rounded-full bg-white/5">
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
            className="fixed inset-0 bg-black/60 backdrop-blur-sm z-50 flex items-center justify-center"
            onClick={() => setShowModal(false)}>
            <motion.div initial={{ scale: 0.95, opacity: 0 }} animate={{ scale: 1, opacity: 1 }} exit={{ scale: 0.95, opacity: 0 }}
              onClick={e => e.stopPropagation()}
              className="bg-card border border-black/10 dark:border-white/10 rounded-2xl p-6 max-w-md w-full mx-4 shadow-2xl">
              <h3 className="text-theme-1 font-semibold text-lg mb-4">{title}</h3>
              <div className="mb-6">{content}</div>
              <button onClick={() => setShowModal(false)}
                className="w-full py-2 rounded-xl bg-emerald-600 hover:bg-emerald-700 text-theme-1 text-sm font-medium transition-all active:scale-95">
                Close
              </button>
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>
    </motion.div>
  );
}
