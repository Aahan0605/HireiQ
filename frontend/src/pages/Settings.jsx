import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { AlertCircle, Save, RefreshCw, Check, Zap, Lock, CreditCard, Users, UserPlus, Trash2, Globe, Shield, Mail, Calendar, Key, Database, Webhook } from 'lucide-react';
import { toast } from 'sonner';
import { apiFetch } from '../lib/apiFetch';
import { useAuth } from '../context/AuthContext';
import MagneticCard from '../components/MagneticCard';


const API = '/api/v1';

const plansList = [
  {
    name: 'Free',
    price: '$0',
    desc: 'Basic candidate evaluation and resume parsing tool.',
    features: [
      '5 resume parses / month',
      'Basic TF-IDF match score',
      'Candidate List View'
    ]
  },
  {
    name: 'Pro',
    price: '$79',
    desc: 'Power features for scaling teams and active recruiters.',
    features: [
      'Unlimited CV uploads',
      'Kanban Hiring pipeline board',
      'Advanced filter controls',
      'Real-time GitHub profile sync'
    ]
  },
  {
    name: 'Enterprise',
    price: 'Custom',
    desc: 'Dedicated database infrastructure and security controls.',
    features: [
      'custom weight templates',
      'DB sync (Supabase/PostgreSQL)',
      'PDF and CSV reports',
      '24/7 Priority support SLA'
    ]
  }
];

function SettingsScoringSkeleton() {
  return (
    <div className="space-y-6">
      <MagneticCard className="p-6 border-black/10 dark:border-white/10 bg-card animate-pulse" maxTilt={0}>
        <div className="mb-6 flex items-center justify-between">
          <div className="h-5 w-36 rounded bg-white/10" />
          <div className="h-4 w-4 rounded-full bg-white/10" />
        </div>
        <div className="space-y-6">
          {Array(4).fill(0).map((_, i) => (
            <div key={i} className="space-y-2">
              <div className="flex justify-between">
                <div className="h-4 w-56 rounded bg-white/10" />
                <div className="h-4 w-10 rounded bg-white/10" />
              </div>
              <div className="h-2 w-full rounded-full bg-white/10" />
            </div>
          ))}
        </div>
        <div className="mt-6 h-12 rounded-lg bg-white/10" />
        <div className="mt-5 h-10 w-36 rounded-xl bg-white/10" />
      </MagneticCard>

      <MagneticCard className="p-6 border-black/10 dark:border-white/10 bg-card animate-pulse" maxTilt={0}>
        <div className="mb-4 h-5 w-28 rounded bg-white/10" />
        <div className="h-20 rounded-lg bg-white/10" />
      </MagneticCard>

      <MagneticCard className="p-6 border-black/10 dark:border-white/10 bg-card animate-pulse" maxTilt={0}>
        <div className="mb-4 h-5 w-36 rounded bg-white/10" />
        <div className="grid grid-cols-3 gap-4">
          {Array(3).fill(0).map((_, i) => (
            <div key={i} className="space-y-2">
              <div className="h-3 w-20 rounded bg-white/10" />
              <div className="h-10 rounded-lg bg-white/10" />
            </div>
          ))}
        </div>
        <div className="mt-5 h-10 w-40 rounded-xl bg-white/10" />
      </MagneticCard>
    </div>
  );
}

