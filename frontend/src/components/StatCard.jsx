import React from 'react';
import { motion } from 'framer-motion';
import { Link } from 'react-router-dom';
import { useCountUp, useIntersection } from '../lib/hooks';
import { fadeUp } from '../lib/animations';
import MagneticCard from './MagneticCard';

export default function StatCard({ title, value, icon, trend, trendLabel, delay = 0 }) {
  const { ref: inViewRef, inView } = useIntersection(0.1);
  const countRef = useCountUp(value, 1.8, inView);

  const isPositive = trend > 0;
  const trendColor = isPositive ? 'text-emerald-400' : 'text-amber';

  return (
    <motion.div
      ref={inViewRef}
      initial="initial"
      animate={inView ? 'animate' : 'initial'}
      variants={{ ...fadeUp, animate: { ...fadeUp.animate, transition: { ...fadeUp.animate.transition, delay } } }}
      className="h-full w-full"
    >
      <Link to="/candidates" className="block h-full cursor-pointer group">
        <MagneticCard className="flex h-full flex-col justify-between p-6 transition-all group-hover:border-violet/40 group-hover:bg-surface-3">
          <div className="flex items-start justify-between">
            <h3 className="text-sm font-medium text-text-2 group-hover:text-text-1 transition-colors">{title}</h3>
            <div className="rounded-lg bg-surface-3 p-2 text-emerald-500 group-hover:bg-emerald-500 group-hover:text-bg transition-all">
              {icon}
            </div>
          </div>

          <div className="mt-4">
            <div className="flex items-baseline gap-2">
              <span
                ref={countRef}
                className="font-display text-4xl font-bold tracking-tight text-white"
              >
                0
              </span>
            </div>
            
            <div className="mt-2 flex items-center text-sm">
              <span className={`font-medium ${trendColor}`}>
                {isPositive ? '+' : ''}{trend}%
              </span>
              <span className="ml-2 text-text-3 group-hover:text-text-2 transition-colors">{trendLabel}</span>
            </div>
          </div>
        </MagneticCard>
      </Link>
    </motion.div>
  );
}
