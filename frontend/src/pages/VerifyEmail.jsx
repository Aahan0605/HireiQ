import React, { useEffect, useState } from 'react';
import { useSearchParams, Link } from 'react-router-dom';
import { CheckCircle2, XCircle, Loader2 } from 'lucide-react';

export default function VerifyEmail() {
  const [searchParams] = useSearchParams();
  const [status, setStatus] = useState('loading'); // loading | success | error
  const [message, setMessage] = useState('');
  const verificationStarted = React.useRef(false);

  useEffect(() => {
    if (verificationStarted.current) return;
    verificationStarted.current = true;

    const token = searchParams.get('token');
    if (!token) { setStatus('error'); setMessage('No verification token found.'); return; }

    fetch(`/api/v1/auth/verify-email?token=${token}`)
      .then(r => r.json().then(d => ({ ok: r.ok, data: d })))
      .then(({ ok, data }) => {
        setStatus(ok ? 'success' : 'error');
        setMessage(data.message || (ok ? 'Email verified!' : 'Verification failed.'));
      })
      .catch(() => { setStatus('error'); setMessage('Network error. Please try again.'); });
  }, []);

  const icon = status === 'loading' ? <Loader2 className="h-8 w-8 animate-spin text-emerald-400" />
    : status === 'success' ? <CheckCircle2 className="h-8 w-8 text-emerald-400" />
    : <XCircle className="h-8 w-8 text-rose-400" />;

  return (
    <div className="min-h-screen bg-bg flex items-center justify-center p-6">
      <div className="text-center space-y-4 max-w-sm">
        <div className="mx-auto h-16 w-16 rounded-2xl bg-white/5 border border-white/10 flex items-center justify-center">{icon}</div>
        <h1 className="font-display text-2xl font-bold text-white">
          {status === 'loading' ? 'Verifying...' : status === 'success' ? 'Email Verified' : 'Verification Failed'}
        </h1>
        <p className="text-gray-400 text-sm">{message}</p>
        {status !== 'loading' && (
          <Link to="/signin" className="inline-flex h-11 items-center justify-center rounded-xl bg-emerald-600 px-6 text-white text-sm font-semibold hover:bg-emerald-700 transition-all font-mono">
            Sign In
          </Link>
        )}
      </div>
    </div>
  );
}
