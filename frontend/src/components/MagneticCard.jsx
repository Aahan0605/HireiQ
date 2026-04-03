import React from 'react';
import { motion } from 'framer-motion';
import { useMagneticTilt } from '../lib/hooks';

export default function MagneticCard({ children, className = '', maxTilt = 8, ...props }) {
  const { ref, onMouseMove, onMouseLeave } = useMagneticTilt(maxTilt);

  return (
    <motion.div
      ref={ref}
      onMouseMove={onMouseMove}
      onMouseLeave={onMouseLeave}
      className={`relative overflow-hidden glass-card rounded-2xl ${className}`}
      {...props}
      style={{ transformStyle: 'preserve-3d' }}
    >
      <div className="card-highlight pointer-events-none absolute inset-0 z-10" />
      <div className="relative z-20 h-full w-full">
        {children}
      </div>
    </motion.div>
  );
}
