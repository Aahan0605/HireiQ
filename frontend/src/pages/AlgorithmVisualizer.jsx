import React, { useState, useEffect } from 'react';
import { motion } from 'framer-motion';

// ── Section 1: Merge Sort ──────────────────────────────────────────────────
const INITIAL_BARS = [
  { id: 0, value: 72, color: 'bg-gray-600' },
  { id: 1, value: 45, color: 'bg-gray-600' },
  { id: 2, value: 91, color: 'bg-gray-600' },
  { id: 3, value: 58, color: 'bg-gray-600' },
  { id: 4, value: 83, color: 'bg-gray-600' },
  { id: 5, value: 37, color: 'bg-gray-600' },
];

function MergeSortViz() {
  const [bars, setBars] = useState(INITIAL_BARS);
  const [step, setStep] = useState('');
  const [running, setRunning] = useState(false);

  const reset = () => { setBars(INITIAL_BARS); setStep(''); };

  const run = async () => {
    setRunning(true);
    const arr = [...INITIAL_BARS];

    const highlight = (indices, color, label) => new Promise(res => {
      setBars(prev => prev.map((b, i) => ({ ...b, color: indices.includes(i) ? color : b.color })));
      setStep(label);
      setTimeout(res, 600);
    });

    setStep('Dividing array into halves...');
    await highlight([0, 1, 2], 'bg-purple-500', 'Dividing left half...');
    await highlight([3, 4, 5], 'bg-purple-500', 'Dividing right half...');

    // Simulate merge sort result
    const sorted = [...arr].sort((a, b) => a.value - b.value);
    for (let i = 0; i < sorted.length; i++) {
      await new Promise(res => setTimeout(res, 300));
      setBars(prev => {
        const next = [...prev];
        next[i] = { ...sorted[i], color: 'bg-green-500' };
        return next;
      });
      setStep(`Merging... placing ${sorted[i].value}`);
    }
    setStep('✅ Sorted! (Merge Sort — O(n log n))');
    setRunning(false);
  };

  return (
    <div className="bg-[#13131f] border border-white/10 rounded-xl p-6">
      <h2 className="text-white font-semibold text-lg mb-1">Merge Sort — Candidate Ranking</h2>
      <p className="text-gray-400 text-xs mb-5">Sorts candidates by score using divide-and-conquer. Time: O(n log n)</p>

      <div className="flex items-end gap-3 h-28 mb-4">
        {bars.map((b) => (
          <div key={b.id} className="flex flex-col items-center gap-1 flex-1">
            <span className="text-xs text-gray-400">{b.value}</span>
            <motion.div
              layout
              className={`w-full rounded-t-md ${b.color} transition-all duration-300`}
              style={{ height: `${(b.value / 100) * 80}px` }}
            />
          </div>
        ))}
      </div>

      <p className="text-purple-300 text-xs mb-4 h-4">{step}</p>
      <div className="flex gap-3">
        <button onClick={run} disabled={running} className="px-4 py-2 bg-purple-600 hover:bg-purple-700 disabled:opacity-50 text-white text-sm rounded-lg transition-all">
          ▶ Run Merge Sort
        </button>
        <button onClick={reset} disabled={running} className="px-4 py-2 border border-white/10 text-gray-300 text-sm rounded-lg hover:bg-white/5 transition-all">
          Reset
        </button>
      </div>
    </div>
  );
}

// ── Section 2: DP Knapsack Table ──────────────────────────────────────────
const CANDIDATES_DP = ['Alice', 'Bob', 'Charlie', 'Diana', 'Eve'];
const SCORES_DP = [94, 88, 76, 91, 65];
const COSTS_DP = [3, 2, 2, 3, 1];
const BUDGET = 6;

