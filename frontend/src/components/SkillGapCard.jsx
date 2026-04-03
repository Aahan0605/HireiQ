import React from 'react';
import { motion } from 'framer-motion';
import MagneticCard from './MagneticCard';

export default function SkillGapCard() {
  const missingSkills = ["Kubernetes", "ML"];
  const learningPath = ["Python", "ML", "Kubernetes"];

  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      transition={{ duration: 0.5, delay: 0.2 }}
    >
      <MagneticCard className="p-8 border-border bg-surface-2/80">
        {/* Header with Badge */}
        <div className="mb-8 flex items-center justify-between">
          <h3 className="text-xl font-semibold text-white">Skill Gap Analysis</h3>
        </div>

        {/* Missing Skills Section */}
        <div className="mb-8">
          <h4 className="mb-4 text-sm font-semibold text-text-2 uppercase tracking-wide">Missing Skills</h4>
          <div className="flex flex-wrap gap-3">
            {missingSkills.map((skill, i) => (
              <motion.span
                key={i}
                initial={{ scale: 0.8, opacity: 0 }}
                animate={{ scale: 1, opacity: 1 }}
                transition={{ delay: i * 0.1 }}
                className="inline-flex items-center rounded-full bg-red-500/15 px-3 py-1.5 text-sm font-medium text-red-400 border border-red-500/30"
              >
                {skill}
              </motion.span>
            ))}
          </div>
        </div>

        {/* Learning Path Section */}
        <div>
          <h4 className="mb-4 text-sm font-semibold text-text-2 uppercase tracking-wide">Recommended Learning Path</h4>
          <div className="flex flex-wrap items-center gap-2">
            {learningPath.map((skill, i) => (
              <React.Fragment key={i}>
                <motion.span
                  initial={{ scale: 0.8, opacity: 0 }}
                  animate={{ scale: 1, opacity: 1 }}
                  transition={{ delay: i * 0.1 + 0.3 }}
                  className="inline-flex items-center rounded-full bg-blue-500/15 px-3 py-1.5 text-sm font-medium text-blue-400 border border-blue-500/30"
                >
                  {skill}
                </motion.span>
                {i < learningPath.length - 1 && (
                  <motion.span
                    initial={{ opacity: 0 }}
                    animate={{ opacity: 1 }}
                    transition={{ delay: i * 0.1 + 0.4 }}
                    className="text-text-3"
                  >
                    →
                  </motion.span>
                )}
              </React.Fragment>
            ))}
          </div>
        </div>
      </MagneticCard>
    </motion.div>
  );
}
