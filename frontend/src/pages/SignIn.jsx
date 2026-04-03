import React from 'react';
import { motion } from 'framer-motion';
import { Link, useNavigate } from 'react-router-dom';
import MagneticCard from '../components/MagneticCard';

export default function SignIn() {
  const navigate = useNavigate();

  const handleAuth = (e) => {
    e.preventDefault();
    navigate('/dashboard');
  };

  return (
    <div className="relative flex min-h-screen items-center justify-center p-6 bg-bg overflow-hidden">
      {/* Animated nodes and gradients */}
      <div className="pointer-events-none absolute top-[20%] left-[30%] h-64 w-64 rounded-full bg-violet/30 blur-[80px] mix-blend-screen animate-pulseGlow" />
      <div className="pointer-events-none absolute bottom-[10%] right-[30%] h-[300px] w-[300px] rounded-full bg-mint/20 blur-[100px] mix-blend-screen animate-floatSlow" />
      
      {/* Floating physical node */}
      <motion.div
        animate={{ y: [0, -30, 0], x: [0, 20, 0] }}
        transition={{ duration: 8, repeat: Infinity, ease: "easeInOut" }}
        className="absolute top-1/4 right-[25%] hidden lg:flex h-16 w-16 items-center justify-center rounded-2xl border border-white/10 bg-surface shadow-glow-mint backdrop-blur-xl"
      >
        <span className="h-3 w-3 rounded-full bg-mint shadow-glow-mint animate-pulseGlow" />
      </motion.div>

      <motion.div
        initial={{ opacity: 0, scale: 0.95, y: 20 }}
        animate={{ opacity: 1, scale: 1, y: 0 }}
        transition={{ duration: 0.6, ease: [0.16, 1, 0.3, 1] }}
        className="w-full max-w-md relative z-10"
      >
        <MagneticCard className="p-8 sm:p-10 border-border bg-surface-2/80" maxTilt={5}>
          <div className="mb-8 text-center">
            <h1 className="mb-2 font-display text-3xl font-bold tracking-tight text-white">
              Welcome back
            </h1>
            <p className="text-text-2">Sign in to your HireIQ account</p>
          </div>

          <form onSubmit={handleAuth} className="space-y-5">
            <div>
              <label htmlFor="email" className="mb-1 block text-sm font-medium text-text-1">Email address</label>
              <input
                type="email"
                id="email"
                required
                defaultValue="admin@hireiq.demo"
                className="w-full rounded-xl border border-border bg-surface-3 p-3 text-white placeholder-text-3 outline-none transition-colors focus:border-violet focus:ring-1 focus:ring-violet"
              />
            </div>
            <div>
              <div className="mb-1 flex items-center justify-between">
                <label htmlFor="password" className="block text-sm font-medium text-text-1">Password</label>
                <a href="#" className="text-xs text-violet hover:text-white transition-colors">Forgot password?</a>
              </div>
              <input
                type="password"
                id="password"
                required
                defaultValue="password123"
                className="w-full rounded-xl border border-border bg-surface-3 p-3 text-white placeholder-text-3 outline-none transition-colors focus:border-violet focus:ring-1 focus:ring-violet"
              />
            </div>

            <button
              type="submit"
              className="group relative mt-2 flex w-full h-12 items-center justify-center overflow-hidden rounded-xl bg-white font-medium text-bg transition-transform hover:scale-[1.02]"
            >
              <span className="absolute inset-0 bg-gradient-to-r from-mint to-sky opacity-0 transition-opacity group-hover:opacity-100" />
              <span className="relative z-10 group-hover:text-bg">Sign In</span>
            </button>
          </form>

          <div className="mt-8 text-center text-sm text-text-2">
            Don't have an account?{' '}
            <Link to="/" className="font-medium text-white hover:text-mint transition-colors">
              Request access
            </Link>
          </div>
        </MagneticCard>
      </motion.div>
    </div>
  );
}
