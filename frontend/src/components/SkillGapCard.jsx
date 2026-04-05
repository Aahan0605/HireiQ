import React from 'react';
import { motion } from 'framer-motion';
import MagneticCard from './MagneticCard';

const SkillGapCard = ({ candidateSkills = [], role = '' }) => {
  const requiredByRole = {
    frontend: ["React", "TypeScript", "CSS", "Testing", "Webpack"],
    backend: ["Docker", "Kubernetes", "PostgreSQL", "Redis", "CI/CD"],
    ml: ["PyTorch", "MLflow", "Kubernetes", "Statistics", "Spark"],
    fullstack: ["React", "Node.js", "Docker", "PostgreSQL", "TypeScript"],
    default: ["Docker", "Git", "CI/CD", "Testing", "REST APIs"]
  };

  // Detect role category
  const roleKey = role?.toLowerCase()?.includes("frontend") ? "frontend" :
                  role?.toLowerCase()?.includes("backend") ? "backend" :
                  role?.toLowerCase()?.includes("ml") ? "ml" :
                  role?.toLowerCase()?.includes("fullstack") ? "fullstack" : "default";

  const required = requiredByRole[roleKey] || requiredByRole.default;
  const candidateSkillsLower = candidateSkills?.map(s => s?.toLowerCase()) || [];
  const missing = required.filter(s => !candidateSkillsLower.includes(s.toLowerCase()));
  const learningPath = missing.slice(0, 3);

  return (
    <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ duration: 0.5, delay: 0.2 }}>
      <MagneticCard className="p-8 border-border bg-[#13131f]">
        <h3 className="text-xl font-semibold text-white mb-6">Skill Gap Analysis</h3>

        {missing.length === 0 ? (
          <div className="text-center py-8">
            <p className="text-green-400 text-lg font-semibold">✅ All required skills present for this role</p>
          </div>
        ) : (
          <>
            <div className="mb-8">
              <h4 className="text-sm font-semibold text-gray-400 uppercase tracking-wide mb-4">Missing Skills</h4>
              <div className="flex flex-wrap gap-3">
                {missing.map((skill, i) => (
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

            <div>
              <h4 className="text-sm font-semibold text-gray-400 uppercase tracking-wide mb-4">Recommended Learning Path</h4>
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
                        className="text-gray-500"
                      >
                        →
                      </motion.span>
                    )}
                  </React.Fragment>
                ))}
              </div>
            </div>
          </>
        )}
      </MagneticCard>
    </motion.div>
  );
};

export default SkillGapCard;
