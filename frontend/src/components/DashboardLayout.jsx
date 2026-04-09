import React, { useState, useEffect } from 'react';
import { Outlet, Link, useLocation } from 'react-router-dom';
import { motion, AnimatePresence } from 'framer-motion';
import {
  Menu, X, Sun, Moon,
  LayoutDashboard, FileSearch, Users,
  Briefcase, ShieldAlert, Settings,
  Cpu, FileDown,
} from 'lucide-react';

const navItems = [
  { label: 'Overview',      path: '/dashboard',   icon: LayoutDashboard },
  { label: 'New Analysis',  path: '/analyze',     icon: FileSearch },
  { label: 'Candidates',    path: '/candidates',  icon: Users },
  { label: 'Jobs',          path: '/jobs',        icon: Briefcase },
  { label: 'Bias Report',   path: '/bias-report', icon: ShieldAlert },
  { label: 'Settings',      path: '/settings',    icon: Settings },
];

// Read saved preference, default to dark
function getInitialTheme() {
  if (typeof window === 'undefined') return 'dark';
  return localStorage.getItem('hireiq-theme') || 'dark';
}

export default function DashboardLayout() {
  const location = useLocation();
  const [mobileOpen, setMobileOpen] = useState(false);
  const [theme, setTheme] = useState(getInitialTheme);

  // Apply / remove .dark class on <html> whenever theme changes
  useEffect(() => {
    const root = document.documentElement;
    if (theme === 'dark') {
      root.classList.add('dark');
    } else {
      root.classList.remove('dark');
    }
    localStorage.setItem('hireiq-theme', theme);
  }, [theme]);

  const toggleTheme = () => setTheme(t => t === 'dark' ? 'light' : 'dark');

  const isActive = (path) =>
    location.pathname === path || location.pathname.startsWith(path + '/');

  const isDark = theme === 'dark';

  // Adaptive class helpers
  const sidebarBg  = isDark ? 'bg-card border-white/10' : 'bg-white border-gray-200';
  const linkActive = isDark
    ? 'bg-emerald-500/15 text-emerald-400 font-medium'
    : 'bg-emerald-50 text-emerald-700 font-medium';
  const linkIdle   = isDark
    ? 'text-gray-400 hover:bg-white/5 hover:text-white'
    : 'text-gray-500 hover:bg-gray-100 hover:text-gray-900';
  const pageBg     = 'bg-page';
  const topBarBg   = isDark ? 'bg-[#0d0d1a]/90 border-white/10' : 'bg-white/90 border-gray-200';
  const logoAccent = isDark ? 'text-emerald-400' : 'text-emerald-600';
  const logoText   = isDark ? 'text-white' : 'text-gray-900';
  const toggleBg   = isDark ? 'bg-white/10 hover:bg-white/20 text-yellow-300' : 'bg-gray-100 hover:bg-gray-200 text-gray-600';

  return (
    <div className={`flex h-screen ${pageBg} text-[var(--text-1)] overflow-hidden transition-colors duration-300`}>

      {/* ── Desktop Sidebar ── */}
      <aside className={`hidden md:flex w-60 flex-col border-r ${sidebarBg} px-4 py-6 flex-shrink-0 transition-colors duration-300`}>
        <div className="flex items-center justify-between mb-8 px-2">
          <Link to="/" className={`font-display text-xl font-bold ${logoText}`}>
            Hire<span className={logoAccent}>IQ</span>
          </Link>
          {/* Dark mode toggle */}
          <button onClick={toggleTheme}
            className={`p-1.5 rounded-lg transition-all ${toggleBg}`}
            title={isDark ? 'Switch to light mode' : 'Switch to dark mode'}>
            {isDark ? <Sun className="h-4 w-4" /> : <Moon className="h-4 w-4" />}
          </button>
        </div>

        <nav className="flex flex-col gap-1">
          {navItems.map(({ path, label, icon: Icon }) => (
            <Link key={path} to={path}
              className={`flex items-center gap-3 rounded-lg px-3 py-2.5 text-sm transition-all ${
                isActive(path) ? linkActive : linkIdle
              }`}>
              <Icon className="h-4 w-4 flex-shrink-0" />
              {label}
            </Link>
          ))}
        </nav>
      </aside>

      {/* ── Mobile Top Bar ── */}
      <div className={`md:hidden fixed top-0 left-0 right-0 z-50 flex items-center justify-between border-b ${topBarBg} px-6 py-4 backdrop-blur-md transition-colors duration-300`}>
        <Link to="/" className={`font-display text-xl font-bold ${logoText}`}>
          Hire<span className={logoAccent}>IQ</span>
        </Link>
        <div className="flex items-center gap-3">
          <button onClick={toggleTheme} className={`p-1.5 rounded-lg transition-all ${toggleBg}`}>
            {isDark ? <Sun className="h-4 w-4" /> : <Moon className="h-4 w-4" />}
          </button>
          <button onClick={() => setMobileOpen(!mobileOpen)} className={isDark ? 'text-white' : 'text-gray-700'}>
            {mobileOpen ? <X /> : <Menu />}
          </button>
        </div>
      </div>

      {/* ── Mobile Drawer ── */}
      <AnimatePresence>
        {mobileOpen && (
          <motion.div
            initial={{ opacity: 0, y: -10 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0, y: -10 }}
            className={`md:hidden fixed inset-0 z-40 bg-page pt-20 px-6 transition-colors duration-300`}>
            <nav className="flex flex-col gap-3">
              {navItems.map(({ path, label, icon: Icon }) => (
                <Link key={path} to={path} onClick={() => setMobileOpen(false)}
                  className={`flex items-center gap-3 text-lg font-bold py-2 ${isDark ? 'text-white' : 'text-gray-900'}`}>
                  <Icon className="h-5 w-5" /> {label}
                </Link>
              ))}
            </nav>
          </motion.div>
        )}
      </AnimatePresence>

      {/* ── Page Content ── */}
      <main className="flex-1 overflow-y-auto pt-16 md:pt-0">
        <motion.div key={location.pathname} initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.2 }}>
          <Outlet />
        </motion.div>
      </main>
    </div>
  );
}
