import os

dashboard_layout_code = """import React, { useState } from 'react';
import { Outlet, Link, useLocation } from 'react-router-dom';
import { motion, AnimatePresence } from 'framer-motion';
import { Menu, X, LayoutDashboard, Users, FileSearch as ScanSearch, Settings, ShieldAlert, Briefcase } from 'lucide-react';

const navItems = [
  { label: 'Overview',     path: '/dashboard',   icon: LayoutDashboard },
  { label: 'New Analysis', path: '/analyze',     icon: ScanSearch },
  { label: 'Candidates',   path: '/candidates',  icon: Users },
  { label: 'Jobs',         path: '/jobs',        icon: Briefcase },
  { label: 'Bias Report',  path: '/bias-report', icon: ShieldAlert },
  { label: 'Settings',     path: '/settings',    icon: Settings },
]

export default function DashboardLayout() {
  const location = useLocation();
  const [mobileOpen, setMobileOpen] = useState(false);
  const isActive = (path) => location.pathname.includes(path);

  return (
    <div className="flex h-screen bg-[#0d0d1a] border-white/10 text-white font-sans overflow-hidden">
      {/* Desktop Sidebar */}
      <aside className="hidden md:flex w-64 border-r border-white/10 bg-[#13131f] p-4 shrink-0 flex-col">
         <h1 className="text-xl font-bold bg-clip-text text-transparent bg-gradient-to-r from-purple-400 to-cyan-400 mb-8 px-2">HireIQ</h1>
         <nav className="flex-1 space-y-2">
         {navItems.map((item) => {
            const Icon = item.icon;
            const active = isActive(item.path);
            return (
              <Link key={item.path} to={item.path} 
                className={`flex items-center gap-3 px-3 py-2 text-sm transition-all rounded-lg ${active ? 'bg-white/10 text-white font-medium' : 'text-gray-400 hover:text-white hover:bg-white/5'}`}>
                <Icon size={18} /> {item.label}
              </Link>
            );
          })}
          </nav>
      </aside>

      {/* Mobile Top Bar */}
      <div className="md:hidden fixed top-0 left-0 right-0 z-50 flex items-center justify-between border-b border-white/10 bg-[#0d0d1a]/90 px-6 py-4 backdrop-blur-md">
        <Link to="/" className="font-display text-xl font-bold text-white">Hire<span className="text-violet">IQ</span></Link>
        <button onClick={() => setMobileOpen(!mobileOpen)} className="text-white">
          {mobileOpen ? <X /> : <Menu />}
        </button>
      </div>

      {/* Mobile Menu */}
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
                  className="flex items-center gap-3 text-xl font-bold text-white py-2"
                >
                  <Icon className="h-5 w-5" /> {label}
                </Link>
              ))}
            </nav>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Page Content */}
      <main className="flex-1 overflow-y-auto w-full pt-16 md:pt-0">
        <Outlet />
      </main>
    </div>
  );
}
"""

with open(
    "/Users/aahanajaygajera/Desktop/al&ml/hireiq/frontend/src/components/DashboardLayout.jsx",
    "w",
) as f:
    f.write(dashboard_layout_code)

print("Updates successful")