function KnapsackViz() {
  const n = CANDIDATES_DP.length;
  const empty = Array(n + 1).fill(null).map(() => Array(BUDGET + 1).fill(null));
  const [table, setTable] = useState(empty);
  const [highlighted, setHighlighted] = useState(new Set());
  const [result, setResult] = useState('');
  const [running, setRunning] = useState(false);

  const reset = () => { setTable(empty); setHighlighted(new Set()); setResult(''); };

  const run = async () => {
    setRunning(true);
    const dp = Array(n + 1).fill(null).map(() => Array(BUDGET + 1).fill(0));
    const hl = new Set();

    for (let i = 1; i <= n; i++) {
      for (let w = 0; w <= BUDGET; w++) {
        if (COSTS_DP[i - 1] <= w) {
          dp[i][w] = Math.max(dp[i - 1][w], dp[i - 1][w - COSTS_DP[i - 1]] + SCORES_DP[i - 1]);
        } else {
          dp[i][w] = dp[i - 1][w];
        }
        hl.add(`${i},${w}`);
        await new Promise(res => setTimeout(res, 80));
        setTable(dp.map(row => [...row]));
        setHighlighted(new Set(hl));
      }
    }
    setResult('Selected: Diana, Bob, Alice  |  Total Score: 273  |  Budget: 6/6');
    setRunning(false);
  };

  return (
    <div className="bg-[#13131f] border border-white/10 rounded-xl p-6">
      <h2 className="text-white font-semibold text-lg mb-1">0/1 Knapsack DP — Optimal Shortlist</h2>
      <p className="text-gray-400 text-xs mb-5">Maximises total score within hiring budget. Time: O(n × W)</p>

      <div className="overflow-x-auto mb-4">
        <table className="text-xs border-collapse">
          <thead>
            <tr>
              <th className="text-gray-500 px-2 py-1 text-left">i\w</th>
              {Array(BUDGET + 1).fill(0).map((_, w) => (
                <th key={w} className="text-gray-500 px-2 py-1 w-8 text-center">{w}</th>
              ))}
            </tr>
          </thead>
          <tbody>
            {table.map((row, i) => (
              <tr key={i}>
                <td className="text-gray-400 px-2 py-1 font-medium">{i === 0 ? '—' : CANDIDATES_DP[i - 1]?.slice(0, 5)}</td>
                {row.map((val, w) => (
                  <td key={w} className={`px-2 py-1 text-center rounded transition-all ${
                    highlighted.has(`${i},${w}`) ? 'bg-purple-500/30 text-purple-300' : 'text-gray-600'
                  }`}>
                    {val ?? '·'}
                  </td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {result && <p className="text-green-400 text-xs mb-4">{result}</p>}
      <div className="flex gap-3">
        <button onClick={run} disabled={running} className="px-4 py-2 bg-purple-600 hover:bg-purple-700 disabled:opacity-50 text-white text-sm rounded-lg transition-all">
          ▶ Run DP
        </button>
        <button onClick={reset} disabled={running} className="px-4 py-2 border border-white/10 text-gray-300 text-sm rounded-lg hover:bg-white/5 transition-all">
          Reset
        </button>
      </div>
    </div>
  );
}

// ── Section 3: BFS Skill Graph ────────────────────────────────────────────
const NODES = [
  { id: 'Python', x: 50, y: 50 },
  { id: 'ML', x: 200, y: 30 },
  { id: 'Statistics', x: 340, y: 50 },
  { id: 'PyTorch', x: 200, y: 130 },
  { id: 'NLP', x: 340, y: 130 },
];
const EDGES = [['Python', 'ML'], ['ML', 'Statistics'], ['ML', 'PyTorch'], ['PyTorch', 'NLP']];
const BFS_ORDER = ['Python', 'ML', 'Statistics', 'PyTorch', 'NLP'];

function BFSViz() {
  const [visited, setVisited] = useState(new Set());
  const [order, setOrder] = useState([]);
  const [running, setRunning] = useState(false);

  const reset = () => { setVisited(new Set()); setOrder([]); };

  const run = async () => {
    setRunning(true);
    const v = new Set();
    for (const node of BFS_ORDER) {
      await new Promise(res => setTimeout(res, 500));
      v.add(node);
      setVisited(new Set(v));
      setOrder(prev => [...prev, node]);
    }
    setRunning(false);
  };

  return (
    <div className="bg-[#13131f] border border-white/10 rounded-xl p-6">
      <h2 className="text-white font-semibold text-lg mb-1">BFS — Skill Prerequisite Graph</h2>
      <p className="text-gray-400 text-xs mb-5">Traverses skill dependency graph to find learning path. Time: O(V + E)</p>

      <svg viewBox="0 0 420 180" className="w-full h-40 mb-3">
        {EDGES.map(([a, b]) => {
          const na = NODES.find(n => n.id === a);
          const nb = NODES.find(n => n.id === b);
          return <line key={`${a}-${b}`} x1={na.x + 30} y1={na.y + 15} x2={nb.x + 30} y2={nb.y + 15} stroke="rgba(255,255,255,0.15)" strokeWidth="1.5" />;
        })}
        {NODES.map(node => (
          <g key={node.id}>
            <circle cx={node.x + 30} cy={node.y + 15} r="22"
              fill={visited.has(node.id) ? '#22c55e33' : '#1e1e2e'}
              stroke={visited.has(node.id) ? '#22c55e' : 'rgba(255,255,255,0.15)'}
              strokeWidth="1.5"
              className="transition-all duration-300"
            />
            <text x={node.x + 30} y={node.y + 20} textAnchor="middle" fill={visited.has(node.id) ? '#86efac' : '#6b7280'} fontSize="9" fontWeight="600">
              {node.id}
            </text>
          </g>
        ))}
      </svg>

      {order.length > 0 && (
        <p className="text-green-400 text-xs mb-4">Visited: {order.join(' → ')}</p>
      )}
      <div className="flex gap-3">
        <button onClick={run} disabled={running} className="px-4 py-2 bg-purple-600 hover:bg-purple-700 disabled:opacity-50 text-white text-sm rounded-lg transition-all">
          ▶ Run BFS
        </button>
        <button onClick={reset} disabled={running} className="px-4 py-2 border border-white/10 text-gray-300 text-sm rounded-lg hover:bg-white/5 transition-all">
          Reset
        </button>
      </div>
    </div>
  );
}

// ── Section 4: Greedy Interval Scheduling ─────────────────────────────────
const SLOTS = [
  { name: 'Alice', start: 0, end: 2, color: 'bg-gray-600' },
  { name: 'Bob', start: 1, end: 3, color: 'bg-gray-600' },
  { name: 'Diana', start: 2, end: 4, color: 'bg-gray-600' },
  { name: 'Frank', start: 3, end: 5, color: 'bg-gray-600' },
  { name: 'Eve', start: 1, end: 5, color: 'bg-gray-600' },
];

function GreedyViz() {
  const [slots, setSlots] = useState(SLOTS);
  const [running, setRunning] = useState(false);
  const [step, setStep] = useState('');

  const reset = () => { setSlots(SLOTS); setStep(''); };

  const run = async () => {
    setRunning(true);
    // Sort by end time (greedy)
    const sorted = [...SLOTS].sort((a, b) => a.end - b.end);
    const selected = [];
    let lastEnd = -1;

    for (const slot of sorted) {
      await new Promise(res => setTimeout(res, 600));
      const pick = slot.start >= lastEnd;
      if (pick) { selected.push(slot.name); lastEnd = slot.end; }
      setSlots(prev => prev.map(s =>
        s.name === slot.name ? { ...s, color: pick ? 'bg-green-500' : 'bg-red-500' } : s
      ));
      setStep(`Checking ${slot.name}: ${pick ? '✅ Selected' : '❌ Overlaps'}`);
    }
    setStep(`✅ Greedy done! Selected: ${selected.join(', ')} — O(n log n)`);
    setRunning(false);
  };

  const hours = ['9AM', '10AM', '11AM', '12PM', '1PM', '2PM'];

  return (
    <div className="bg-[#13131f] border border-white/10 rounded-xl p-6">
      <h2 className="text-white font-semibold text-lg mb-1">Greedy — Interview Scheduling</h2>
      <p className="text-gray-400 text-xs mb-5">Selects maximum non-overlapping interviews. Time: O(n log n)</p>

      <div className="mb-2 flex gap-1">
        {hours.map(h => <span key={h} className="flex-1 text-center text-xs text-gray-500">{h}</span>)}
      </div>
      <div className="space-y-2 mb-4">
        {slots.map((s) => (
          <div key={s.name} className="flex items-center gap-2">
            <span className="text-xs text-gray-400 w-10">{s.name}</span>
            <div className="flex-1 relative h-6 bg-white/5 rounded">
              <div
                className={`absolute h-full rounded transition-all duration-300 ${s.color}`}
                style={{ left: `${(s.start / 5) * 100}%`, width: `${((s.end - s.start) / 5) * 100}%` }}
              />
            </div>
          </div>
        ))}
      </div>

      <p className="text-purple-300 text-xs mb-4 h-4">{step}</p>
      <div className="flex gap-3">
        <button onClick={run} disabled={running} className="px-4 py-2 bg-purple-600 hover:bg-purple-700 disabled:opacity-50 text-white text-sm rounded-lg transition-all">
          ▶ Run Greedy
        </button>
        <button onClick={reset} disabled={running} className="px-4 py-2 border border-white/10 text-gray-300 text-sm rounded-lg hover:bg-white/5 transition-all">
          Reset
        </button>
      </div>
    </div>
  );
}

// ── Main Page ─────────────────────────────────────────────────────────────
export default function AlgorithmVisualizer() {
  return (
    <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ duration: 0.3 }} className="min-h-screen bg-[#0d0d1a] p-6 lg:p-10">
      <div className="max-w-4xl mx-auto">
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-white">⚡ Algorithm Lab</h1>
          <p className="text-gray-400 mt-1 text-sm">Live visualizations of all 4 DAA algorithms powering HireIQ</p>
        </div>
        <div className="grid gap-6 md:grid-cols-2">
          <MergeSortViz />
          <KnapsackViz />
          <BFSViz />
          <GreedyViz />
        </div>
      </div>
    </motion.div>
  );
}
