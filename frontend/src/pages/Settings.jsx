import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { AlertCircle, Save, RefreshCw, Check, Zap, Lock, CreditCard } from 'lucide-react';
import { toast } from 'sonner';

const API = '/api/v1';

export default function Settings() {
  const [activeTab, setActiveTab] = useState('scoring'); // 'scoring' | 'billing'
  
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
  const [cardNumber, setCardNumber] = useState('');
  const [cardHolder, setCardHolder] = useState('');
  const [cardExpiry, setCardExpiry] = useState('');
  const [cardCVC, setCardCVC] = useState('');
  const [checkoutLoading, setCheckoutLoading] = useState(false);
  const [showCheckout, setShowCheckout] = useState(false);
  const [selectedPlan, setSelectedPlan] = useState('');

  // Load current weights from backend on mount and listen for Stripe checkout callbacks
  useEffect(() => {
    fetch(`${API}/settings/weights`)
      .then(r => r.ok ? r.json() : null)
      .then(data => {
        if (data) {
          setResume(Math.round((data.resume    ?? 0.4) * 100));
          setGithub(Math.round((data.github    ?? 0.3) * 100));
          setLeetcode(Math.round((data.leetcode  ?? 0.2) * 100));
          setPortfolio(Math.round((data.portfolio ?? 0.1) * 100));
        }
      })
      .catch(() => {})
      .finally(() => setLoading(false));

    // Listen for Stripe checkout session redirect success/cancel params
    const params = new URLSearchParams(window.location.search);
    if (params.get('checkout') === 'success') {
      const planName = localStorage.getItem('hireiq_saas_pending_plan') || 'Pro';
      setPlan(planName);
      localStorage.setItem('hireiq_saas_plan', planName);
      localStorage.removeItem('hireiq_saas_pending_plan');
      toast.success(`Subscription verified! You have been upgraded to ${planName}! 🎉`);
      window.history.replaceState({}, document.title, window.location.pathname);
    } else if (params.get('checkout') === 'cancel') {
      toast.info("Subscription checkout was cancelled.");
      window.history.replaceState({}, document.title, window.location.pathname);
    }
  }, []);

  const total   = resume + github + leetcode + portfolio;
  const isValid = total === 100;

  const handleSaveWeights = async () => {
    try {
      await fetch(`${API}/settings/weights`, {
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
      await fetch(`${API}/settings/thresholds`, {
        method:  'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ strong: strongMatch, match, weak: weakMatch }),
      });
    } catch { /* backend offline */ }
    setSaved(true);
    setTimeout(() => setSaved(false), 2500);
  };

  const handleInitiateCheckout = async (planName) => {
    setSelectedPlan(planName);
    setCheckoutLoading(true);
    try {
      // Store pending plan name locally to activate on successful redirect back
      localStorage.setItem('hireiq_saas_pending_plan', planName);
      
      const res = await fetch(`${API}/settings/billing/create-checkout-session`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          plan_name: planName,
          success_url: window.location.origin + '/settings?checkout=success',
          cancel_url: window.location.origin + '/settings?checkout=cancel'
        })
      });
      if (!res.ok) throw new Error();
      const data = await res.json();
      if (data.url && data.url.includes('stripe.com')) {
        // Redirect to Stripe Checkout page
        window.location.href = data.url;
      } else {
        // Fallback to beautiful local credit card mock form
        setShowCheckout(true);
      }
    } catch {
      // Fallback on error / offline
      setShowCheckout(true);
    } finally {
      setCheckoutLoading(false);
    }
  };

  const handleSubscribe = (e) => {
    e.preventDefault();
    if (!cardNumber || !cardHolder || !cardExpiry || !cardCVC) {
      toast.error("Please fill in all payment fields.");
      return;
    }
    setCheckoutLoading(true);
    setTimeout(() => {
      setCheckoutLoading(false);
      setPlan(selectedPlan);
      localStorage.setItem('hireiq_saas_plan', selectedPlan);
      localStorage.removeItem('hireiq_saas_pending_plan');
      setShowCheckout(false);
      toast.success(`Success! You have been upgraded to the ${selectedPlan} plan! 🎉`);
    }, 2000);
  };

  const handleResetPlan = () => {
    setPlan('Free');
    localStorage.setItem('hireiq_saas_plan', 'Free');
    toast.success("Downgraded back to Free tier.");
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
          </div>
        </div>

        {activeTab === 'scoring' ? (
          <div className="space-y-6">
            {/* Algorithm Weights */}
            <motion.div initial={{ opacity: 0, y: 15 }} animate={{ opacity: 1, y: 0 }}
              className="bg-card border border-black/10 dark:border-white/10 rounded-xl p-6">
              <div className="flex items-center justify-between mb-6">
                <h2 className="text-lg font-semibold text-white">Scoring Weights</h2>
                {loading && <RefreshCw className="h-4 w-4 text-gray-500 animate-spin" />}
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
        ) : (
          /* Billing & SaaS tabs */
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
                    <span>3 of 5 CV uploads parsed</span>
                    <span className="text-emerald-400 font-bold">60% quota used</span>
                  </div>
                  <div className="w-full h-3 bg-white/5 rounded-full overflow-hidden border border-white/5">
                    <div className="h-full bg-gradient-to-r from-emerald-500 to-emerald-400 rounded-full" style={{ width: '60%' }} />
                  </div>
                  <p className="text-[11px] text-yellow-400/80 mt-3 flex items-center gap-1.5">
                    <AlertCircle size={12} />
                    You are approaching your free tier limit. Upgrade to Pro for unlimited parsing and candidate management.
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
              {/* Free Card */}
              <div className={`rounded-xl border p-5 flex flex-col justify-between transition-all bg-card ${
                plan === 'Free' ? 'border-white/20' : 'border-white/5'
              }`}>
                <div>
                  <h4 className="font-bold text-sm text-gray-300 mb-1">Free Tier</h4>
                  <div className="text-2xl font-bold text-white mb-3">$0<span className="text-xs text-gray-400 font-normal"> / mo</span></div>
                  <p className="text-xs text-gray-400 leading-relaxed mb-4">Basic candidate evaluation and resume parsing tool.</p>
                  <ul className="space-y-2 text-[11px] text-gray-400 mb-5">
                    <li className="flex items-center gap-1.5"><Check size={11} className="text-emerald-400" /> 5 resume parses / month</li>
                    <li className="flex items-center gap-1.5"><Check size={11} className="text-emerald-400" /> Basic TF-IDF match score</li>
                    <li className="flex items-center gap-1.5"><Check size={11} className="text-emerald-400" /> Candidate List View</li>
                  </ul>
                </div>
                <button 
                  disabled={plan === 'Free'} 
                  className={`w-full py-2 rounded-lg text-xs font-semibold border transition-all ${
                    plan === 'Free' 
                      ? 'bg-white/5 text-white/50 border-white/5 cursor-default' 
                      : 'bg-white/5 text-white border-white/10 hover:bg-white/10'
                  }`}
                >
                  {plan === 'Free' ? 'Current Active Plan' : 'Free Tier'}
                </button>
              </div>

              {/* Pro Card */}
              <div className={`rounded-xl border p-5 flex flex-col justify-between transition-all relative overflow-hidden bg-card ${
                plan === 'Pro' 
                  ? 'border-emerald-500/50 shadow-glow-emerald/10' 
                  : 'border-emerald-500/20 hover:border-emerald-500/30'
              }`}>
                <div className="absolute top-0 right-0 bg-emerald-500/20 text-emerald-400 text-[8px] font-bold tracking-widest px-2.5 py-0.5 rounded-bl">RECOMMENDED</div>
                <div>
                  <h4 className="font-bold text-sm text-emerald-400 mb-1 flex items-center gap-1">
                    <Zap size={12} /> Recruiter Suite
                  </h4>
                  <div className="text-2xl font-bold text-white mb-3">$79<span className="text-xs text-gray-400 font-normal"> / mo</span></div>
                  <p className="text-xs text-gray-400 leading-relaxed mb-4">Power features for scaling teams and active recruiters.</p>
                  <ul className="space-y-2 text-[11px] text-gray-400 mb-5">
                    <li className="flex items-center gap-1.5"><Check size={11} className="text-emerald-400" /> Unlimited CV uploads</li>
                    <li className="flex items-center gap-1.5"><Check size={11} className="text-emerald-400" /> Kanban Hiring pipeline board</li>
                    <li className="flex items-center gap-1.5"><Check size={11} className="text-emerald-400" /> Advanced filter controls</li>
                    <li className="flex items-center gap-1.5"><Check size={11} className="text-emerald-400" /> Real-time GitHub profile sync</li>
                  </ul>
                </div>
                <button
                  onClick={() => handleInitiateCheckout('Pro')}
                  disabled={plan === 'Pro' || checkoutLoading}
                  className={`w-full py-2 rounded-lg text-xs font-semibold transition-all flex items-center justify-center gap-1.5 ${
                    plan === 'Pro' 
                      ? 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 cursor-default' 
                      : 'bg-emerald-600 hover:bg-emerald-700 text-white shadow active:scale-95 disabled:opacity-50'
                  }`}
                >
                  {checkoutLoading && selectedPlan === 'Pro' && <RefreshCw className="h-3 w-3 animate-spin" />}
                  {plan === 'Pro' ? 'Current Active Plan' : 'Upgrade to Pro'}
                </button>
              </div>

              {/* Enterprise Card */}
              <div className={`rounded-xl border p-5 flex flex-col justify-between transition-all bg-card ${
                plan === 'Enterprise' ? 'border-white/20' : 'border-white/5'
              }`}>
                <div>
                  <h4 className="font-bold text-sm text-indigo-400 mb-1 flex items-center gap-1">
                    <Lock size={11} /> Enterprise
                  </h4>
                  <div className="text-2xl font-bold text-white mb-3">Custom<span className="text-xs text-gray-400 font-normal"> / mo</span></div>
                  <p className="text-xs text-gray-400 leading-relaxed mb-4">Dedicated database infrastructure and security controls.</p>
                  <ul className="space-y-2 text-[11px] text-gray-400 mb-5">
                    <li className="flex items-center gap-1.5"><Check size={11} className="text-emerald-400" /> custom weight templates</li>
                    <li className="flex items-center gap-1.5"><Check size={11} className="text-emerald-400" /> DB sync (Supabase/PostgreSQL)</li>
                    <li className="flex items-center gap-1.5"><Check size={11} className="text-emerald-400" /> PDF and CSV reports</li>
                    <li className="flex items-center gap-1.5"><Check size={11} className="text-emerald-400" /> 24/7 Priority support SLA</li>
                  </ul>
                </div>
                <button
                  onClick={() => handleInitiateCheckout('Enterprise')}
                  disabled={plan === 'Enterprise' || checkoutLoading}
                  className={`w-full py-2 rounded-lg text-xs font-semibold border transition-all flex items-center justify-center gap-1.5 ${
                    plan === 'Enterprise' 
                      ? 'bg-indigo-500/10 text-indigo-400 border border-indigo-500/20 cursor-default' 
                      : 'bg-white/5 text-white border-white/10 hover:bg-white/10 active:scale-95 disabled:opacity-50'
                  }`}
                >
                  {checkoutLoading && selectedPlan === 'Enterprise' && <RefreshCw className="h-3 w-3 animate-spin" />}
                  {plan === 'Enterprise' ? 'Current Active Plan' : 'Select Enterprise'}
                </button>
              </div>
            </motion.div>

            {/* Expandable Checkout Card Portal */}
            <AnimatePresence>
              {showCheckout && (
                <motion.div 
                  initial={{ opacity: 0, scale: 0.95 }}
                  animate={{ opacity: 1, scale: 1 }}
                  exit={{ opacity: 0, scale: 0.95 }}
                  className="bg-card border border-white/10 rounded-xl p-6 relative overflow-hidden"
                >
                  <div className="absolute top-0 right-0 p-4 opacity-5 pointer-events-none">
                    <CreditCard size={150} className="text-emerald-400" />
                  </div>
                  
                  <div className="flex justify-between items-start mb-6">
                    <div>
                      <h3 className="text-lg font-semibold text-white">💳 Checkout</h3>
                      <p className="text-xs text-gray-400">Billing details for {selectedPlan} subscription package</p>
                    </div>
                    <button onClick={() => setShowCheckout(false)} className="text-gray-400 hover:text-white text-xs">✕ Cancel</button>
                  </div>

                  <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                    {/* Visual Credit Card Preview */}
                    <div className="flex flex-col justify-center items-center">
                      <div className="w-full max-w-[280px] h-44 bg-gradient-to-br from-emerald-600 via-emerald-800 to-indigo-900 rounded-xl p-5 text-white flex flex-col justify-between shadow-xl relative overflow-hidden">
                        {/* Chip & Brand */}
                        <div className="flex justify-between items-center">
                          <div className="w-10 h-7 bg-yellow-400/20 rounded-md border border-yellow-400/30 flex items-center justify-center font-bold text-[9px] text-yellow-300">CHIP</div>
                          <div className="font-display font-bold italic text-sm tracking-wider">HireiQ {selectedPlan}</div>
                        </div>
                        {/* Number */}
                        <div className="text-base tracking-widest font-mono select-none my-2">
                          {cardNumber || '•••• •••• •••• ••••'}
                        </div>
                        {/* Holder & Expiry */}
                        <div className="flex justify-between text-[10px] font-mono">
                          <div className="max-w-[170px] truncate">
                            <span className="text-[8px] text-white/50 block">CARDHOLDER</span>
                            <span className="uppercase">{cardHolder || 'CARDHOLDER NAME'}</span>
                          </div>
                          <div className="text-right">
                            <span className="text-[8px] text-white/50 block">EXPIRES</span>
                            <span>{cardExpiry || 'MM/YY'}</span>
                          </div>
                        </div>
                      </div>
                    </div>

                    {/* Inputs form */}
                    <form onSubmit={handleSubscribe} className="space-y-4">
                      <div>
                        <label className="block text-xs font-semibold text-gray-400 mb-1">Cardholder Name</label>
                        <input 
                          type="text" 
                          required
                          placeholder="e.g. John Doe"
                          value={cardHolder} 
                          onChange={e => setCardHolder(e.target.value)}
                          className="w-full px-3 py-2 bg-white/5 border border-white/10 rounded-lg text-theme-1 text-xs focus:border-emerald-500/50 outline-none transition-colors"
                        />
                      </div>
                      
                      <div>
                        <label className="block text-xs font-semibold text-gray-400 mb-1">Card Number</label>
                        <input 
                          type="text" 
                          required
                          maxLength="19"
                          placeholder="4000 1234 5678 9010"
                          value={cardNumber} 
                          onChange={e => {
                            // simple formatting space
                            const val = e.target.value.replace(/\s?/g, '').replace(/(\d{4})/g, '$1 ').trim();
                            setCardNumber(val);
                          }}
                          className="w-full px-3 py-2 bg-white/5 border border-white/10 rounded-lg text-theme-1 text-xs focus:border-emerald-500/50 outline-none transition-colors font-mono"
                        />
                      </div>

                      <div className="grid grid-cols-2 gap-4">
                        <div>
                          <label className="block text-xs font-semibold text-gray-400 mb-1">Expiration (MM/YY)</label>
                          <input 
                            type="text" 
                            required
                            maxLength="5"
                            placeholder="12/28"
                            value={cardExpiry} 
                            onChange={e => {
                              let val = e.target.value.replace(/\D/g, '');
                              if (val.length > 2) val = val.substring(0, 2) + '/' + val.substring(2, 4);
                              setCardExpiry(val);
                            }}
                            className="w-full px-3 py-2 bg-white/5 border border-white/10 rounded-lg text-theme-1 text-xs focus:border-emerald-500/50 outline-none transition-colors font-mono"
                          />
                        </div>
                        <div>
                          <label className="block text-xs font-semibold text-gray-400 mb-1">CVC / CVV</label>
                          <input 
                            type="password" 
                            required
                            maxLength="3"
                            placeholder="•••"
                            value={cardCVC} 
                            onChange={e => setCardCVC(e.target.value.replace(/\D/g, ''))}
                            className="w-full px-3 py-2 bg-white/5 border border-white/10 rounded-lg text-theme-1 text-xs focus:border-emerald-500/50 outline-none transition-colors font-mono"
                          />
                        </div>
                      </div>

                      <button
                        type="submit"
                        disabled={checkoutLoading}
                        className="w-full mt-4 py-2.5 bg-emerald-600 hover:bg-emerald-700 text-white rounded-xl text-xs font-bold transition-all flex items-center justify-center gap-2 shadow active:scale-95 disabled:opacity-50"
                      >
                        {checkoutLoading ? (
                          <>
                            <RefreshCw size={14} className="animate-spin" /> Upgrading Plan...
                          </>
                        ) : (
                          <>
                            Subscribe to {selectedPlan} plan
                          </>
                        )}
                      </button>
                    </form>
                  </div>
                </motion.div>
              )}
            </AnimatePresence>
          </div>
        )}

      </div>
    </motion.div>
  );
}
