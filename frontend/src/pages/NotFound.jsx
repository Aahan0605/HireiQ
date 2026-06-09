import React from 'react';
import { Link } from 'react-router-dom';
import { Compass, MoveLeft } from 'lucide-react';
import ConstellationBackground from '../components/ConstellationBackground';

export default function NotFound() {
  return (
    <div className="relative flex min-h-screen flex-col items-center justify-center overflow-hidden bg-[#0a0a16] px-6 py-12 text-center text-white">
      {/* Dynamic Constellation Underlay */}
      <div className="absolute inset-0 z-0 opacity-40">
        <ConstellationBackground />
      </div>

      {/* Decorative Blur Orbs */}
      <div className="absolute top-1/4 left-1/4 h-72 w-72 rounded-full bg-violet/10 blur-[80px] pointer-events-none" />
      <div className="absolute bottom-1/4 right-1/4 h-80 w-80 rounded-full bg-mint/5 blur-[100px] pointer-events-none" />

      {/* Content Card */}
      <div className="relative z-10 max-w-md rounded-2xl border border-white/10 bg-white/[0.02] p-8 md:p-12 backdrop-blur-xl shadow-2xl">
        <div className="mx-auto mb-6 flex h-16 w-16 items-center justify-center rounded-full border border-violet/30 bg-violet/10 text-violet">
          <Compass className="h-8 w-8 animate-spin-slow" />
        </div>

        <h1 className="font-display text-7xl font-black tracking-tight text-white md:text-8xl">
          404
        </h1>
        
        <h2 className="mt-4 font-display text-xl font-bold tracking-wide text-violet">
          Lost in Space
        </h2>

        <p className="mt-4 text-sm leading-relaxed text-gray-400">
          The candidate, job, or dashboard you are looking for has either relocated or never stepped foot in this sector of the galaxy.
        </p>

        <div className="mt-8 flex flex-col gap-4">
          <Link
            to="/dashboard"
            className="flex items-center justify-center gap-2 rounded-xl bg-violet px-6 py-3 font-semibold text-white shadow-lg transition-all hover:bg-violet-hover hover:scale-[1.02] active:scale-[0.98]"
          >
            Go to Dashboard
          </Link>
          
          <Link
            to="/"
            className="flex items-center justify-center gap-2 rounded-xl border border-white/10 bg-white/5 px-6 py-3 font-semibold text-gray-300 transition-all hover:bg-white/10 hover:text-white"
          >
            <MoveLeft className="h-4 w-4" />
            Back to Home
          </Link>
        </div>
      </div>
    </div>
  );
}
