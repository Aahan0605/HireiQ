import React, { Suspense, lazy } from 'react';
import { BrowserRouter as Router, Routes, Route, Link, useLocation } from 'react-router-dom';
import { Toaster as SonnerToaster } from 'sonner';
import { AuthProvider } from './context/AuthContext';
import ErrorBoundary from './components/ErrorBoundary';
import GrainOverlay from './components/GrainOverlay';

// Eager: entry points and lightweight auth/legal pages that must render instantly.
import Landing from './pages/Landing';
import SignIn from './pages/SignIn';
import ProtectedRoute from './components/ProtectedRoute';

// Lazy: authenticated dashboard pages (pull in recharts and other heavy deps).
// Code-splitting these keeps the landing/marketing bundle lean for first paint.
const DashboardLayout = lazy(() => import('./components/DashboardLayout'));
const Dashboard = lazy(() => import('./pages/Dashboard'));
const Analyze = lazy(() => import('./pages/Analyze'));
const CandidateProfile = lazy(() => import('./pages/CandidateProfile'));
const Candidates = lazy(() => import('./pages/Candidates'));
const Settings = lazy(() => import('./pages/Settings'));
const Jobs = lazy(() => import('./pages/Jobs'));
const JobMatches = lazy(() => import('./pages/JobMatches'));
const BiasReport = lazy(() => import('./pages/BiasReport'));
const CompareView = lazy(() => import('./pages/CompareView'));
const NotFound = lazy(() => import('./pages/NotFound'));
const VerifyEmail = lazy(() => import('./pages/VerifyEmail'));
const ForgotPassword = lazy(() => import('./pages/ForgotPassword'));
const ResetPassword = lazy(() => import('./pages/ResetPassword'));
const AcceptInvite = lazy(() => import('./pages/AcceptInvite'));
const PrivacyPolicy = lazy(() => import('./pages/PrivacyPolicy'));
const TermsOfService = lazy(() => import('./pages/TermsOfService'));

function RouteFallback() {
  return (
    <div className="min-h-screen bg-bg flex items-center justify-center">
      <div className="h-6 w-6 rounded-full border-2 border-emerald-400 border-t-transparent animate-spin" />
    </div>
  );
}


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
      <SonnerToaster theme="dark" closeButton richColors position="top-center" />
      <MarketingNav />
      <Suspense fallback={<RouteFallback />}>
        <Routes>
          <Route path="/"       element={<Landing />} />
          <Route path="/signin" element={<SignIn />} />
          <Route path="/verify-email" element={<VerifyEmail />} />
          <Route path="/forgot-password" element={<ForgotPassword />} />
          <Route path="/reset-password" element={<ResetPassword />} />
          <Route path="/accept-invite" element={<AcceptInvite />} />
          <Route path="/privacy" element={<PrivacyPolicy />} />
          <Route path="/terms" element={<TermsOfService />} />

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
      </Suspense>
    </>
  );
}

export default function App() {
  return (
    <Router future={{ v7_startTransition: true, v7_relativeSplatPath: true }}>
      <AuthProvider>
        <ErrorBoundary>
          <AppRoutes />
        </ErrorBoundary>
      </AuthProvider>
    </Router>
  );
}
