import React, { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { X } from 'lucide-react';

const AlgorithmLegend = () => {
  const [isOpen, setIsOpen] = useState(false);

  const algorithms = [
    { name: 'Max-Heap', use: 'Candidate Ranking', complexity: 'O(n log n)', icon: '📊' },
    { name: 'TF-IDF', use: 'JD Matching', complexity: 'O(n·m)', icon: '📄' },
    { name: 'BFS', use: 'Skill Gap Analysis', complexity: 'O(V+E)', icon: '🌐' },
    { name: '0/1 Knapsack', use: 'Optimal Shortlisting', complexity: 'O(n·W)', icon: '💼' },
    { name: 'Greedy', use: 'Interview Scheduling', complexity: 'O(n log n)', icon: '📅' },
    { name: 'Merge Sort', use: 'Score Re-ranking', complexity: 'O(n log n)', icon: '🔄' },
  ];

  return (
    <div className="fixed bottom-6 right-6 z-50">
      <AnimatePresence>
        {isOpen && (
          <motion.div
            initial={{ opacity: 0, scale: 0.9, y: 20 }}
            animate={{ opacity: 1, scale: 1, y: 0 }}
            exit={{ opacity: 0, scale: 0.9, y: 20 }}
            className="absolute bottom-16 right-0 w-80 bg-black/70 backdrop-blur-md border border-emerald-500/30 rounded-2xl p-4 mb-2"
          >
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-green-400 font-mono text-sm font-bold">🧠 Active Algorithms</h3>
              <button
                onClick={() => setIsOpen(false)}
                className="text-gray-400 hover:text-white"
              >
                <X className="h-4 w-4" />
              </button>
            </div>

            <div className="space-y-3 max-h-96 overflow-y-auto">
              {algorithms.map((algo, idx) => (
                <motion.div
                  key={idx}
                  initial={{ opacity: 0, x: -10 }}
                  animate={{ opacity: 1, x: 0 }}
                  transition={{ delay: idx * 0.05 }}
                  className="text-xs font-mono text-green-400 border-l-2 border-green-500/30 pl-3 py-1"
                >
                  <div className="flex items-center gap-2">
                    <span>{algo.icon}</span>
                    <span className="font-bold">{algo.name}</span>
                  </div>
                  <div className="text-gray-400 text-xs mt-0.5">
                    → {algo.use} &nbsp;&nbsp; {algo.complexity}
                  </div>
                </motion.div>
              ))}
            </div>
          </motion.div>
        )}
      </AnimatePresence>

      <motion.button
        whileHover={{ scale: 1.1 }}
        whileTap={{ scale: 0.95 }}
        onClick={() => setIsOpen(!isOpen)}
        className="w-12 h-12 rounded-full bg-gradient-to-br from-emerald-600 to-emerald-800 text-white shadow-lg hover:shadow-emerald-500/50 flex items-center justify-center text-xl font-bold border border-emerald-400/30"
      >
        🧠
      </motion.button>
    </div>
  );
};

export default AlgorithmLegend;