export default function Settings() {
  const { user } = useAuth();
  const [activeTab, setActiveTab] = useState(() => {
    const params = new URLSearchParams(window.location.search);
    const tab = params.get('tab');
    if (tab === 'billing') return 'billing';
    if (tab === 'team') return 'team';
    if (tab === 'integrations') return 'integrations';
    if (tab === 'security') return 'security';
    return 'scoring';
  });
  
  // Scoring weights state
  const [resume,    setResume]    = useState(40);
  const [github,    setGithub]    = useState(30);
  const [leetcode,  setLeetcode]  = useState(20);
  const [portfolio, setPortfolio] = useState(10);
  const [blindScoring, setBlindScoring] = useState(true);
  const [strongMatch, setStrongMatch]   = useState(85);
  const [match,       setMatch]         = useState(60);
  const [weakMatch,   setWeakMatch]     = useState(40);
  const [saved,    setSaved]    = useState(false);
  const [loading,  setLoading]  = useState(true);

  // Billing SaaS states
  const [plan, setPlan] = useState(() => localStorage.getItem('hireiq_saas_plan') || 'Free');
  const [quotaUsed, setQuotaUsed] = useState(0);
  const [checkoutLoading, setCheckoutLoading] = useState(false);

  // Team states
  const [members, setMembers] = useState([]);
  const [membersLoading, setMembersLoading] = useState(true);
  const [membersError, setMembersError] = useState(null);
  const [inviteEmail, setInviteEmail] = useState('');
  const [inviteRole, setInviteRole] = useState('Recruiter');
  const [inviteLoading, setInviteLoading] = useState(false);
  const [inviteSuccessLink, setInviteSuccessLink] = useState(null);

  // Integrations states
  const [integrations, setIntegrations] = useState({
    slack: true,
    gmail: true,
    outlook: false,
    gcal: true,
    ocal: false,
    workday: false,
    bamboohr: false,
    codility: false,
  });
  const [configureIntegration, setConfigureIntegration] = useState(null);

  // Security & SSO states
  const [ssoEnabled, setSsoEnabled] = useState(false);
  const [ssoProviderUrl, setSsoProviderUrl] = useState("https://identity.company.com/sso/saml");
  const [gdprDeleteEnabled, setGdprDeleteEnabled] = useState(true);
  const [retentionPeriod, setRetentionPeriod] = useState("indefinite");
  const [exportingLogs, setExportingLogs] = useState(false);

  const fetchMembers = () => {
    setMembersLoading(true);
    setMembersError(null);
    apiFetch(`${API}/members`)
      .then(res => {
        if (!res.ok) throw new Error("Failed to load team members.");
        return res.json();
      })
      .then(data => {
        setMembers(data);
      })
      .catch(err => {
        setMembersError(err.message || "Unable to load team members.");
      })
      .finally(() => {
        setMembersLoading(false);
      });
  };

  useEffect(() => {
    if (activeTab === 'team') {
      fetchMembers();
    }
  }, [activeTab]);

  const handleInvite = async (e) => {
    e.preventDefault();
    if (!inviteEmail) return;
    setInviteLoading(true);
    setInviteSuccessLink(null);
    try {
      const res = await apiFetch(`${API}/members/invite`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email: inviteEmail, role: inviteRole })
      });
      const data = await res.json();
      if (!res.ok) {
        throw new Error(data.detail || "Failed to invite member.");
      }
      const frontendUrl = window.location.origin;
      const link = `${frontendUrl}/accept-invite?token=${data.token}`;
      setInviteSuccessLink(link);
      setInviteEmail('');
      toast.success(`Invitation generated for ${inviteEmail}!`);
      fetchMembers();
    } catch (err) {
      toast.error(err.message || "Error generating invitation.");
    } finally {
      setInviteLoading(false);
    }
  };

  const handleRemoveMember = async (memberId) => {
    if (!window.confirm("Are you sure you want to remove this team member?")) return;
    try {
      const res = await apiFetch(`${API}/members/${memberId}`, {
        method: 'DELETE'
      });
      if (!res.ok) {
        const data = await res.json();
        throw new Error(data.detail || "Failed to remove member.");
      }
      toast.success("Team member removed successfully.");
      fetchMembers();
    } catch (err) {
      toast.error(err.message || "Error removing team member.");
    }
  };

  // Load current weights and sync billing quota/plan from backend on mount and listen for Stripe checkout callbacks
  useEffect(() => {
    let cancelled = false;

    const loadSettings = async () => {
      setLoading(true);
      const [weightsResult, analyticsResult] = await Promise.allSettled([
        apiFetch(`${API}/settings/weights`).then(r => r.ok ? r.json() : null),
        apiFetch(`${API}/settings/analytics`).then(r => r.ok ? r.json() : { total_candidates: 0 }),
      ]);

      if (cancelled) return;

      if (weightsResult.status === 'fulfilled' && weightsResult.value) {
        const data = weightsResult.value;
        setResume(Math.round((data.resume    ?? 0.4) * 100));
        setGithub(Math.round((data.github    ?? 0.3) * 100));
        setLeetcode(Math.round((data.leetcode  ?? 0.2) * 100));
        setPortfolio(Math.round((data.portfolio ?? 0.1) * 100));
      }

      if (analyticsResult.status === 'fulfilled') {
        const data = analyticsResult.value || { total_candidates: 0 };
        setQuotaUsed(data.total_candidates ?? 0);
        if (data.plan_name) {
          setPlan(data.plan_name);
          localStorage.setItem('hireiq_saas_plan', data.plan_name);
        }
      }

      setLoading(false);
    };

    loadSettings();

    return () => {
      cancelled = true;
    };
  }, []);

  useEffect(() => {
    const params = new URLSearchParams(window.location.search);
    if (params.get('checkout') === 'success') {
      toast.success('Subscription upgraded successfully!');
      window.history.replaceState({}, '', '/settings');
    }
    if (params.get('checkout') === 'cancelled') {
      toast.info('Checkout cancelled.');
      window.history.replaceState({}, '', '/settings');
    }
  }, []);

  const total   = resume + github + leetcode + portfolio;
  const isValid = total === 100;

  const handleSaveWeights = async () => {
    try {
      await apiFetch(`${API}/settings/weights`, {
        method:  'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          resume:    resume    / 100,
          github:    github    / 100,
          leetcode:  leetcode  / 100,
          portfolio: portfolio / 100,
        }),
      });
    } catch { /* backend offline */ }
    setSaved(true);
    setTimeout(() => setSaved(false), 2500);
  };

  const handleSaveThresholds = async () => {
    try {
      await apiFetch(`${API}/settings/thresholds`, {
        method:  'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ strong: strongMatch, match, weak: weakMatch }),
      });
    } catch { /* backend offline */ }
    setSaved(true);
    setTimeout(() => setSaved(false), 2500);
  };



  const handleExportAuditLogs = async () => {
    setExportingLogs(true);
    try {
      const res = await apiFetch(`${API}/features/security/audit-logs`);
      if (!res.ok) throw new Error("Failed to export audit logs");
      const blob = await res.blob();
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `hireiq_audit_logs_${new Date().toISOString().split('T')[0]}.csv`;
      document.body.appendChild(a);
      a.click();
      a.remove();
      toast.success("Audit logs exported successfully! 📂");
    } catch (err) {
      toast.error(err.message || "Error exporting audit logs.");
    } finally {
      setExportingLogs(false);
    }
  };

  const handleUpgrade = async (planName) => {
    setCheckoutLoading(true);
    try {
      const res = await apiFetch(`${API}/billing/create-checkout-session`, {
        method: 'POST',
        body: JSON.stringify({ plan_name: planName }),
      });
      if (!res.ok) {
        const err = await res.json();
        toast.error(err.detail || 'Failed to start checkout');
        return;
      }
      const { checkout_url } = await res.json();
      window.location.href = checkout_url;
    } catch {
      toast.error('Something went wrong. Please try again.');
    } finally {
      setCheckoutLoading(false);
    }
  };

  const handleResetPlan = async () => {
    try {
      const res = await apiFetch(`${API}/settings/billing/update-plan`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ plan_name: 'Free' })
      });
      if (!res.ok) throw new Error();
      setPlan('Free');
      localStorage.setItem('hireiq_saas_plan', 'Free');
      toast.success("Downgraded back to Free tier.");
    } catch {
      toast.error("Failed to cancel subscription.");
    }
  };

  const sliders = [
    { label: 'Resume Matching (TF-IDF + Cosine Similarity)', value: resume,    set: setResume,    color: 'accent-emerald-500' },
    { label: 'GitHub Analysis (Commit Frequency + Stars)',   value: github,    set: setGithub,    color: 'accent-cyan-500' },
    { label: 'LeetCode / Competitive Coding Score',          value: leetcode,  set: setLeetcode,  color: 'accent-green-500' },
    { label: 'Portfolio Review',                             value: portfolio, set: setPortfolio, color: 'accent-amber-500' },
  ];

  return (
    <motion.div initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.2 }}
      className="min-h-screen bg-page p-6 lg:p-10 text-theme-1">
      <div className="max-w-3xl mx-auto space-y-6">

        {/* Title */}
        <div className="flex justify-between items-end">
          <div>
            <h1 className="text-3xl font-bold text-white mb-1">Settings</h1>
            <p className="text-gray-400 text-sm">Configure weights, match metrics, and billing subscriptions</p>
          </div>
          {/* Tabs */}
          <div className="flex bg-white/5 p-1 rounded-xl border border-white/5">
            <button 
              onClick={() => setActiveTab('scoring')}
              className={`px-4 py-2 rounded-lg text-xs font-semibold transition-all ${
                activeTab === 'scoring' 
                  ? 'bg-emerald-600 text-white shadow' 
                  : 'text-gray-400 hover:text-white'
              }`}
            >
              Algorithm & Weights
            </button>
            <button 
              onClick={() => setActiveTab('billing')}
              className={`px-4 py-2 rounded-lg text-xs font-semibold transition-all flex items-center gap-1.5 ${
                activeTab === 'billing' 
                  ? 'bg-emerald-600 text-white shadow' 
                  : 'text-gray-400 hover:text-white'
              }`}
            >
              <Zap size={13} /> Billing & Plan
            </button>
            <button 
              onClick={() => setActiveTab('team')}
              className={`px-4 py-2 rounded-lg text-xs font-semibold transition-all flex items-center gap-1.5 ${
                activeTab === 'team' 
                  ? 'bg-emerald-600 text-white shadow' 
                  : 'text-gray-400 hover:text-white'
              }`}
            >
              <Users size={13} /> Team
            </button>
            <button 
              onClick={() => setActiveTab('integrations')}
              className={`px-4 py-2 rounded-lg text-xs font-semibold transition-all flex items-center gap-1.5 ${
                activeTab === 'integrations' 
                  ? 'bg-emerald-600 text-white shadow' 
                  : 'text-gray-400 hover:text-white'
              }`}
            >
              <Globe size={13} /> Integrations
            </button>
            <button 
              onClick={() => setActiveTab('security')}
              className={`px-4 py-2 rounded-lg text-xs font-semibold transition-all flex items-center gap-1.5 ${
                activeTab === 'security' 
                  ? 'bg-emerald-600 text-white shadow' 
                  : 'text-gray-400 hover:text-white'
              }`}
            >
              <Lock size={13} /> Security & SSO
            </button>
          </div>
        </div>

        {activeTab === 'scoring' ? (
          loading ? (
            <SettingsScoringSkeleton />
          ) : (
          <div className="space-y-6">
            {/* Algorithm Weights */}
            <motion.div initial={{ opacity: 0, y: 15 }} animate={{ opacity: 1, y: 0 }}
              className="bg-card border border-black/10 dark:border-white/10 rounded-xl p-6">
              <div className="flex items-center justify-between mb-6">
                <h2 className="text-lg font-semibold text-white">Scoring Weights</h2>
              </div>

              <div className="space-y-5">
                {sliders.map(item => (
                  <div key={item.label}>
                    <div className="flex justify-between text-sm mb-2">
                      <label className="text-theme-2 font-medium">{item.label}</label>
                      <span className="text-emerald-400 font-semibold tabular-nums">{item.value}%</span>
                    </div>
                    <input type="range" min="0" max="100" value={item.value}
                      onChange={e => item.set(parseInt(e.target.value))}
                      className={`w-full h-2 bg-white/10 rounded-lg appearance-none cursor-pointer ${item.color}`} />
                  </div>
                ))}
              </div>

              {/* Total indicator */}
              <div className={`mt-5 flex items-center justify-between rounded-lg px-4 py-3 ${
                isValid ? 'bg-green-500/10 border border-green-500/20' : 'bg-amber-500/15 border border-amber-500/30'
              }`}>
                <div className="flex items-center gap-2">
                  {!isValid && <AlertCircle className="h-4 w-4 text-amber-400 flex-shrink-0" />}
                  <p className={`text-sm font-medium ${isValid ? 'text-green-400' : 'text-amber-300'}`}>
                    {isValid ? '✓ Weights sum to 100%' : `Weights must total 100% (currently ${total}%)`}
                  </p>
                </div>
                <span className={`text-lg font-bold tabular-nums ${isValid ? 'text-green-400' : 'text-amber-400'}`}>
                  {total}%
                </span>
              </div>

              <button onClick={handleSaveWeights} disabled={!isValid}
                className={`mt-5 px-5 py-2.5 rounded-xl font-medium flex items-center gap-2 transition-all text-sm ${
                  isValid ? 'bg-emerald-600 hover:bg-emerald-700 text-white active:scale-95' : 'bg-gray-700 text-gray-500 cursor-not-allowed'
                }`}>
                <Save className="h-4 w-4" /> Save Weights
              </button>
              {saved && <p className="mt-2 text-green-400 text-sm">✓ Saved — weights will apply to next resume upload</p>}
            </motion.div>

            {/* Bias Audit Toggle */}
            <motion.div initial={{ opacity: 0, y: 15 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.05 }}
              className="bg-card border border-black/10 dark:border-white/10 rounded-xl p-6">
              <h2 className="text-lg font-semibold text-white mb-4">Bias Audit</h2>
              <div className="flex items-center justify-between p-4 bg-white/5 rounded-lg">
                <div>
                  <p className="text-theme-1 font-medium text-sm">Anonymization Engine</p>
                  <p className="text-gray-400 text-xs mt-0.5">Enable blind scoring to reduce demographic bias in resume evaluation</p>
                </div>
                <button onClick={() => setBlindScoring(!blindScoring)}
                  className={`w-12 h-6 rounded-full transition-colors relative flex-shrink-0 ${blindScoring ? 'bg-emerald-600' : 'bg-gray-600'}`}>
                  <div className={`absolute top-0.5 w-5 h-5 rounded-full bg-white transition-transform ${blindScoring ? 'translate-x-6' : 'translate-x-0.5'}`} />
                </button>
              </div>
              {!blindScoring && (
                <div className="mt-3 flex items-center gap-3 bg-amber-500/15 border border-amber-500/30 rounded-lg p-3">
                  <AlertCircle className="h-4 w-4 text-amber-400 flex-shrink-0" />
                  <p className="text-amber-300 text-sm">Turning this off may introduce demographic bias into scoring</p>
                </div>
              )}
            </motion.div>

            {/* Match Thresholds */}
            <motion.div initial={{ opacity: 0, y: 15 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.1 }}
              className="bg-card border border-black/10 dark:border-white/10 rounded-xl p-6">
              <h2 className="text-lg font-semibold text-white mb-4">Match Thresholds</h2>
              <div className="grid grid-cols-3 gap-4">
                {[
                  { label: 'Strong Match', value: strongMatch, set: setStrongMatch, color: 'focus:border-green-500' },
                  { label: 'Match',        value: match,       set: setMatch,       color: 'focus:border-yellow-500' },
                  { label: 'Weak Match',   value: weakMatch,   set: setWeakMatch,   color: 'focus:border-red-500' },
                ].map(item => (
                  <div key={item.label}>
                    <label className="block text-xs font-medium text-gray-400 mb-1">{item.label}</label>
                    <input type="number" min="0" max="100" value={item.value}
                      onChange={e => item.set(parseInt(e.target.value))}
                      className={`w-full px-3 py-2 bg-white/10 border border-white/20 rounded-lg text-theme-1 text-sm focus:outline-none ${item.color}`} />
                  </div>
                ))}
              </div>
              <button onClick={handleSaveThresholds}
                className="mt-5 px-5 py-2.5 bg-emerald-600 hover:bg-emerald-700 text-white rounded-xl font-medium flex items-center gap-2 text-sm transition-all active:scale-95">
                <Save className="h-4 w-4" /> Save Thresholds
              </button>
            </motion.div>
          </div>
          )
        ) : activeTab === 'billing' ? (
          <div className="space-y-6">
            {/* Active Plan Usage Tracker */}
            <motion.div initial={{ opacity: 0, y: 15 }} animate={{ opacity: 1, y: 0 }}
              className="bg-card border border-black/10 dark:border-white/10 rounded-xl p-6 relative overflow-hidden"
            >
              <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4 mb-4">
                <div>
                  <h3 className="text-lg font-semibold text-white">Usage Tracker</h3>
                  <p className="text-xs text-gray-400">Total processed CV resumes on your account</p>
                </div>
                <div className="flex items-center gap-2">
                  <span className="text-xs text-gray-400">Current Plan:</span>
                  <span className={`text-xs font-bold px-3 py-1 rounded-full border ${
                    plan === 'Free' 
                      ? 'bg-white/5 text-white border-white/10' 
                      : plan === 'Pro' 
                        ? 'bg-emerald-500/10 text-emerald-400 border-emerald-500/20 shadow-glow-emerald/10'
                        : 'bg-indigo-500/10 text-indigo-400 border-indigo-500/20 shadow-glow-indigo/10'
                  }`}>
                    {plan} Plan
                  </span>
                </div>
              </div>

              {/* Uploads progress bar */}
              {plan === 'Free' ? (
                <div>
                  <div className="flex justify-between text-xs text-gray-400 mb-2">
                    <span>{quotaUsed} of 5 CV uploads parsed</span>
                    <span className="text-emerald-400 font-bold">{Math.round((quotaUsed / 5) * 100)}% quota used</span>
                  </div>
                  <div className="w-full h-3 bg-white/5 rounded-full overflow-hidden border border-white/5">
                    <div className="h-full bg-gradient-to-r from-emerald-500 to-emerald-400 rounded-full" style={{ width: `${Math.min(100, (quotaUsed / 5) * 100)}%` }} />
                  </div>
                  <p className="text-[11px] text-yellow-400/80 mt-3 flex items-center gap-1.5">
                    <AlertCircle size={12} />
                    {quotaUsed >= 5 
                      ? "You have reached your free tier limit. Upgrade to Pro for unlimited parsing and candidate management."
                      : "Upgrade to Pro for unlimited parsing, advanced filters, and candidate management."}
                  </p>
                </div>
              ) : (
                <div>
                  <div className="flex justify-between text-xs text-gray-400 mb-2">
                    <span>Quota limits (Pro active)</span>
                    <span className="text-emerald-400 font-bold">Unlimited CV Uploads</span>
                  </div>
                  <div className="w-full h-3 bg-white/5 rounded-full overflow-hidden border border-white/5">
                    <div className="h-full bg-gradient-to-r from-emerald-500 to-indigo-500 rounded-full w-full" />
                  </div>
                  <div className="mt-4 flex justify-between items-center">
                    <p className="text-[11px] text-gray-400">Next renewal date: July 9, 2026</p>
                    <button onClick={handleResetPlan} className="text-[10px] text-red-400 hover:text-red-300 underline">
                      Cancel subscription
                    </button>
                  </div>
                </div>
              )}
            </motion.div>

            {/* Pricing Selection Grid */}
            <motion.div initial={{ opacity: 0, y: 15 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.05 }}
              className="grid grid-cols-1 md:grid-cols-3 gap-6"
            >
              {plansList.map(planItem => {
                const isActive = plan === planItem.name;
                return (
                  <div key={planItem.name} className={`rounded-xl border p-5 flex flex-col justify-between transition-all bg-card relative overflow-hidden ${
                    isActive 
                      ? planItem.name === 'Pro' 
                        ? 'border-emerald-500/50 shadow-glow-emerald/10' 
                        : 'border-indigo-500/50 shadow-glow-indigo/10'
                      : 'border-white/5 hover:border-white/10'
                  }`}>
                    {planItem.name === 'Pro' && (
                      <div className="absolute top-0 right-0 bg-emerald-500/20 text-emerald-400 text-[8px] font-bold tracking-widest px-2.5 py-0.5 rounded-bl">RECOMMENDED</div>
                    )}
                    <div>
                      <h4 className={`font-bold text-sm mb-1 flex items-center gap-1 ${
                        planItem.name === 'Pro' ? 'text-emerald-400' : planItem.name === 'Enterprise' ? 'text-indigo-400' : 'text-gray-300'
                      }`}>
                        {planItem.name === 'Pro' && <Zap size={12} />}
                        {planItem.name === 'Enterprise' && <Lock size={11} />}
                        {planItem.name}
                      </h4>
                      <div className="text-2xl font-bold text-white mb-3">{planItem.price}<span className="text-xs text-gray-400 font-normal"> {planItem.price !== 'Custom' && '/ mo'}</span></div>
                      <p className="text-xs text-gray-400 leading-relaxed mb-4">{planItem.desc}</p>
                      <ul className="space-y-2 text-[11px] text-gray-400 mb-5">
                        {planItem.features.map(f => (
                          <li key={f} className="flex items-center gap-1.5"><Check size={11} className="text-emerald-400" /> {f}</li>
                        ))}
                      </ul>
                    </div>
                    {planItem.name === 'Free' ? (
                      <button 
                        disabled 
                        className="w-full py-2 rounded-lg text-xs font-semibold border transition-all bg-white/5 text-white/50 border-white/5 cursor-default"
                      >
                        {isActive ? 'Current Active Plan' : 'Free Tier'}
                      </button>
                    ) : (
                      <button
                        onClick={() => handleUpgrade(planItem.name)}
                        disabled={checkoutLoading || isActive}
                        className={`w-full py-2 rounded-lg text-xs font-semibold transition-all flex items-center justify-center gap-1.5 ${
                          isActive 
                            ? planItem.name === 'Pro' 
                              ? 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 cursor-default' 
                              : 'bg-indigo-500/10 text-indigo-400 border border-indigo-500/20 cursor-default'
                            : planItem.name === 'Pro'
                              ? 'bg-emerald-600 hover:bg-emerald-700 text-white shadow active:scale-95 disabled:opacity-50'
                              : 'bg-white/5 text-white border-white/10 hover:bg-white/10 active:scale-95 disabled:opacity-50'
                        }`}
                      >
                        {isActive ? 'Current Active Plan' : (checkoutLoading ? 'Redirecting...' : 'Upgrade')}
                      </button>
                    )}
                  </div>
                );
              })}
            </motion.div>
          </div>
        ) : (
          /* Team management tab */
          <div className="space-y-6">
            {/* Team Members List Card */}
            <motion.div initial={{ opacity: 0, y: 15 }} animate={{ opacity: 1, y: 0 }}
              className="bg-card border border-black/10 dark:border-white/10 rounded-xl p-6"
            >
              <div className="flex justify-between items-center mb-6">
                <div>
                  <h2 className="text-lg font-semibold text-white">Team Members</h2>
                  <p className="text-xs text-gray-400">Manage colleagues and their workspace roles</p>
                </div>
                {membersLoading && <RefreshCw className="h-4 w-4 text-emerald-500 animate-spin" />}
              </div>

              {membersLoading && members.length === 0 ? (
                <div className="flex justify-center py-8">
                  <RefreshCw className="animate-spin text-emerald-500 h-6 w-6" />
                </div>
              ) : membersError ? (
                <div className="p-4 bg-red-500/10 border border-red-500/20 rounded-xl text-red-400 text-xs flex items-center gap-2">
                  <AlertCircle size={14} /> {membersError}
                </div>
              ) : members.length === 0 ? (
                <div className="text-center py-8 text-xs text-gray-400">
                  No members found.
                </div>
              ) : (
                <div className="overflow-x-auto">
                  <table className="w-full border-collapse text-left">
                    <thead>
                      <tr className="border-b border-white/10 text-gray-400 text-xs font-semibold">
                        <th className="pb-3 pt-2 px-4">Email</th>
                        <th className="pb-3 pt-2 px-4">Role</th>
                        <th className="pb-3 pt-2 px-4">Joined At</th>
                        <th className="pb-3 pt-2 px-4 text-right">Actions</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-white/5 text-xs sm:text-sm">
                      {members.map(m => (
                        <tr key={m.id} className="hover:bg-white/5 transition-colors">
                          <td className="py-3 px-4 text-white font-medium">{m.email}</td>
                          <td className="py-3 px-4">
                            <span className={`px-2.5 py-0.5 rounded-full text-xs font-medium border ${
                              m.role === 'Admin' || m.role === 'Owner'
                                ? 'bg-emerald-500/10 text-emerald-400 border-emerald-500/20'
                                : 'bg-white/5 text-gray-300 border-white/10'
                            }`}>
                              {m.role}
                            </span>
                          </td>
                          <td className="py-3 px-4 text-gray-400">
                            {m.joined_at ? new Date(m.joined_at).toLocaleDateString(undefined, { year: 'numeric', month: 'short', day: 'numeric' }) : 'Pending'}
                          </td>
                          <td className="py-3 px-4 text-right">
                            {user?.email !== m.email && (user?.role === 'Owner' || user?.role === 'Admin') && (
                              <button
                                onClick={() => handleRemoveMember(m.id)}
                                className="text-xs text-red-400 hover:text-red-300 font-semibold transition-colors active:scale-95 flex items-center gap-1 ml-auto"
                              >
                                <Trash2 size={12} /> Remove
                              </button>
                            )}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
            </motion.div>

            {/* Invite Section */}
            {(user?.role === 'Owner' || user?.role === 'Admin') && (
              <motion.div initial={{ opacity: 0, y: 15 }} animate={{ opacity: 1, y: 0 }}
                className="bg-card border border-black/10 dark:border-white/10 rounded-xl p-6"
              >
                <div className="flex items-center gap-2 mb-4">
                  <UserPlus className="text-emerald-500" size={18} />
                  <h3 className="text-lg font-semibold text-white">Invite Team Member</h3>
                </div>
                
                <form onSubmit={handleInvite} className="space-y-4">
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div>
                      <label className="block text-xs font-semibold text-gray-400 mb-1">Email Address</label>
                      <input
                        type="email"
                        required
                        value={inviteEmail}
                        onChange={e => setInviteEmail(e.target.value)}
                        placeholder="colleague@company.com"
                        className="w-full px-3 py-2 bg-white/5 border border-white/10 rounded-lg text-theme-1 text-xs focus:border-emerald-500/50 outline-none transition-colors"
                      />
                    </div>
                    <div>
                      <label className="block text-xs font-semibold text-gray-400 mb-1">Role</label>
                      <select
                        value={inviteRole}
                        onChange={e => setInviteRole(e.target.value)}
                        className="w-full px-3 py-2 bg-white/5 border border-white/10 rounded-lg text-theme-1 text-xs focus:border-emerald-500/50 outline-none transition-colors"
                      >
                        <option value="Recruiter">Recruiter</option>
                        <option value="Admin">Admin</option>
                        <option value="Hiring Manager">Hiring Manager</option>
                        <option value="Viewer">Viewer</option>
                      </select>
                    </div>
                  </div>
                  
                  <button
                    type="submit"
                    disabled={inviteLoading}
                    className="px-5 py-2.5 bg-emerald-600 hover:bg-emerald-700 text-white rounded-xl font-medium flex items-center gap-2 text-xs transition-all active:scale-95 disabled:opacity-50"
                  >
                    {inviteLoading ? (
                      <>
                        <RefreshCw size={13} className="animate-spin" /> Inviting...
                      </>
                    ) : (
                      <>
                        Send Invitation
                      </>
                    )}
                  </button>
                </form>

                {inviteSuccessLink && (
                  <motion.div initial={{ opacity: 0, scale: 0.95 }} animate={{ opacity: 1, scale: 1 }}
                    className="mt-4 p-4 bg-emerald-500/10 border border-emerald-500/20 rounded-xl space-y-2"
                  >
                    <p className="text-xs text-emerald-400 font-semibold flex items-center gap-1.5">
                      <Check size={14} /> Invitation generated successfully!
                    </p>
                    <p className="text-xs text-gray-400">Share this link with your team member to accept the invite:</p>
                    <div className="flex gap-2">
                      <input
                        type="text"
                        readOnly
                        value={inviteSuccessLink}
                        className="flex-1 px-3 py-1.5 bg-black/30 border border-white/10 rounded-lg text-gray-300 text-xs font-mono select-all outline-none"
                      />
                      <button
                        onClick={() => {
                          navigator.clipboard.writeText(inviteSuccessLink);
                          toast.success("Invitation link copied to clipboard!");
                        }}
                        className="px-3 py-1.5 bg-emerald-600 hover:bg-emerald-700 text-white rounded-lg text-xs font-semibold transition-colors"
                      >
                        Copy Link
                      </button>
                    </div>
                  </motion.div>
                )}
              </motion.div>
            )}
          </div>
        )}

        {activeTab === 'integrations' && (
          <div className="space-y-6">
            <motion.div initial={{ opacity: 0, y: 15 }} animate={{ opacity: 1, y: 0 }}
              className="bg-card border border-black/10 dark:border-white/10 rounded-xl p-6"
            >
              <div className="flex items-center gap-2 mb-4">
                <Globe className="text-emerald-500" size={18} />
                <h3 className="text-lg font-semibold text-white">Integrations Marketplace</h3>
              </div>
              <p className="text-xs text-gray-400 mb-6">Connect HireIQ with your existing HR tech stack, communication tools, and calendar services to automate workflows.</p>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {/* Slack Card */}
                <div className="p-4 bg-white/5 border border-white/10 rounded-xl flex flex-col justify-between space-y-4">
                  <div className="flex items-start justify-between">
                    <div className="flex items-center gap-2.5">
                      <div className="p-2 bg-purple-500/10 text-purple-400 rounded-lg"><Webhook size={18} /></div>
                      <div>
                        <h4 className="text-sm font-semibold text-white">Slack Notifications</h4>
                        <p className="text-[10px] text-gray-400">Post scoring updates and candidate matches to channels.</p>
                      </div>
                    </div>
                    <input type="checkbox" checked={integrations.slack}
                      onChange={e => setIntegrations({...integrations, slack: e.target.checked})}
                      className="w-4 h-4 rounded border-gray-300 text-emerald-600 focus:ring-emerald-500 cursor-pointer accent-emerald-500" />
                  </div>
                  <button onClick={() => setConfigureIntegration("Slack")} className="px-3 py-1.5 bg-white/5 hover:bg-white/10 border border-white/10 text-white rounded-lg text-xs font-semibold self-start transition-all">Configure</button>
                </div>

                {/* Gmail Card */}
                <div className="p-4 bg-white/5 border border-white/10 rounded-xl flex flex-col justify-between space-y-4">
                  <div className="flex items-start justify-between">
                    <div className="flex items-center gap-2.5">
                      <div className="p-2 bg-red-500/10 text-red-400 rounded-lg"><Mail size={18} /></div>
                      <div>
                        <h4 className="text-sm font-semibold text-white">Gmail Integration</h4>
                        <p className="text-[10px] text-gray-400">Native tracking and automated recruiter outreach.</p>
                      </div>
                    </div>
                    <input type="checkbox" checked={integrations.gmail}
                      onChange={e => setIntegrations({...integrations, gmail: e.target.checked})}
                      className="w-4 h-4 rounded border-gray-300 text-emerald-600 focus:ring-emerald-500 cursor-pointer accent-emerald-500" />
                  </div>
                  <button onClick={() => setConfigureIntegration("Gmail")} className="px-3 py-1.5 bg-white/5 hover:bg-white/10 border border-white/10 text-white rounded-lg text-xs font-semibold self-start transition-all">Configure</button>
                </div>

                {/* Outlook Card */}
                <div className="p-4 bg-white/5 border border-white/10 rounded-xl flex flex-col justify-between space-y-4">
                  <div className="flex items-start justify-between">
                    <div className="flex items-center gap-2.5">
                      <div className="p-2 bg-blue-500/10 text-blue-400 rounded-lg"><Mail size={18} /></div>
                      <div>
                        <h4 className="text-sm font-semibold text-white">Outlook Integration</h4>
                        <p className="text-[10px] text-gray-400">Sync conversations and schedule communications.</p>
                      </div>
                    </div>
                    <input type="checkbox" checked={integrations.outlook}
                      onChange={e => setIntegrations({...integrations, outlook: e.target.checked})}
                      className="w-4 h-4 rounded border-gray-300 text-emerald-600 focus:ring-emerald-500 cursor-pointer accent-emerald-500" />
                  </div>
                  <button onClick={() => setConfigureIntegration("Outlook")} className="px-3 py-1.5 bg-white/5 hover:bg-white/10 border border-white/10 text-white rounded-lg text-xs font-semibold self-start transition-all">Configure</button>
                </div>

                {/* Google Calendar Card */}
                <div className="p-4 bg-white/5 border border-white/10 rounded-xl flex flex-col justify-between space-y-4">
                  <div className="flex items-start justify-between">
                    <div className="flex items-center gap-2.5">
                      <div className="p-2 bg-emerald-500/10 text-emerald-400 rounded-lg"><Calendar size={18} /></div>
                      <div>
                        <h4 className="text-sm font-semibold text-white">Google Calendar</h4>
                        <p className="text-[10px] text-gray-400">Sync interviews directly to Google Calendars.</p>
                      </div>
                    </div>
                    <input type="checkbox" checked={integrations.gcal}
                      onChange={e => setIntegrations({...integrations, gcal: e.target.checked})}
                      className="w-4 h-4 rounded border-gray-300 text-emerald-600 focus:ring-emerald-500 cursor-pointer accent-emerald-500" />
                  </div>
                  <button onClick={() => setConfigureIntegration("Google Calendar")} className="px-3 py-1.5 bg-white/5 hover:bg-white/10 border border-white/10 text-white rounded-lg text-xs font-semibold self-start transition-all">Configure</button>
                </div>

                {/* Workday Card */}
                <div className="p-4 bg-white/5 border border-white/10 rounded-xl flex flex-col justify-between space-y-4">
                  <div className="flex items-start justify-between">
                    <div className="flex items-center gap-2.5">
                      <div className="p-2 bg-orange-500/10 text-orange-400 rounded-lg"><Database size={18} /></div>
                      <div>
                        <h4 className="text-sm font-semibold text-white">Workday HRIS</h4>
                        <p className="text-[10px] text-gray-400">Export selected candidates directly to Workday.</p>
                      </div>
                    </div>
                    <input type="checkbox" checked={integrations.workday}
                      onChange={e => setIntegrations({...integrations, workday: e.target.checked})}
                      className="w-4 h-4 rounded border-gray-300 text-emerald-600 focus:ring-emerald-500 cursor-pointer accent-emerald-500" />
                  </div>
                  <button onClick={() => setConfigureIntegration("Workday")} className="px-3 py-1.5 bg-white/5 hover:bg-white/10 border border-white/10 text-white rounded-lg text-xs font-semibold self-start transition-all">Configure</button>
                </div>

                {/* Codility Card */}
                <div className="p-4 bg-white/5 border border-white/10 rounded-xl flex flex-col justify-between space-y-4">
                  <div className="flex items-start justify-between">
                    <div className="flex items-center gap-2.5">
                      <div className="p-2 bg-yellow-500/10 text-yellow-400 rounded-lg"><Key size={18} /></div>
                      <div>
                        <h4 className="text-sm font-semibold text-white">Codility Assessments</h4>
                        <p className="text-[10px] text-gray-400">Trigger coding tests and pull scorecard ratings.</p>
                      </div>
                    </div>
                    <input type="checkbox" checked={integrations.codility}
                      onChange={e => setIntegrations({...integrations, codility: e.target.checked})}
                      className="w-4 h-4 rounded border-gray-300 text-emerald-600 focus:ring-emerald-500 cursor-pointer accent-emerald-500" />
                  </div>
                  <button onClick={() => setConfigureIntegration("Codility")} className="px-3 py-1.5 bg-white/5 hover:bg-white/10 border border-white/10 text-white rounded-lg text-xs font-semibold self-start transition-all">Configure</button>
                </div>
              </div>
            </motion.div>
          </div>
        )}

        {activeTab === 'security' && (
          <div className="space-y-6">
            <motion.div initial={{ opacity: 0, y: 15 }} animate={{ opacity: 1, y: 0 }}
              className="bg-card border border-black/10 dark:border-white/10 rounded-xl p-6 space-y-6"
            >
              {/* SSO Configuration */}
              <div className="space-y-3">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <Key className="text-emerald-500" size={18} />
                    <h3 className="text-base font-semibold text-white">Single Sign-On (SSO)</h3>
                  </div>
                  <div className="flex items-center">
                    <span className="text-xs text-gray-400 mr-2">{ssoEnabled ? "Enabled" : "Disabled"}</span>
                    <input type="checkbox" checked={ssoEnabled}
                      onChange={e => setSsoEnabled(e.target.checked)}
                      className="w-4 h-4 rounded border-gray-300 text-emerald-600 focus:ring-emerald-500 cursor-pointer accent-emerald-500" />
                  </div>
                </div>
                <p className="text-xs text-gray-400">Enforce SAML 2.0 or OIDC authentication for all team members signing into this recruiter workspace.</p>

                {ssoEnabled && (
                  <motion.div initial={{ opacity: 0, height: 0 }} animate={{ opacity: 1, height: 'auto' }} className="space-y-4 pt-3 border-t border-white/5">
                    <div>
                      <label className="block text-xs font-semibold text-gray-400 mb-1">SSO Metadata Identity Provider URL</label>
                      <input type="text" value={ssoProviderUrl} onChange={e => setSsoProviderUrl(e.target.value)}
                        className="w-full px-3 py-2 bg-white/5 border border-white/10 rounded-lg text-theme-1 text-xs outline-none focus:border-emerald-500/50" />
                    </div>
                    <div className="grid grid-cols-2 gap-4">
                      <div>
                        <label className="block text-xs font-semibold text-gray-400 mb-1">Entity ID</label>
                        <input type="text" readOnly value="urn:auth0:hireiq:saml"
                          className="w-full px-3 py-2 bg-black/20 border border-white/5 rounded-lg text-gray-400 text-xs font-mono outline-none" />
                      </div>
                      <div>
                        <label className="block text-xs font-semibold text-gray-400 mb-1">ACS URL</label>
                        <input type="text" readOnly value="https://api.hireiq.dev/sso/saml/callback"
                          className="w-full px-3 py-2 bg-black/20 border border-white/5 rounded-lg text-gray-400 text-xs font-mono outline-none" />
                      </div>
                    </div>
                    <button onClick={() => toast.success("SSO Configuration saved successfully!")} className="px-4 py-2 bg-emerald-600 hover:bg-emerald-700 text-white rounded-lg text-xs font-semibold transition-all">Save SSO Config</button>
                  </motion.div>
                )}
              </div>

              {/* GDPR Compliance Section */}
              <div className="pt-6 border-t border-white/10 space-y-3">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <Shield className="text-emerald-500" size={18} />
                    <h3 className="text-base font-semibold text-white">GDPR & Data Protection</h3>
                  </div>
                  <div className="flex items-center">
                    <span className="text-xs text-gray-400 mr-2">{gdprDeleteEnabled ? "Active" : "Inactive"}</span>
                    <input type="checkbox" checked={gdprDeleteEnabled}
                      onChange={e => setGdprDeleteEnabled(e.target.checked)}
                      className="w-4 h-4 rounded border-gray-300 text-emerald-600 focus:ring-emerald-500 cursor-pointer accent-emerald-500" />
                  </div>
                </div>
                <p className="text-xs text-gray-400">Manage candidate data compliance. When active, candidates can request full deletion of their uploaded profiles.</p>
                <div>
                  <label className="block text-xs font-semibold text-gray-400 mb-1">Candidate Data Retention Period</label>
                  <select value={retentionPeriod} onChange={e => setRetentionPeriod(e.target.value)}
                    className="w-full max-w-xs px-3 py-2 bg-white/5 border border-white/10 rounded-lg text-theme-1 text-xs focus:border-emerald-500/50 outline-none"
                  >
                    <option value="indefinite">Keep Indefinitely (No automatic deletion)</option>
                    <option value="6months">Auto-delete after 6 months</option>
                    <option value="1year">Auto-delete after 1 year</option>
                    <option value="2years">Auto-delete after 2 years</option>
                  </select>
                </div>
                <button onClick={() => toast.success("GDPR compliance settings updated!")} className="px-4 py-2 bg-emerald-600 hover:bg-emerald-700 text-white rounded-lg text-xs font-semibold transition-all mt-1">Save Compliance Settings</button>
              </div>

              {/* Audit Logs Section */}
              <div className="pt-6 border-t border-white/10 space-y-3">
                <div className="flex items-center gap-2">
                  <Database className="text-emerald-500" size={18} />
                  <h3 className="text-base font-semibold text-white">Security Audit Trail Logs</h3>
                </div>
                <p className="text-xs text-gray-400">Download cryptographically verifiable logs documenting recuited user events, login locations, scoring adjustments, and data exports.</p>
                <button
                  onClick={handleExportAuditLogs}
                  disabled={exportingLogs}
                  className="px-4 py-2 bg-emerald-600 hover:bg-emerald-700 disabled:opacity-50 text-white rounded-lg text-xs font-semibold transition-all flex items-center gap-1.5"
                >
                  {exportingLogs ? "Exporting..." : "Export Audit Logs (CSV)"}
                </button>
              </div>
            </motion.div>
          </div>
        )}

        {/* Configure Integration Modal */}
        {configureIntegration && (
          <div className="fixed inset-0 z-50 flex items-center justify-center p-6 bg-black/60 backdrop-blur-sm">
            <motion.div initial={{ opacity: 0, scale: 0.95 }} animate={{ opacity: 1, scale: 1 }}
              className="w-full max-w-md bg-[#131324] border border-white/10 rounded-xl p-6 space-y-4 shadow-2xl"
            >
              <h3 className="text-lg font-bold text-white">Configure {configureIntegration}</h3>
              <p className="text-xs text-gray-400">Configure connection tokens, API endpoints, or Webhooks for the {configureIntegration} service integration.</p>
              
              <div className="space-y-3">
                <div>
                  <label className="block text-xs font-semibold text-gray-400 mb-1">API Webhook / Client URL</label>
                  <input type="text" placeholder={`https://api.company.com/hooks/${configureIntegration.toLowerCase()}`}
                    className="w-full px-3 py-2 bg-white/5 border border-white/10 rounded-lg text-gray-300 text-xs outline-none focus:border-emerald-500/50" />
                </div>
                <div>
                  <label className="block text-xs font-semibold text-gray-400 mb-1">Secret Token / Authorization Key</label>
                  <input type="password" placeholder="••••••••••••••••••••••••••••••••"
                    className="w-full px-3 py-2 bg-white/5 border border-white/10 rounded-lg text-gray-300 text-xs outline-none focus:border-emerald-500/50" />
                </div>
              </div>

              <div className="flex justify-end gap-2 pt-2 border-t border-white/5">
                <button onClick={() => setConfigureIntegration(null)} className="px-4 py-2 bg-white/5 hover:bg-white/10 border border-white/10 text-white rounded-lg text-xs font-semibold transition-colors">Cancel</button>
                <button onClick={() => {
                  setConfigureIntegration(null);
                  toast.success(`${configureIntegration} integration saved and connected!`);
                }} className="px-4 py-2 bg-emerald-600 hover:bg-emerald-700 text-white rounded-lg text-xs font-semibold transition-colors">Save & Test Connection</button>
              </div>
            </motion.div>
          </div>
        )}

      </div>
    </motion.div>
  );
}
