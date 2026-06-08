import React, { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { X, Cpu } from 'lucide-react';

const AlgorithmLegend = () => {
  const [isOpen, setIsOpen] = useState(false);

  const algorithms = [
    { name: 'Max-Priority Matching Engine (Heap)', use: 'Candidates Ranking', complexity: 'O(n log n)', icon: '📊' },
    { name: 'Contextual Keyword Vectorizer (TF-IDF)', use: 'Semantic Job Fit Match', complexity: 'O(n·m)', icon: '📄' },
    { name: 'Graph-based Skill Gap Mapper (BFS)', use: 'Prerequisite Learning Paths', complexity: 'O(V+E)', icon: '🌐' },
    { name: 'Resource-Constrained Budget Allocator (Knapsack DP)', use: 'ROI-optimal Shortlists', complexity: 'O(n·W)', icon: '💼' },
    { name: 'Greedy Schedule Conflict Resolver (Activity Selection)', use: 'Interview Time Slots Optimisation', complexity: 'O(n log n)', icon: '📅' },
    { name: 'Divide-&-Conquer Score Merger (Merge Sort)', use: 'Real-time Rank Delta Analysis', complexity: 'O(n log n)', icon: '🔄' },
  ];

  return (
    <div className="fixed bottom-6 right-6 z-50">
      <AnimatePresence>
        {isOpen && (
          <motion.div
            initial={{ opacity: 0, scale: 0.9, y: 20 }}
            animate={{ opacity: 1, scale: 1, y: 0 }}
            exit={{ opacity: 0, scale: 0.9, y: 20 }}
            className="absolute bottom-16 right-0 w-80 bg-black/80 backdrop-blur-md border border-cyan-500/30 rounded-2xl p-4 mb-2 shadow-2xl"
          >
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-cyan-400 font-mono text-sm font-bold flex items-center gap-1.5">
                <Cpu className="h-4 w-4 text-cyan-400 animate-spin" /> Analytical Core Pipelines
              </h3>
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
                  className="text-xs font-mono text-cyan-400 border-l-2 border-cyan-500/30 pl-3 py-1.5"
                >
                  <div className="flex items-center gap-2">
                    <span>{algo.icon}</span>
                    <span className="font-bold text-white">{algo.name}</span>
                  </div>
                  <div className="text-gray-400 text-xs mt-0.5">
                    → {algo.use} &nbsp;&nbsp; <span className="text-gray-500">[{algo.complexity}]</span>
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
        className="w-12 h-12 rounded-full bg-gradient-to-br from-cyan-600 to-cyan-800 text-white shadow-lg hover:shadow-cyan-500/50 flex items-center justify-center text-xl font-bold border border-cyan-400/30"
      >
        <Cpu className="h-5 w-5 text-white" />
      </motion.button>
    </div>
  );
};

export default AlgorithmLegend;
