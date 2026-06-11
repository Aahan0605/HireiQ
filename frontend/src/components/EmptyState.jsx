import React from 'react';
import { motion } from 'framer-motion';
import * as Icons from 'lucide-react';

export default function EmptyState({
  icon = 'FileQuestion',
  title = 'No data available',
  description = 'There are no items to display at the moment.',
  actionLabel,
  onAction,
}) {
  const IconComponent = Icons[icon] || Icons.FileQuestion;

  return (
    <motion.div
      initial={{ opacity: 0, y: 15 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.4, ease: 'easeOut' }}
      className="flex flex-col items-center justify-center p-12 text-center rounded-2xl border border-white/5 bg-[#131324]/40 backdrop-blur-xl shadow-xl max-w-lg mx-auto my-8"
    >
      <div className="relative mb-6">
        {/* Glow effect */}
        <div className="absolute inset-0 rounded-full bg-violet/20 blur-[20px]" />
        <div className="relative flex h-20 w-20 items-center justify-center rounded-2xl bg-white/[0.03] border border-white/10 text-violet shadow-2xl">
          <IconComponent className="h-10 w-10 text-violet" />
        </div>
      </div>

      <h3 className="text-xl font-bold text-white mb-2 tracking-tight">
        {title}
      </h3>
      <p className="text-gray-400 text-sm leading-relaxed max-w-sm mb-8">
        {description}
      </p>

      {actionLabel && onAction && (
        <motion.button
          whileHover={{ scale: 1.02 }}
          whileTap={{ scale: 0.98 }}
          onClick={onAction}
          className="px-6 py-3 rounded-xl bg-gradient-to-r from-violet to-[#8b5cf6] font-bold text-white shadow-lg shadow-violet/20 hover:shadow-violet/30 transition-all duration-200 text-sm"
        >
          {actionLabel}
        </motion.button>
      )}
    </motion.div>
  );
}
