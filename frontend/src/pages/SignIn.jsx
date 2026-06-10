import React, { useState } from 'react';
import { motion } from 'framer-motion';
import { Link, useNavigate, useLocation } from 'react-router-dom';
import MagneticCard from '../components/MagneticCard';
import { useAuth } from '../context/AuthContext';
import ConstellationBackground from '../components/ConstellationBackground';

export default function SignIn() {
  const navigate = useNavigate();
  const location = useLocation();
  const { login, register, loading } = useAuth();
  const [isRegistering, setIsRegistering] = useState(false);
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [role, setRole] = useState('Recruiter');

  React.useEffect(() => {
    setEmail('');
    setPassword('');
  }, [isRegistering]);

  const handleAuth = async (e) => {
    e.preventDefault();
    try {
      if (isRegistering) {
        await register(email, password, role);
        setIsRegistering(false);
      } else {
        await login(email, password);
        const state = location.state;
        navigate(state?.from?.pathname || '/dashboard', { replace: true });
      }
    } catch (err) {
      console.error(err);
    }
  };

  return (
    <div className="relative flex min-h-screen items-center justify-center p-6 bg-bg overflow-hidden">
      {/* Animated premium constellation network */}
      <ConstellationBackground />
      
      <motion.div
        initial={{ opacity: 0, scale: 0.95, y: 20 }}
        animate={{ opacity: 1, scale: 1, y: 0 }}
        transition={{ duration: 0.6, ease: [0.16, 1, 0.3, 1] }}
        className="w-full max-w-md relative z-10"
      >
        <MagneticCard className="p-8 sm:p-10 border border-white/10 bg-surface/30 backdrop-blur-xl shadow-glow-indigo/10" maxTilt={5}>
          <div className="mb-8 text-center">
            <h1 className="mb-2 font-display text-3xl font-bold tracking-tight text-white">
              {isRegistering ? 'Create Account' : 'Welcome back'}
            </h1>
            <p className="text-text-2">
              {isRegistering ? 'Sign up for a HireIQ recruiter account' : 'Sign in to your HireIQ account'}
            </p>
          </div>

          <form onSubmit={handleAuth} className="space-y-5">
            <div>
              <label htmlFor="email" className="mb-1 block text-sm font-medium text-text-1">Email address</label>
              <input
                type="email"
                id="email"
                required
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                className="w-full rounded-xl border border-border bg-surface-3 p-3 text-white placeholder-text-3 outline-none transition-colors focus:border-violet focus:ring-1 focus:ring-violet"
              />
            </div>
            
            {isRegistering && (
              <div>
                <label htmlFor="role" className="mb-1 block text-sm font-medium text-text-1">Recruiter Role</label>
                <select
                  id="role"
                  value={role}
                  onChange={(e) => setRole(e.target.value)}
                  className="w-full rounded-xl border border-border bg-surface-3 p-3 text-white placeholder-text-3 outline-none transition-colors focus:border-violet focus:ring-1 focus:ring-violet"
                >
                  <option value="Recruiter">Recruiter</option>
                  <option value="Hiring Manager">Hiring Manager</option>
                  <option value="Talent Acquisition">Talent Acquisition</option>
                  <option value="Admin">Admin</option>
                </select>
              </div>
            )}

            <div>
              <div className="mb-1 flex items-center justify-between">
                <label htmlFor="password" className="block text-sm font-medium text-text-1">Password</label>
                {!isRegistering && (
                  <Link to="/forgot-password" className="text-xs text-violet hover:text-emerald-400 transition-colors">Forgot password?</Link>
                )}
              </div>
              <input
                type="password"
                id="password"
                required
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder={isRegistering ? "Min. 8 chars, 1 letter, 1 number" : ""}
                className="w-full rounded-xl border border-border bg-surface-3 p-3 text-white placeholder-text-3 outline-none transition-colors focus:border-violet focus:ring-1 focus:ring-violet"
              />
            </div>

            <button
              type="submit"
              disabled={loading}
              className="group relative mt-2 flex w-full h-12 items-center justify-center overflow-hidden rounded-xl bg-white font-medium text-bg transition-transform hover:scale-[1.02] disabled:opacity-50 disabled:pointer-events-none"
            >
              <span className="absolute inset-0 bg-gradient-to-r from-emerald-500 to-cyan-500 opacity-0 transition-opacity group-hover:opacity-100" />
              <span className="relative z-10 group-hover:text-bg">
                {loading ? 'Processing...' : isRegistering ? 'Sign Up' : 'Sign In'}
              </span>
            </button>
          </form>

          <div className="mt-8 text-center text-sm text-text-2">
            {isRegistering ? (
              <>
                Already have an account?{' '}
                <button
                  onClick={() => setIsRegistering(false)}
                  className="font-medium text-white hover:text-mint transition-colors bg-transparent border-none p-0 cursor-pointer"
                >
                  Sign In
                </button>
              </>
            ) : (
              <>
                Don't have an account?{' '}
                <button
                  onClick={() => setIsRegistering(true)}
                  className="font-medium text-white hover:text-mint transition-colors bg-transparent border-none p-0 cursor-pointer"
                >
                  Sign Up
                </button>
              </>
            )}
          </div>


        </MagneticCard>
      </motion.div>
    </div>
  );
}
