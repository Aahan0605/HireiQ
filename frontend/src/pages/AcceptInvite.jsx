import React, { useState, useEffect } from 'react';
import { useSearchParams, useNavigate, Link } from 'react-router-dom';
import { motion } from 'framer-motion';
import { CheckCircle2, XCircle, Loader2, Lock } from 'lucide-react';
import { useAuth } from '../context/AuthContext';
import ConstellationBackground from '../components/ConstellationBackground';

const API = '/api/v1';

export default function AcceptInvite() {
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();
  const { setToken, setUser } = useAuth();
  const token = searchParams.get('token');

  const [status, setStatus] = useState('loading'); // loading | ready | accepting | success | error
  const [invite, setInvite] = useState(null);
  const [error, setError] = useState('');
  const [password, setPassword] = useState('');

  useEffect(() => {
    if (!token) {
      setStatus('error');
      setError('No invitation token found in this link.');
      return;
    }
    fetch(`${API}/members/invite/${token}`)
      .then(r => r.json().then(d => ({ ok: r.ok, data: d })))
      .then(({ ok, data }) => {
        if (!ok) { setStatus('error'); setError(data.detail || 'Invalid invitation.'); return; }
        setInvite(data);
        setStatus('ready');
      })
      .catch(() => { setStatus('error'); setError('Network error. Please try again.'); });
  }, [token]);

  const handleAccept = async (e) => {
    e.preventDefault();
    setStatus('accepting');
    try {
      const res = await fetch(`${API}/members/invite/${token}/accept`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ token, password }),
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || 'Failed to accept invitation.');

      localStorage.setItem('hireiq_token', data.access_token);
      localStorage.setItem('hireiq_user', JSON.stringify(data.user));
      setToken(data.access_token);
      setUser(data.user);
      setStatus('success');
      setTimeout(() => navigate('/dashboard', { replace: true }), 1200);
    } catch (err) {
      setStatus('ready');
      setError(err.message);
    }
  };

  return (
    <div className="relative min-h-screen flex items-center justify-center p-6 bg-bg overflow-hidden">
      <ConstellationBackground />
      <motion.div
        initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }}
        className="w-full max-w-md relative z-10 bg-surface/30 backdrop-blur-xl border border-white/10 rounded-2xl p-8 sm:p-10"
      >
        {status === 'loading' && (
          <div className="text-center py-8">
            <Loader2 className="h-8 w-8 animate-spin text-emerald-400 mx-auto" />
          </div>
        )}

        {status === 'error' && (
          <div className="text-center space-y-4">
            <XCircle className="h-12 w-12 text-rose-400 mx-auto" />
            <h1 className="font-display text-xl font-bold text-white">Invitation Invalid</h1>
            <p className="text-gray-400 text-sm">{error}</p>
            <Link to="/signin" className="text-emerald-400 text-sm hover:underline">Go to Sign In</Link>
          </div>
        )}

        {status === 'success' && (
          <div className="text-center space-y-4">
            <CheckCircle2 className="h-12 w-12 text-emerald-400 mx-auto" />
            <h1 className="font-display text-xl font-bold text-white">Welcome aboard!</h1>
            <p className="text-gray-400 text-sm">Redirecting you to your dashboard...</p>
          </div>
        )}

        {(status === 'ready' || status === 'accepting') && invite && (
          <form onSubmit={handleAccept} className="space-y-5">
            <div className="text-center mb-2">
              <h1 className="font-display text-xl font-bold text-white mb-1">
                You're invited to join {invite.company}
              </h1>
              <p className="text-gray-400 text-sm">
                {invite.email} · Role: {invite.role}
              </p>
            </div>

            {!invite.account_exists && (
              <div>
                <label className="block text-sm font-medium text-gray-300 mb-1">Create a password</label>
                <div className="relative">
                  <Lock className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-gray-500" />
                  <input
                    type="password" required minLength={8} value={password}
                    onChange={e => setPassword(e.target.value)}
                    className="w-full rounded-xl border border-white/10 bg-surface-3 pl-10 pr-4 py-3 text-white placeholder-gray-500 outline-none focus:border-emerald-500/50 transition-colors"
                    placeholder="At least 8 characters"
                  />
                </div>
              </div>
            )}

            {error && <p className="text-rose-400 text-sm">{error}</p>}

            <button
              type="submit" disabled={status === 'accepting'}
              className="w-full h-11 rounded-xl bg-emerald-600 hover:bg-emerald-700 text-white font-semibold transition-all disabled:opacity-50"
            >
              {status === 'accepting' ? 'Joining...' : invite.account_exists ? 'Join Team' : 'Create Account & Join'}
            </button>
          </form>
        )}
      </motion.div>
    </div>
  );
}
