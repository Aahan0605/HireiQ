import React from 'react';
import { BrowserRouter as Router, Routes, Route, Link, useLocation } from 'react-router-dom';
import { Toaster } from 'react-hot-toast';
import { Toaster as SonnerToaster } from 'sonner';
import { AuthProvider } from './context/AuthContext';
import ErrorBoundary from './components/ErrorBoundary';
import GrainOverlay from './components/GrainOverlay';
import AlgorithmLegend from './components/AlgorithmLegend';
import DashboardLayout from './components/DashboardLayout';
import Landing from './pages/Landing';
import SignIn from './pages/SignIn';
import Dashboard from './pages/Dashboard';
import Analyze from './pages/Analyze';
import CandidateProfile from './pages/CandidateProfile';
import Candidates from './pages/Candidates';
import Settings from './pages/Settings';
import Jobs from './pages/Jobs';
import JobMatches from './pages/JobMatches';
import BiasReport from './pages/BiasReport';
import CompareView from './pages/CompareView';
import NotFound from './pages/NotFound';
import ProtectedRoute from './components/ProtectedRoute';
import VerifyEmail from './pages/VerifyEmail';
import ForgotPassword from './pages/ForgotPassword';
import ResetPassword from './pages/ResetPassword';

const DASH_PREFIXES = [
  '/dashboard', '/analyze', '/candidates', '/candidate',
  '/settings', '/jobs', '/bias-report', '/compare',
];

function MarketingNav() {
  const { pathname } = useLocation();
  const hide = DASH_PREFIXES.some(p => pathname.startsWith(p)) || pathname === '/signin' || pathname === '/';
  if (hide) return null;
  return (
    <nav className="fixed top-0 z-40 w-full border-b border-white/10 bg-[#0d0d1a]/80 backdrop-blur-md">
      <div className="mx-auto flex h-16 max-w-6xl items-center justify-between px-6">
        <Link to="/" className="font-display text-xl font-bold text-white">
          Hire<span className="text-violet">IQ</span>
        </Link>
        <div className="flex items-center gap-6 text-sm">
          <a href="#features" className="text-gray-400 hover:text-white transition-colors hidden sm:block">Features</a>
          <a href="#pricing"  className="text-gray-400 hover:text-white transition-colors hidden sm:block">Pricing</a>
          <Link to="/signin" className="text-white hover:text-mint transition-colors">Sign In</Link>
        </div>
      </div>
    </nav>
  );
}

function AppRoutes() {
  return (
    <>
      <GrainOverlay />
      <Toaster position="top-center" reverseOrder={false} toastOptions={{ style: { background: '#131324', color: '#fff', border: '1px solid rgba(255, 255, 255, 0.1)', fontSize: '14px', borderRadius: '12px' } }} />
      <SonnerToaster theme="dark" closeButton richColors position="top-center" />
      <MarketingNav />
      <AlgorithmLegend />
      <Routes>
        <Route path="/"       element={<Landing />} />
        <Route path="/signin" element={<SignIn />} />
        <Route path="/verify-email" element={<VerifyEmail />} />
        <Route path="/forgot-password" element={<ForgotPassword />} />
        <Route path="/reset-password" element={<ResetPassword />} />

        {/* All dashboard pages share the sidebar layout */}
        <Route element={<ProtectedRoute><DashboardLayout /></ProtectedRoute>}>
          <Route path="/dashboard"          element={<Dashboard />} />
          <Route path="/analyze"            element={<Analyze />} />
          <Route path="/candidates"         element={<Candidates />} />
          <Route path="/candidate/:id"      element={<CandidateProfile />} />
          <Route path="/jobs"               element={<Jobs />} />
          <Route path="/jobs/:id/matches"   element={<JobMatches />} />
          <Route path="/bias-report"        element={<BiasReport />} />
          <Route path="/settings"           element={<Settings />} />
          <Route path="/compare"            element={<CompareView />} />
        </Route>
        <Route path="*"                     element={<NotFound />} />
      </Routes>
    </>
  );
}

export default function App() {
  return (
    <Router>
      <AuthProvider>
        <ErrorBoundary>
          <AppRoutes />
        </ErrorBoundary>
      </AuthProvider>
    </Router>
  );
}
