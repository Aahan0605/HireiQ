import React, { useState, useEffect } from 'react';
import { useSearchParams, useNavigate, Link } from 'react-router-dom';
import { Lock, CheckCircle2, XCircle, Loader2 } from 'lucide-react';
import ConstellationBackground from '../components/ConstellationBackground';
import { validatePassword } from '../utils/passwordValidation';
import { validatePassword } from '../utils/passwordValidation';

export default function ResetPassword() {
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();
  const token = searchParams.get('token');

  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [loading, setLoading] = useState(false);
  const [status, setStatus] = useState('idle'); // idle | success | error
  const [message, setMessage] = useState('');

  useEffect(() => {
    if (!token) {
      setStatus('error');
      setMessage('No password reset token was found.');
    }
  }, [token]);

  const handleSubmit = async (e) => {
    e.preventDefault();
    const val = validatePassword(password);
    if (!val.valid) {
      setStatus('error');
      setMessage(`Password must contain: ${val.errors.join(', ')}.`);
      return;
    }
    if (password !== confirmPassword) {
      setStatus('error');
      setMessage('Passwords do not match.');
      return;
    }
    setLoading(true);
    setStatus('idle');
    setMessage('');
    try {
      const res = await fetch('/api/v1/auth/reset-password', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ token, new_password: password }),
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || 'Password reset failed');
      setStatus('success');
      setMessage(data.message || 'Password reset successfully!');
      setTimeout(() => {
        navigate('/signin');
      }, 2000);
    } catch (err) {
      setStatus('error');
      setMessage(err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="relative min-h-screen flex items-center justify-center p-6 bg-bg overflow-hidden">
      <ConstellationBackground />
      <div className="w-full max-w-md relative z-10 bg-surface/30 backdrop-blur-xl border border-white/10 rounded-2xl p-8 sm:p-10">
        {status === 'success' ? (
          <div className="text-center space-y-4">
            <div className="mx-auto h-14 w-14 rounded-2xl bg-emerald-500/10 flex items-center justify-center">
              <CheckCircle2 className="h-7 w-7 text-emerald-400 animate-pulse" />
            </div>
            <h1 className="font-display text-2xl font-bold text-white">Reset Complete</h1>
            <p className="text-gray-400 text-sm">{message}</p>
            <p className="text-xs text-gray-500 animate-pulse">Redirecting you to Sign In...</p>
          </div>
        ) : (
          <>
            <div className="mb-8">
              <h1 className="font-display text-2xl font-bold text-white mb-1">Set new password</h1>
              <p className="text-gray-400 text-sm">Please choose a secure password for your account.</p>
            </div>
            <form onSubmit={handleSubmit} className="space-y-5">
              <div>
                <label className="block text-sm font-medium text-gray-300 mb-1">New Password</label>
                <div className="relative">
                  <Lock className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-gray-500" />
                  <input
                    type="password"
                    required
                    minLength={8}
                    value={password}
                    onChange={e => setPassword(e.target.value)}
                    placeholder="Min. 8 chars, 1 letter, 1 number"
                    className="w-full rounded-xl border border-white/10 bg-surface-3 pl-10 pr-4 py-3 text-white placeholder-gray-500 outline-none focus:border-emerald-500/50 transition-colors"
                  />
                </div>
              </div>
              
              <div>
                <label className="block text-sm font-medium text-gray-300 mb-1">Confirm New Password</label>
                <div className="relative">
                  <Lock className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-gray-500" />
                  <input
                    type="password"
                    required
                    value={confirmPassword}
                    onChange={e => setConfirmPassword(e.target.value)}
                    placeholder="Confirm new password"
                    className="w-full rounded-xl border border-white/10 bg-surface-3 pl-10 pr-4 py-3 text-white placeholder-gray-500 outline-none focus:border-emerald-500/50 transition-colors"
                  />
                </div>
              </div>

              {status === 'error' && (
                <div className="flex items-center gap-2 text-rose-400 text-sm border border-rose-500/20 bg-rose-500/5 rounded-xl p-3">
                  <XCircle className="h-4 w-4 flex-shrink-0" />
                  <span>{message}</span>
                </div>
              )}

              <button
                type="submit"
                disabled={loading || !token}
                className="w-full h-11 rounded-xl bg-emerald-600 hover:bg-emerald-700 text-white font-semibold transition-all disabled:opacity-50 flex items-center justify-center gap-2"
              >
                {loading && <Loader2 className="h-4 w-4 animate-spin" />}
                {loading ? 'Resetting...' : 'Reset Password'}
              </button>
            </form>
          </>
        )}
      </div>
    </div>
  );
}
