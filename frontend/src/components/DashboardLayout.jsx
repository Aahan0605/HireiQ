import React, { useState } from 'react';
import { Outlet, Link, useLocation } from 'react-router-dom';
import { motion, AnimatePresence } from 'framer-motion';
import {
  Menu, X,
  LayoutDashboard, FileSearch, Users,
  Briefcase, ShieldAlert, Settings,
} from 'lucide-react';

// Sidebar order: Overview → New Analysis → Candidates → Jobs → Bias Report → Settings
const navItems = [
  { label: 'Overview',     path: '/dashboard',   icon: LayoutDashboard },
  { label: 'New Analysis', path: '/analyze',     icon: FileSearch },
  { label: 'Candidates',   path: '/candidates',  icon: Users },
  { label: 'Jobs',         path: '/jobs',        icon: Briefcase },
  { label: 'Bias Report',  path: '/bias-report', icon: ShieldAlert },
  { label: 'Settings',     path: '/settings',    icon: Settings },
];

export default function DashboardLayout() {
  const location = useLocation();
  const [mobileOpen, setMobileOpen] = useState(false);

  // Active if exact match or sub-path (e.g. /jobs/1/matches → /jobs active)
  const isActive = (path) =>
    location.pathname === path || location.pathname.startsWith(path + '/');

  return (
    <div className="flex h-screen bg-[#0d0d1a] text-white overflow-hidden">

      {/* ── Desktop Sidebar ── */}
      <aside className="hidden md:flex w-60 flex-col border-r border-white/10 bg-[#13131f] px-4 py-6 flex-shrink-0">
        <Link to="/" className="font-display text-xl font-bold text-white mb-8 px-2">
          Hire<span className="text-violet">IQ</span>
        </Link>
        <nav className="flex flex-col gap-1">
          {navItems.map(({ path, label, icon: Icon }) => (
            <Link
              key={path}
              to={path}
              className={`flex items-center gap-3 rounded-lg px-3 py-2.5 text-sm transition-all ${
                isActive(path)
                  ? 'bg-white/10 text-white font-medium'
                  : 'text-gray-400 hover:text-white hover:bg-white/5'
              }`}
            >
              <Icon className="h-4 w-4 flex-shrink-0" />
              {label}
            </Link>
          ))}
        </nav>
      </aside>

      {/* ── Mobile Top Bar ── */}
      <div className="md:hidden fixed top-0 left-0 right-0 z-50 flex items-center justify-between border-b border-white/10 bg-[#0d0d1a]/90 px-6 py-4 backdrop-blur-md">
        <Link to="/" className="font-display text-xl font-bold text-white">
          Hire<span className="text-violet">IQ</span>
        </Link>
        <button onClick={() => setMobileOpen(!mobileOpen)} className="text-white">
          {mobileOpen ? <X /> : <Menu />}
        </button>
      </div>

      {/* ── Mobile Drawer ── */}
      <AnimatePresence>
        {mobileOpen && (
          <motion.div
            initial={{ opacity: 0, y: -10 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -10 }}
            className="md:hidden fixed inset-0 z-40 bg-[#0d0d1a] pt-20 px-6"
          >
            <nav className="flex flex-col gap-3">
              {navItems.map(({ path, label, icon: Icon }) => (
                <Link
                  key={path}
                  to={path}
                  onClick={() => setMobileOpen(false)}
                  className="flex items-center gap-3 text-lg font-bold text-white py-2"
                >
                  <Icon className="h-5 w-5" /> {label}
                </Link>
              ))}
            </nav>
          </motion.div>
        )}
      </AnimatePresence>

      {/* ── Page Content ── */}
      <main className="flex-1 overflow-y-auto pt-16 md:pt-0">
        <motion.div
          key={location.pathname}
          initial={{ opacity: 0, y: 8 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.2 }}
        >
          <Outlet />
        </motion.div>
      </main>
    </div>
  );
}
