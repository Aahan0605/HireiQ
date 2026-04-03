import React from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Link, useLocation } from 'react-router-dom';
import StatCard from '../components/StatCard';
import RecentCandidates from '../components/RecentCandidates';
import { Menu, X, Users, FileSearch, TrendingUp, Sparkles, Calendar, Target } from 'lucide-react';

export default function Dashboard() {
  const [isMobileMenuOpen, setIsMobileMenuOpen] = React.useState(false);
  const location = useLocation();

  const isActive = (path) => location.pathname === path;

  return (
    <div className="flex min-h-screen bg-bg">
      {/* Sidebar (Desktop) */}
      <aside className="hidden w-64 flex-col border-r border-border bg-surface md:flex px-6 py-8">
        <Link to="/" className="font-display text-2xl font-bold tracking-tight text-white mb-10">
          Hire<span className="text-violet">IQ</span>
        </Link>
        <nav className="flex flex-col gap-2">
          <Link to="/dashboard" className={`rounded-xl px-4 py-2.5 font-medium transition-colors ${isActive('/dashboard') ? 'bg-surface-3 text-white' : 'text-text-2 hover:bg-surface-2 hover:text-white'}`}>Overview</Link>
          <Link to="/analyze" className={`rounded-xl px-4 py-2.5 font-medium transition-colors ${isActive('/analyze') ? 'bg-surface-3 text-white' : 'text-text-2 hover:bg-surface-2 hover:text-white'}`}>New Analysis</Link>
          <Link to="/candidates" className={`rounded-xl px-4 py-2.5 font-medium transition-colors ${isActive('/candidates') ? 'bg-surface-3 text-white' : 'text-text-2 hover:bg-surface-2 hover:text-white'}`}>Candidates</Link>
          <Link to="/settings" className={`rounded-xl px-4 py-2.5 font-medium transition-colors ${isActive('/settings') ? 'bg-surface-3 text-white' : 'text-text-2 hover:bg-surface-2 hover:text-white'}`}>Settings</Link>
        </nav>
      </aside>

      {/* Mobile Nav */}
      <div className="md:hidden fixed top-0 left-0 right-0 z-50 flex items-center justify-between border-b border-border bg-bg/80 px-6 py-4 backdrop-blur-md">
        <Link to="/" className="font-display text-xl font-bold text-white">Hire<span className="text-violet">IQ</span></Link>
        <button onClick={() => setIsMobileMenuOpen(!isMobileMenuOpen)} className="text-white">
          {isMobileMenuOpen ? <X /> : <Menu />}
        </button>
      </div>

      {/* Mobile Menu Overlay */}
      <AnimatePresence>
        {isMobileMenuOpen && (
          <motion.div
            initial={{ opacity: 0, y: -20 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -20 }}
            className="md:hidden fixed inset-0 z-40 bg-bg pt-24 px-6"
          >
            <nav className="flex flex-col gap-4">
              <Link to="/dashboard" onClick={() => setIsMobileMenuOpen(false)} className="text-2xl font-bold text-white">Overview</Link>
              <Link to="/analyze" onClick={() => setIsMobileMenuOpen(false)} className="text-2xl font-bold text-white">New Analysis</Link>
              <Link to="/candidates" onClick={() => setIsMobileMenuOpen(false)} className="text-2xl font-bold text-white">Candidates</Link>
              <Link to="/settings" onClick={() => setIsMobileMenuOpen(false)} className="text-2xl font-bold text-white">Settings</Link>
            </nav>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Main Content */}
      <main className="flex-1 px-6 py-20 md:py-8 sm:px-10 lg:py-12">
        <div className="mx-auto max-w-5xl">
          <motion.header
            initial={{ opacity: 0, y: -20 }}
            animate={{ opacity: 1, y: 0 }}
            className="mb-10 flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between"
          >
            <div>
              <h1 className="font-display text-3xl font-bold text-white">Dashboard</h1>
              <p className="text-text-2 mt-1">Here's what's happening today.</p>
            </div>
            
            <Link to="/analyze" className="inline-flex h-11 items-center justify-center rounded-xl bg-violet px-5 font-semibold text-bg transition-transform hover:scale-105 shadow-glow-violet">
              <Sparkles className="mr-2 h-4 w-4" />
              Analyze Candidate
            </Link>
          </motion.header>

          <div className="grid gap-6 sm:grid-cols-2 lg:grid-cols-3 mb-8">
            <StatCard
              title="Total Candidates analyzed"
              value={1284}
              icon={<Users className="h-5 w-5" />}
              trend={12}
              trendLabel="vs last month"
              delay={0.1}
            />
            <StatCard
              title="Resumes Parsed"
              value={459}
              icon={<FileSearch className="h-5 w-5" />}
              trend={8}
              trendLabel="vs last month"
              delay={0.2}
            />
            <StatCard
              title="Average Match Rate"
              value={78}
              icon={<TrendingUp className="h-5 w-5" />}
              trend={-2}
              trendLabel="vs last month"
              delay={0.3}
            />
          </div>

          {/* Interview & Shortlist Cards */}
          <div className="grid gap-6 sm:grid-cols-2 mb-8">
            {/* Interviews Scheduled Today */}
            <motion.button
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.4, duration: 0.5 }}
              onClick={() => alert('Interview Details: 4 interviews scheduled with zero overlaps')}
              className="rounded-2xl border border-border bg-surface/50 p-6 backdrop-blur-md hover:border-green-500/50 hover:bg-surface/70 transition-all cursor-pointer text-left"
            >
              <div className="flex items-start justify-between mb-4">
                <div>
                  <p className="text-sm font-medium text-text-2">Interviews Scheduled Today</p>
                  <p className="text-3xl font-bold text-white mt-2">4</p>
                  <p className="text-xs text-text-3 mt-2">Click to view details</p>
                </div>
                <div className="flex h-12 w-12 items-center justify-center rounded-xl bg-green-500/15 text-green-400">
                  <Calendar className="h-6 w-6" />
                </div>
              </div>
              <div className="h-1 w-full rounded-full bg-surface-3">
                <div className="h-full w-4/5 rounded-full bg-gradient-to-r from-green-400 to-green-500" />
              </div>
            </motion.button>

            {/* Optimal Shortlist Size */}
            <motion.button
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.5, duration: 0.5 }}
              onClick={() => alert('Shortlist Analysis: 3 candidates selected within optimal budget constraints')}
              className="rounded-2xl border border-border bg-surface/50 p-6 backdrop-blur-md hover:border-purple-500/50 hover:bg-surface/70 transition-all cursor-pointer text-left"
            >
              <div className="flex items-start justify-between mb-4">
                <div>
                  <p className="text-sm font-medium text-text-2">Optimal Shortlist Size</p>
                  <p className="text-3xl font-bold text-white mt-2">3</p>
                  <p className="text-xs text-text-3 mt-2">Click to view details</p>
                </div>
                <div className="flex h-12 w-12 items-center justify-center rounded-xl bg-purple-500/15 text-purple-400">
                  <Target className="h-6 w-6" />
                </div>
              </div>
              <div className="h-1 w-full rounded-full bg-surface-3">
                <div className="h-full w-3/5 rounded-full bg-gradient-to-r from-purple-400 to-violet" />
              </div>
            </motion.button>
          </div>

          <div className="grid gap-6 lg:grid-cols-2">
            <RecentCandidates />
          </div>
        </div>
      </main>
    </div>
  );
}
