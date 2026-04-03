import React from 'react';
import { motion } from 'framer-motion';
import { Search, Filter, ArrowLeft } from 'lucide-react';
import { Link } from 'react-router-dom';
import { staggerContainer, fadeUp } from '../lib/animations';
import MagneticCard from '../components/MagneticCard';
import { getAllCandidates } from '../data/candidates';

export default function Candidates() {
  const [searchTerm, setSearchTerm] = useState('');
  const candidatesList = getAllCandidates();
  
  const filteredCandidates = candidatesList.filter(c => 
    c.name.toLowerCase().includes(searchTerm.toLowerCase()) || 
    c.role.toLowerCase().includes(searchTerm.toLowerCase())
  );

  return (
    <div className="min-h-screen bg-bg p-6 lg:p-12">
      <div className="mx-auto max-w-6xl">
        <div className="mb-8 flex items-center justify-between">
          <Link to="/dashboard" className="inline-flex items-center text-sm font-medium text-text-2 transition-colors hover:text-white">
            <ArrowLeft className="mr-2 h-4 w-4" />
            Back to Dashboard
          </Link>
          <h1 className="font-display text-4xl font-bold text-white">Candidates</h1>
        </div>

        <div className="mb-8 flex flex-col gap-4 sm:flex-row sm:items-center">
          <div className="relative flex-1">
            <Search className="absolute left-4 top-1/2 h-5 w-5 -translate-y-1/2 text-text-3" />
            <input
              type="text"
              placeholder="Search candidates by name, role, or skills..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="w-full rounded-xl border border-border bg-surface-2 py-3 pl-12 pr-4 text-white outline-none focus:border-violet/50"
            />
          </div>
          <button className="inline-flex h-12 items-center rounded-xl border border-border bg-surface-2 px-6 font-medium text-text-1 transition-colors hover:bg-surface-3">
            <Filter className="mr-2 h-4 w-4" />
            Filters
          </button>
        </div>

        <motion.div
          variants={staggerContainer}
          initial="initial"
          animate="animate"
          className="grid gap-4"
        >
          {filteredCandidates.length > 0 ? filteredCandidates.map((c) => (
            <motion.div key={c.id} variants={fadeUp}>
              <Link to={`/candidate/${c.id}`}>
                <MagneticCard className="flex items-center justify-between p-6 transition-all hover:border-violet/40 hover:bg-surface-3" maxTilt={2}>
                  <div className="flex items-center gap-6">
                    <div className="flex h-14 w-14 items-center justify-center rounded-full bg-surface-3 text-xl font-bold text-violet">
                      {c.name.split(' ').map(n => n[0]).join('')}
                    </div>
                    <div>
                      <h3 className="text-xl font-bold text-white">{c.name}</h3>
                      <p className="text-text-2">{c.role}</p>
                    </div>
                  </div>

                  <div className="flex items-center gap-12 text-right">
                    <div className="hidden lg:block">
                      <p className="text-xs uppercase tracking-wider text-text-3">Status</p>
                      <span className={`inline-flex items-center rounded-full px-3 py-1 text-xs font-semibold mt-1 ${
                        c.score >= 90 ? 'bg-mint/10 text-mint' :
                        c.score >= 80 ? 'bg-violet/10 text-violet' :
                        'bg-amber/10 text-amber'
                      }`}>
                        {c.status}
                      </span>
                    </div>
                    
                    <div className="hidden sm:block">
                      <p className="text-xs uppercase tracking-wider text-text-3">Analyzed</p>
                      <p className="text-sm font-medium text-text-1 mt-1">{c.date}</p>
                    </div>

                    <div className="flex flex-col items-end min-w-[80px]">
                      <span className="font-display text-2xl font-bold text-white tracking-tight">{c.score}</span>
                      <span className="text-[10px] uppercase tracking-widest text-text-3">Match Score</span>
                    </div>
                  </div>
                </MagneticCard>
              </Link>
            </motion.div>
          )) : (
            <motion.div variants={fadeUp} className="py-20 text-center">
              <p className="text-text-2 text-lg">No candidates found matching "{searchTerm}"</p>
            </motion.div>
          )}
        </motion.div>
      </div>
    </div>
  );
}
