import React, { useMemo } from 'react';
import { motion } from 'framer-motion';

/**
 * SkillMatchGraph — an animated "candidates → skills → job matches" network.
 *
 * Pure SVG + framer-motion, no WebGL/three.js, so it adds ~0 KB of dependencies
 * and never blocks first paint. When `reducedMotion` is true it renders a static
 * graph (no travelling pulses, no float), satisfying prefers-reduced-motion.
 *
 * The visual maps HireIQ's core pipeline: uploaded candidates connect through
 * extracted skills to the roles they match.
 */

const COLS = {
  candidate: { x: 70, color: '#4DFFA4', label: 'Candidates' },
  skill: { x: 300, color: '#22d3ee', label: 'Skills' },
  job: { x: 530, color: '#a78bfa', label: 'Job Matches' },
};

const candidates = [
  { id: 'c0', y: 55 },
  { id: 'c1', y: 115 },
  { id: 'c2', y: 175 },
];
const skills = [
  { id: 's0', y: 40, label: 'React' },
  { id: 's1', y: 90, label: 'Python' },
  { id: 's2', y: 140, label: 'SQL' },
  { id: 's3', y: 190, label: 'Docker' },
];
const jobs = [
  { id: 'j0', y: 80, label: 'Frontend' },
  { id: 'j1', y: 150, label: 'Backend' },
];

// candidate -> skill and skill -> job connections
const edgesA = [
  ['c0', 's0'], ['c0', 's1'], ['c1', 's1'], ['c1', 's2'],
  ['c2', 's2'], ['c2', 's3'], ['c0', 's2'],
];
const edgesB = [
  ['s0', 'j0'], ['s1', 'j0'], ['s1', 'j1'], ['s2', 'j1'], ['s3', 'j1'],
];

function nodePos(id) {
  if (id.startsWith('c')) return { x: COLS.candidate.x, y: candidates.find((n) => n.id === id).y };
  if (id.startsWith('s')) return { x: COLS.skill.x, y: skills.find((n) => n.id === id).y };
  return { x: COLS.job.x, y: jobs.find((n) => n.id === id).y };
}

export default function SkillMatchGraph({ reducedMotion = false }) {
  // Precompute edge geometry so we don't recompute on every render.
  const paths = useMemo(() => {
    const build = (edges) =>
      edges.map(([from, to], i) => {
        const a = nodePos(from);
        const b = nodePos(to);
        const midX = (a.x + b.x) / 2;
        return {
          key: `${from}-${to}`,
          d: `M ${a.x} ${a.y} C ${midX} ${a.y}, ${midX} ${b.y}, ${b.x} ${b.y}`,
          delay: (i % 5) * 0.6,
        };
      });
    return { a: build(edgesA), b: build(edgesB) };
  }, []);

  const allPaths = [...paths.a, ...paths.b];

  return (
    <svg
      viewBox="0 0 600 230"
      className="w-full h-auto"
      role="img"
      aria-label="Diagram: candidate profiles connecting through extracted skills to matched job roles"
    >
      {/* Column labels */}
      {Object.values(COLS).map((c) => (
        <text
          key={c.label}
          x={c.x}
          y={222}
          textAnchor="middle"
          fill={c.color}
          className="font-mono"
          style={{ fontSize: 11, opacity: 0.75, letterSpacing: 0.5 }}
        >
          {c.label}
        </text>
      ))}

      {/* Edges */}
      {allPaths.map((p) => (
        <path
          key={p.key}
          d={p.d}
          fill="none"
          stroke="rgba(255,255,255,0.12)"
          strokeWidth="1"
        />
      ))}

      {/* Travelling pulses along each edge (skipped for reduced motion).
          Uses native SVG <animateMotion> — reliable, warning-free, zero JS. */}
      {!reducedMotion &&
        allPaths.map((p) => (
          <circle key={`pulse-${p.key}`} r="2.4" fill="#4DFFA4" opacity="0">
            <animateMotion dur="2.4s" repeatCount="indefinite" begin={`${p.delay}s`} path={p.d} />
            <animate
              attributeName="opacity"
              values="0;1;1;0"
              dur="2.4s"
              repeatCount="indefinite"
              begin={`${p.delay}s`}
            />
          </circle>
        ))}

      {/* Candidate nodes */}
      {candidates.map((n) => (
        <Node key={n.id} x={COLS.candidate.x} y={n.y} color={COLS.candidate.color} reducedMotion={reducedMotion} />
      ))}
      {/* Skill nodes (with labels) */}
      {skills.map((n) => (
        <g key={n.id}>
          <Node x={COLS.skill.x} y={n.y} color={COLS.skill.color} reducedMotion={reducedMotion} r={5} />
          <text x={COLS.skill.x + 12} y={n.y + 3.5} fill="rgba(255,255,255,0.6)" style={{ fontSize: 10 }}>
            {n.label}
          </text>
        </g>
      ))}
      {/* Job nodes (with labels) */}
      {jobs.map((n) => (
        <g key={n.id}>
          <Node x={COLS.job.x} y={n.y} color={COLS.job.color} reducedMotion={reducedMotion} r={7} />
          <text x={COLS.job.x - 12} y={n.y + 3.5} textAnchor="end" fill="rgba(255,255,255,0.75)" style={{ fontSize: 10 }}>
            {n.label}
          </text>
        </g>
      ))}
    </svg>
  );
}

function Node({ x, y, color, r = 4, reducedMotion }) {
  return (
    <g>
      {!reducedMotion && (
        <motion.circle
          cx={x}
          cy={y}
          r={r}
          fill={color}
          initial={{ opacity: 0.25, scale: 1 }}
          animate={{ opacity: [0.15, 0.4, 0.15], scale: [1, 2.4, 1] }}
          transition={{ duration: 2.8, repeat: Infinity, ease: 'easeInOut' }}
          style={{ transformOrigin: `${x}px ${y}px` }}
        />
      )}
      <circle cx={x} cy={y} r={r} fill={color} />
      <circle cx={x} cy={y} r={r} fill="none" stroke={color} strokeOpacity="0.4" strokeWidth="1" />
    </g>
  );
}
