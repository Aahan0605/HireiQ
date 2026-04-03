import React from 'react';
import { Routes, Route, Link, useLocation } from 'react-router-dom';
import { AnimatePresence } from 'framer-motion';

import { Toaster } from 'sonner';
import GrainOverlay from './components/GrainOverlay';
import Landing from './pages/Landing';
import SignIn from './pages/SignIn';
import Dashboard from './pages/Dashboard';
import Analyze from './pages/Analyze';
import CandidateProfile from './pages/CandidateProfile';
import Candidates from './pages/Candidates';
import Settings from './pages/Settings';

function Navigation() {
  const location = useLocation();
  // Hide global nav on auth and dashboard routes if desired, but let's just make it adapt or hide on dashboard
  const isDashboard = location.pathname.startsWith('/dashboard') || location.pathname.startsWith('/analyze') || location.pathname.startsWith('/candidate');
  const isAuth = location.pathname === '/signin';

  if (isDashboard || isAuth) return null;

  return (
    <nav className="fixed top-0 z-40 w-full border-b border-border bg-bg/50 backdrop-blur-md">
      <div className="mx-auto flex h-16 max-w-6xl items-center justify-between px-6">
        <Link to="/" className="font-display text-xl font-bold tracking-tight text-white">
          Hire<span className="text-violet">IQ</span>
        </Link>
        <div className="flex items-center gap-6 text-sm font-medium">
          <a href="#features" className="text-text-2 transition-colors hover:text-white hidden sm:block">Features</a>
          <a href="#pricing" className="text-text-2 transition-colors hover:text-white hidden sm:block">Pricing</a>
          <Link to="/signin" className="text-white hover:text-mint transition-colors">Sign In</Link>
        </div>
      </div>
    </nav>
  );
}

export default function App() {
  const location = useLocation();

  return (
    <>
      <GrainOverlay />
      <Toaster position="top-center" richColors />
      <Navigation />
      <AnimatePresence mode="wait">
        <Routes location={location} key={location.pathname}>
          <Route path="/" element={<Landing />} />
          <Route path="/signin" element={<SignIn />} />
          <Route path="/dashboard" element={<Dashboard />} />
          <Route path="/candidates" element={<Candidates />} />
          <Route path="/settings" element={<Settings />} />
          <Route path="/analyze" element={<Analyze />} />
          <Route path="/candidate/:id" element={<CandidateProfile />} />
        </Routes>
      </AnimatePresence>
    </>
  );
}
