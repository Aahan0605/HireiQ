import React, { useState } from 'react';
import { Link } from 'react-router-dom';
import { Mail, ArrowLeft, CheckCircle2 } from 'lucide-react';
import ConstellationBackground from '../components/ConstellationBackground';

export default function ForgotPassword() {
  const [email, setEmail] = useState('');
  const [loading, setLoading] = useState(false);
  const [sent, setSent] = useState(false);
  const [error, setError] = useState('');

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true); setError('');
    try {
      const res = await fetch('/api/v1/auth/forgot-password', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email }),
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || 'Request failed');
      setSent(true);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="relative min-h-screen flex items-center justify-center p-6 bg-bg overflow-hidden">
      <ConstellationBackground />
      <div className="w-full max-w-md relative z-10 bg-surface/30 backdrop-blur-xl border border-white/10 rounded-2xl p-8 sm:p-10">
        {sent ? (
          <div className="text-center space-y-4">
            <div className="mx-auto h-14 w-14 rounded-2xl bg-emerald-500/10 flex items-center justify-center">
              <CheckCircle2 className="h-7 w-7 text-emerald-400" />
            </div>
            <h1 className="font-display text-2xl font-bold text-white">Check your email</h1>
            <p className="text-gray-400 text-sm">If an account exists for {email}, a reset link has been sent.</p>
            <Link to="/signin" className="block mt-4 text-emerald-400 text-sm hover:underline">← Back to Sign In</Link>
          </div>
        ) : (
          <>
            <div className="mb-8">
              <Link to="/signin" className="flex items-center gap-1 text-gray-400 text-sm hover:text-white transition-colors mb-6">
                <ArrowLeft className="h-4 w-4" /> Back to Sign In
              </Link>
              <h1 className="font-display text-2xl font-bold text-white mb-1">Forgot password?</h1>
              <p className="text-gray-400 text-sm">Enter your email and we'll send a reset link.</p>
            </div>
            <form onSubmit={handleSubmit} className="space-y-5">
              <div>
                <label className="block text-sm font-medium text-gray-300 mb-1">Email address</label>
                <div className="relative">
                  <Mail className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-gray-500" />
                  <input type="email" required value={email} onChange={e => setEmail(e.target.value)}
                    className="w-full rounded-xl border border-white/10 bg-surface-3 pl-10 pr-4 py-3 text-white placeholder-gray-500 outline-none focus:border-emerald-500/50 transition-colors" />
                </div>
              </div>
              {error && <p className="text-rose-400 text-sm">{error}</p>}
              <button type="submit" disabled={loading}
                className="w-full h-11 rounded-xl bg-emerald-600 hover:bg-emerald-700 text-white font-semibold transition-all disabled:opacity-50">
                {loading ? 'Sending...' : 'Send Reset Link'}
              </button>
            </form>
          </>
        )}
      </div>
    </div>
  );
}
