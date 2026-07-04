import React, { useEffect, useState } from 'react';
import { motion, AnimatePresence, useReducedMotion } from 'framer-motion';

/**
 * CelebrationBurst — a brief, dependency-free particle burst for "win" moments
 * (e.g. a candidate moved to Hired). Render once near the app root and trigger
 * by bumping the `trigger` key. Honors prefers-reduced-motion (no particles).
 *
 * Usage:
 *   const [celebrate, setCelebrate] = useState(0);
 *   <CelebrationBurst trigger={celebrate} />
 *   // ...later: setCelebrate((n) => n + 1);
 */
const COLORS = ['#4DFFA4', '#22d3ee', '#a78bfa', '#ffffff'];
const PARTICLES = Array.from({ length: 18 }, (_, i) => {
  const angle = (i / 18) * Math.PI * 2;
  const dist = 90 + (i % 4) * 34;
  return {
    id: i,
    x: Math.cos(angle) * dist,
    y: Math.sin(angle) * dist,
    color: COLORS[i % COLORS.length],
    size: 5 + (i % 3) * 3,
  };
});

export default function CelebrationBurst({ trigger }) {
  const prefersReducedMotion = useReducedMotion();
  const [visible, setVisible] = useState(false);

  useEffect(() => {
    if (!trigger) return;
    if (prefersReducedMotion) return;
    setVisible(true);
    const t = setTimeout(() => setVisible(false), 1100);
    return () => clearTimeout(t);
  }, [trigger, prefersReducedMotion]);

  return (
    <div className="pointer-events-none fixed inset-0 z-[100] flex items-center justify-center">
      <AnimatePresence>
        {visible && (
          <div key={trigger} className="relative">
            {PARTICLES.map((p) => (
              <motion.span
                key={p.id}
                className="absolute rounded-full"
                style={{ width: p.size, height: p.size, background: p.color, boxShadow: `0 0 8px ${p.color}` }}
                initial={{ x: 0, y: 0, opacity: 1, scale: 1 }}
                animate={{ x: p.x, y: p.y, opacity: 0, scale: 0.3 }}
                transition={{ duration: 0.9, ease: [0.16, 1, 0.3, 1] }}
              />
            ))}
            <motion.span
              className="absolute rounded-full"
              style={{ width: 40, height: 40, background: 'radial-gradient(circle, rgba(77,255,164,0.5), transparent 70%)', left: -20, top: -20 }}
              initial={{ opacity: 0.8, scale: 0.4 }}
              animate={{ opacity: 0, scale: 2.4 }}
              transition={{ duration: 0.8, ease: 'easeOut' }}
            />
          </div>
        )}
      </AnimatePresence>
    </div>
  );
}
