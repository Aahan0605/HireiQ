import React, { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import { useParams, Link, useNavigate } from 'react-router-dom';
import { ResponsiveContainer, RadarChart, PolarGrid, PolarAngleAxis, Radar } from 'recharts';
import { Mail, Github, Linkedin, MapPin, Award, ArrowLeft, Terminal, Layout, Loader2, Calendar, Download, Star, GitBranch, Activity } from 'lucide-react';
import { toast } from 'sonner';
import MagneticCard from '../components/MagneticCard';
import SkillGapCard from '../components/SkillGapCard';
import { fadeUp, staggerContainer, listItem } from '../lib/animations';
import { getCandidateById } from '../data/candidates';

const API = '/api/v1';

function QACard({ qa, index }) {
  const [showAnswer, setShowAnswer] = useState(false);
  return (
    <div className="p-4 bg-white/5 rounded-xl border border-white/10 flex flex-col gap-3 transition-colors hover:border-violet/40">
      <div className="flex items-center justify-between gap-2">
        <span className="text-xs px-2.5 py-0.5 rounded-full bg-violet/10 text-violet border border-violet/20 font-mono">
          Skill: {qa.skill}
        </span>
        <span className="text-xs text-gray-500">Question #{index + 1}</span>
      </div>
      <p className="text-theme-1 text-sm font-medium leading-relaxed font-sans text-white">
        {qa.question}
      </p>
      <div>
        <button 
          onClick={() => setShowAnswer(!showAnswer)}
          className="text-xs font-semibold text-violet hover:text-fuchsia-400 transition-colors flex items-center gap-1"
        >
          {showAnswer ? "Hide Answer Blueprint" : "Show Answer Blueprint"}
        </button>
        {showAnswer && (
          <motion.div 
            initial={{ opacity: 0, height: 0 }}
            animate={{ opacity: 1, height: "auto" }}
            className="mt-3 p-3.5 bg-black/40 border border-white/10 rounded-lg text-xs text-gray-300 leading-relaxed font-mono"
          >
            <span className="text-emerald-400 font-bold block mb-1">Expected Answer Concept:</span>
            {qa.answer}
          </motion.div>
        )}
      </div>
    </div>
  );
}

export default function CandidateProfile() {
  const { id } = useParams();
  const navigate = useNavigate();
  const [candidate, setCandidate] = useState(null);
  const [loading, setLoading] = useState(true);
  const [isScheduling, setIsScheduling] = useState(false);
  const [jobs, setJobs] = useState([]);
  const [github, setGithub] = useState(null);   // live GitHub stats
  const [githubLoading, setGithubLoading] = useState(false);
  const [qaList, setQaList] = useState([]);
  const [qaLoading, setQaLoading] = useState(false);
  const [syncLoading, setSyncLoading] = useState(false);

  const [blindReview] = useState(() => {
    return localStorage.getItem('hireiq_blind_review') === 'true';
  });

  const [notes, setNotes] = useState(() => {
    try {
      return JSON.parse(localStorage.getItem(`hireiq_notes_${id}`) || '[]');
    } catch {
      return [];
    }
  });
  const [newComment, setNewComment] = useState('');
  const [newRating, setNewRating] = useState(5);
  const [interviewerName, setInterviewerName] = useState('Senior Interviewer');

  const handleAddNote = (e) => {
    e.preventDefault();
    if (!newComment.trim()) return;

    const note = {
      id: Date.now().toString(),
      author: interviewerName,
      comment: newComment,
      rating: newRating,
      date: new Date().toLocaleDateString('en-US', {
        month: 'short',
        day: 'numeric',
        year: 'numeric',
        hour: '2-digit',
        minute: '2-digit'
      })
    };

    const updated = [note, ...notes];
    setNotes(updated);
    localStorage.setItem(`hireiq_notes_${id}`, JSON.stringify(updated));
    setNewComment('');
    toast.success('Feedback recorded!');
  };

  const handleDeleteNote = (noteId) => {
    const updated = notes.filter(n => n.id !== noteId);
    setNotes(updated);
    localStorage.setItem(`hireiq_notes_${id}`, JSON.stringify(updated));
    toast.success('Feedback deleted.');
  };

  // Fetch open jobs for Recommended Roles section
  useEffect(() => {
    fetch(`${API}/jobs`)
      .then(r => r.ok ? r.json() : [])
      .then(data => setJobs(Array.isArray(data) ? data.filter(j => j.status === 'Open') : []))
      .catch(() => {});
  }, []);

  // Fetch candidate details dynamically
  useEffect(() => {
    setLoading(true);
    fetch(`${API}/candidates/${id}`)
      .then(r => {
        if (!r.ok) throw new Error("Not found");
        return r.json();
      })
      .then(data => {
        setCandidate(data);
        if (data.qa) {
          setQaList(data.qa);
        }
      })
      .catch(() => {
        // fallback to local data
        const localCand = getCandidateById(id) || getCandidateById('1');
        setCandidate(localCand);
        if (localCand?.qa) {
          setQaList(localCand.qa);
        }
      })
      .finally(() => setLoading(false));
  }, [id]);

  // Fetch GitHub stats once we know the candidate's github handle
  useEffect(() => {
    if (!candidate?.github) return;
    setGithubLoading(true);
    fetch(`${API}/candidates/github/${encodeURIComponent(candidate.github)}`)
      .then(r => r.ok ? r.json() : null)
      .then(data => { if (data && !data.error) setGithub(data); })
      .catch(() => {})
      .finally(() => setGithubLoading(false));
  }, [candidate?.github]);

  if (loading) {
    return (
      <div className="min-h-screen bg-[#0d0d1a] flex items-center justify-center">
        <div className="text-center">
          <Loader2 className="h-8 w-8 text-emerald-400 animate-spin mx-auto mb-4" />
          <p className="text-gray-400 text-sm">Loading candidate profile data...</p>
        </div>
      </div>
    );
  }

  if (!candidate) {
    return (
      <div className="min-h-screen bg-[#0d0d1a] flex items-center justify-center">
        <div className="text-center">
          <p className="text-5xl mb-4">🔍</p>
          <h1 className="text-2xl font-bold text-white mb-3">Candidate Not Found</h1>
          <Link to="/candidates" className="text-emerald-400 hover:text-emerald-300 text-sm">← Back to Candidates</Link>
        </div>
      </div>
    );
  }

  const baseScore = candidate?.baseScore || candidate?.score || 75;

  const insights = candidate?.insights || {
    completeness_score: 80,
    ats_score: 75,
    career_progression: 'Mid-Level Professional',
    strengths: [
      'Strong coding signal with active GitHub',
      'Solid Next.js/React experience',
      'Broad core library experience'
    ],
    weaknesses: [
      'No formal cloud vendor certifications listed',
      'Limited CI/CD automation experience details'
    ],
    concerns: [
      'Short average tenure (< 1.5 years per role)'
    ]
  };

  // Build radar data from skills
  let radarData = candidate.radarData || candidate.radar_data;
  if (!radarData) {
    const topSkills = (candidate?.skills || []).slice(0, 6);
    radarData = topSkills.map(skill => ({
      subject: skill?.substring(0, 12) || 'Skill',
      A: Math.min(100, baseScore + ((skill?.length || 0) % 15) - 5),
      fullMark: 100,
    }));
    const defaults = ['Problem Solving', 'Architecture', 'Testing', 'DevOps', 'Agile', 'System Design'];
    while (radarData.length < 6) {
      radarData.push({ subject: defaults[radarData.length] || `Skill ${radarData.length}`, A: baseScore - 5, fullMark: 100 });
    }
  }

  // Trust score based on how many profile fields are filled
  const verifiedCount = [candidate.email, candidate.github, candidate.linkedin, candidate.location].filter(Boolean).length;
  const trustLabel = verifiedCount >= 4 ? 'High' : verifiedCount >= 2 ? 'Medium' : 'Low';
  const trustColor = trustLabel === 'High'
    ? 'text-green-400 bg-green-500/10 border-green-500/20'
    : trustLabel === 'Medium'
    ? 'text-yellow-400 bg-yellow-500/10 border-yellow-500/20'
    : 'text-red-400 bg-red-500/10 border-red-500/20';

  // Compute top 3 job matches client-side using skill overlap
  const candidateSkillsLower = (candidate.skills || []).map(s => s.toLowerCase());
  const topJobs = jobs
    .map(job => {
      const jobSkills = (job.required_skills || '').split(',').map(s => s.trim().toLowerCase());
      const matched = jobSkills.filter(s => candidateSkillsLower.includes(s));
      const matchScore = jobSkills.length > 0 ? Math.round((matched.length / jobSkills.length) * 100) : 0;
      return { ...job, matchScore };
    })
    .sort((a, b) => b.matchScore - a.matchScore)
    .slice(0, 3);

  const handleSchedule = () => {
    setIsScheduling(true);
    const promise = new Promise(resolve => setTimeout(resolve, 2000));
    toast.promise(promise, {
      loading: 'Scheduling interview...',
      success: () => { setIsScheduling(false); return `Interview scheduled! Email sent to ${candidate.email}`; },
      error: 'Failed to schedule.',
    });
  };

  const handleDownload = () => {
    const lines = [
      'HireIQ Candidate Report',
      '========================',
      `Name:     ${candidate.name}`,
      `Role:     ${candidate.role}`,
      `Email:    ${candidate.email}`,
      `Location: ${candidate.location}`,
      `Score:    ${candidate.score}%`,
      `Trust:    ${trustLabel}`,
      '',
      'Summary:',
      candidate.summary || 'N/A',
      '',
      `Skills: ${(candidate.skills || []).join(', ')}`,
      '',
      'Experience:',
      ...(candidate.experience || []).map(e => `  - ${e.title} @ ${e.company} (${e.date})`),
    ];
    const blob = new Blob([lines.join('\n')], { type: 'text/plain' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `${(candidate.name || 'candidate').replace(/\s+/g, '-')}-report.txt`;
    a.click();
    URL.revokeObjectURL(url);
  };

  // Feature B Q&A trigger
  const handleGenerateQA = async () => {
    setQaLoading(true);
    try {
      const res = await fetch(`${API}/candidates/${id}/generate-qa`, {
        method: 'POST',
      });
      if (!res.ok) throw new Error('API Error');
      const data = await res.json();
      setQaList(data.qa);
      toast.success('Interview Q&A generated successfully!');
    } catch (e) {
      toast.error('Failed to generate interview Q&A. Using mock questions.');
      setQaList([
        {
          skill: "System Design",
          question: "How would you design a scalable B2B SaaS architecture using Node.js/Python and PostgreSQL?",
          answer: "You would use database partitioning/sharding, connection pooling with PgBouncer, caching with Redis, asynchronous worker queues (Celery/BullMQ) for heavy operations, and keep routes modular with clean APIs."
        },
        {
          skill: "Security",
          question: "How do you implement secure multi-tenant isolation in a SaaS application?",
          answer: "Use Row Level Security (RLS) on PostgreSQL tables with a tenant_id context set per request, or separate schemas/databases depending on the enterprise compliance needs, combined with JWT token claims verification."
        }
      ]);
    } finally {
      setQaLoading(false);
    }
  };

  // Feature D Webhook Sync
  const handleGithubSync = async () => {
    setSyncLoading(true);
    try {
      const res = await fetch(`${API}/candidates/${id}/webhook/github-sync`, {
        method: 'POST',
      });
      if (!res.ok) {
        const err = await res.json();
        throw new Error(err.detail || 'Sync failed');
      }
      const data = await res.json();
      toast.success(data.message || 'Profile synced via Webhook!');
      
      setCandidate(prev => ({
        ...prev,
        score: data.overall_score,
        status: data.overall_score > 90 ? 'Strong Match' : 'Match',
      }));

      if (data.signals) {
        setGithub(prev => ({
          ...prev,
          total_repos: data.signals.public_repos,
          total_stars: data.signals.stars,
          commit_frequency_per_week: data.signals.commit_frequency,
          score: data.github_score,
        }));
      }
    } catch (e) {
      toast.error(e.message || 'Failed to sync GitHub profile via webhook.');
    } finally {
      setSyncLoading(false);
    }
  };

  return (
    <motion.div initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.2 }}
      className="min-h-screen bg-[#0d0d1a] p-6 lg:p-12">
      <div className="mx-auto max-w-6xl">

        <div className="mb-8">
          <Link to="/candidates" className="inline-flex items-center text-sm font-medium text-gray-400 hover:text-white transition-colors">
            <ArrowLeft className="mr-2 h-4 w-4" /> Back to Candidates
          </Link>
        </div>

        <motion.div variants={staggerContainer} initial="initial" animate="animate" className="grid gap-8 lg:grid-cols-3">

          {/* ── Left Sidebar ── */}
          <motion.div variants={fadeUp} className="flex flex-col gap-6">
            <MagneticCard className="p-8 border-black/10 dark:border-white/10 bg-[#13131f]">
              <div className="mb-6 flex flex-col items-center">
                <div className="mb-4 flex h-24 w-24 items-center justify-center rounded-full bg-gradient-to-br from-emerald-500 to-mint text-3xl font-bold text-[#0d0d1a] shadow-glow-mint">
                  {blindReview ? '🕵️' : (candidate?.name?.split(' ')?.map(n => n?.[0])?.join('') || 'C')}
                </div>
                <h1 className="text-2xl font-bold text-white text-center">
                  {blindReview 
                    ? `Candidate ${candidate?.id ? candidate.id.substring(0, 4).toUpperCase() : 'XXXX'}` 
                    : candidate?.name}
                </h1>
                <p className="text-gray-400 text-sm text-center">{candidate?.role}</p>
                <div className="mt-3 inline-flex items-center gap-1.5 rounded-full bg-emerald-400/10 px-3 py-1 text-sm font-medium text-emerald-400">
                  <Award className="h-4 w-4" /> {candidate?.score}% Match
                </div>
                <div className={`mt-2 inline-flex items-center gap-1 rounded-full border px-3 py-1 text-xs font-medium ${trustColor}`}>
                  Trust: {trustLabel}
                </div>
              </div>

              <div className="space-y-3 border-t border-black/10 dark:border-white/10 pt-5 text-sm">
                {blindReview ? (
                  <div className="text-xs text-red-400 bg-red-500/10 border border-red-500/20 rounded-lg p-3 text-center">
                    🔒 Blind mode is enabled. Contact details, location, and social links are hidden to minimize bias.
                  </div>
                ) : (
                  <>
                    {candidate?.location && <div className="flex items-center gap-3 text-gray-300"><MapPin className="h-4 w-4 text-gray-500" />{candidate.location}</div>}
                    {candidate?.email    && <div className="flex items-center gap-3 text-gray-300"><Mail className="h-4 w-4 text-gray-500" />{candidate.email}</div>}
                    {candidate?.github   && <div className="flex items-center gap-3 text-gray-300"><Github className="h-4 w-4 text-gray-500" />{candidate.github}</div>}
                    {candidate?.linkedin && <div className="flex items-center gap-3 text-gray-300"><Linkedin className="h-4 w-4 text-gray-500" />{candidate.linkedin}</div>}
                  </>
                )}
              </div>

              <div className="mt-6 flex flex-col gap-2">
                <button onClick={handleSchedule} disabled={isScheduling}
                  className="w-full rounded-xl bg-white px-4 py-3 font-semibold text-[#0d0d1a] transition-all hover:scale-[1.02] active:scale-[0.98] disabled:opacity-50 flex items-center justify-center gap-2">
                  {isScheduling
                    ? <><Loader2 className="h-4 w-4 animate-spin" />Scheduling...</>
                    : <><Calendar className="h-4 w-4" />Schedule Interview</>}
                </button>
                <button onClick={handleDownload}
                  className="w-full rounded-xl border border-black/10 dark:border-white/10 bg-white/5 px-4 py-2.5 text-sm font-medium text-gray-300 hover:bg-white/10 transition-all flex items-center justify-center gap-2">
                  <Download className="h-4 w-4" /> Download Report
                </button>
              </div>
            </MagneticCard>

            {/* Skill radar */}
            <MagneticCard className="p-6 border-black/10 dark:border-white/10 bg-[#13131f]">
              <h3 className="mb-4 text-lg font-semibold text-white">Skill Analysis</h3>
              {candidate?.skills?.length > 0 ? (
                <div className="mb-5 flex flex-wrap gap-2">
                  {candidate.skills.map((skill, i) => (
                    <span key={i} className="inline-flex items-center rounded-full bg-green-500/10 px-3 py-1 text-xs font-medium text-green-400 border border-green-500/20">
                      {skill}
                    </span>
                  ))}
                </div>
              ) : <p className="text-gray-500 text-sm mb-4">No skills extracted.</p>}
              <div className="h-56 w-full">
                <ResponsiveContainer width="100%" height="100%">
                  <RadarChart cx="50%" cy="50%" outerRadius="70%" data={radarData}>
                    <PolarGrid stroke="rgba(255,255,255,0.1)" />
                    <PolarAngleAxis dataKey="subject" tick={{ fill: '#9494B0', fontSize: 11 }} />
                    <Radar name={candidate?.name} dataKey="A" stroke="#9D74FF" fill="#9D74FF" fillOpacity={0.4} />
                  </RadarChart>
                </ResponsiveContainer>
              </div>
            </MagneticCard>

            {/* GitHub Stats Card */}
            <MagneticCard className="p-6 border-black/10 dark:border-white/10 bg-[#13131f]">
              <div className="flex items-center justify-between mb-4 gap-2">
                <h3 className="text-base font-semibold text-white flex items-center gap-1.5">
                  <Github className="h-4 w-4 text-cyan-400 animate-pulse" /> Webhook Sync
                </h3>
                <button 
                  onClick={handleGithubSync}
                  disabled={syncLoading || !candidate?.github}
                  className="text-[10px] px-2 py-1 rounded bg-cyan-500/10 hover:bg-cyan-500/25 text-cyan-400 border border-cyan-500/20 transition-all active:scale-95 disabled:opacity-50 flex items-center gap-1"
                >
                  {syncLoading ? <Loader2 className="h-3 w-3 animate-spin" /> : <Activity className="h-3 w-3" />}
                  Sync Live
                </button>
              </div>

              {!candidate?.github ? (
                <p className="text-gray-500 text-xs">No GitHub handle on profile</p>
              ) : githubLoading ? (
                <div className="space-y-2">
                  {Array(4).fill(0).map((_, i) => (
                    <div key={i} className="h-8 rounded-lg bg-white/5 animate-pulse" />
                  ))}
                </div>
              ) : github ? (
                <div className="space-y-3">
                  {/* Score bar */}
                  <div className="flex items-center justify-between">
                    <span className="text-gray-400 text-xs">GitHub Score</span>
                    <span className={`text-sm font-bold ${
                      github.score >= 70 ? 'text-green-400' :
                      github.score >= 40 ? 'text-yellow-400' : 'text-red-400'
                    }`}>{github.score}/100</span>
                  </div>
                  <div className="w-full bg-white/5 rounded-full h-1.5">
                    <div className="h-1.5 rounded-full bg-gradient-to-r from-emerald-500 to-cyan-400 transition-all"
                      style={{ width: `${github.score}%` }} />
                  </div>

                  {/* Stats grid */}
                  <div className="grid grid-cols-2 gap-2 mt-3">
                    {[
                      { icon: <GitBranch className="h-3 w-3" />, label: 'Repos',   value: github.total_repos },
                      { icon: <Star className="h-3 w-3" />,      label: 'Stars',   value: github.total_stars },
                      { icon: <Activity className="h-3 w-3" />,  label: 'Commits/wk', value: github.commit_frequency_per_week },
                      { icon: <Github className="h-3 w-3" />,    label: 'PRs',     value: github.open_source_prs_estimate },
                    ].map(stat => (
                      <div key={stat.label} className="flex items-center gap-2 bg-white/5 rounded-lg px-3 py-2">
                        <span className="text-gray-500">{stat.icon}</span>
                        <div>
                          <p className="text-[#9D74FF] text-sm font-semibold">{stat.value ?? '—'}</p>
                          <p className="text-gray-500 text-xs">{stat.label}</p>
                        </div>
                      </div>
                    ))}
                  </div>

                  {/* Languages */}
                  {github.languages?.length > 0 && (
                    <div className="mt-2">
                      <p className="text-gray-500 text-xs mb-1.5">Languages</p>
                      <div className="flex flex-wrap gap-1">
                        {github.languages.slice(0, 6).map(lang => (
                          <span key={lang} className="text-xs px-2 py-0.5 rounded-full bg-cyan-500/10 text-cyan-400 border border-cyan-500/20">
                            {lang}
                          </span>
                        ))}
                      </div>
                    </div>
                  )}

                  {/* Bio */}
                  {github.raw_bio && (
                    <p className="text-gray-500 text-xs italic mt-1 line-clamp-2">"{github.raw_bio}"</p>
                  )}
                </div>
              ) : (
                <p className="text-gray-500 text-xs">GitHub profile not found or private</p>
              )}
            </MagneticCard>
          </motion.div>

          {/* ── Main Content ── */}
          <motion.div variants={fadeUp} className="flex flex-col gap-6 lg:col-span-2">

            {/* Resume Intelligence & ATS Analysis */}
            <MagneticCard className="p-8 border-black/10 dark:border-white/10 bg-[#13131f] relative overflow-hidden">
              <div className="absolute top-0 right-0 p-4 opacity-5 pointer-events-none">
                <Terminal size={120} className="text-violet" />
              </div>
              <h3 className="mb-1 text-xl font-semibold text-white flex items-center gap-2">
                ⚡ ATS Resume Intelligence
              </h3>
              <p className="text-xs text-gray-500 mb-6">Automated parse completeness and layout compliance analysis</p>

              {/* Progress Gauges */}
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 mb-6">
                <div className="bg-white/5 border border-white/5 rounded-xl p-4 flex items-center justify-between">
                  <div>
                    <span className="text-xs text-gray-400 block">Completeness Score</span>
                    <span className="text-lg font-bold text-white tabular-nums">{insights.completeness_score}%</span>
                  </div>
                  <div className="w-16 h-1.5 bg-white/10 rounded-full overflow-hidden">
                    <div className="h-full bg-emerald-500 rounded-full" style={{ width: `${insights.completeness_score}%` }} />
                  </div>
                </div>
                <div className="bg-white/5 border border-white/5 rounded-xl p-4 flex items-center justify-between">
                  <div>
                    <span className="text-xs text-gray-400 block">ATS Optimization Score</span>
                    <span className="text-lg font-bold text-white tabular-nums">{insights.ats_score}%</span>
                  </div>
                  <div className="w-16 h-1.5 bg-white/10 rounded-full overflow-hidden">
                    <div className="h-full bg-violet rounded-full" style={{ width: `${insights.ats_score}%` }} />
                  </div>
                </div>
              </div>

              {/* Career Progression & Strengths/Weaknesses */}
              <div className="space-y-4">
                <div className="flex items-center gap-2">
                  <span className="text-xs text-gray-400">Career Tier:</span>
                  <span className="text-xs font-semibold px-2.5 py-0.5 rounded-full bg-violet/10 text-violet border border-violet/20">
                    {insights.career_progression}
                  </span>
                </div>

                <div className="grid grid-cols-1 sm:grid-cols-2 gap-6 pt-2">
                  <div>
                    <h4 className="text-xs font-bold text-emerald-400 uppercase tracking-wider mb-2">Key Strengths</h4>
                    <ul className="space-y-1.5 text-xs text-gray-300">
                      {insights.strengths?.map((item, idx) => (
                        <li key={idx} className="flex items-start gap-1.5">
                          <span className="text-emerald-400">✓</span> {item}
                        </li>
                      ))}
                    </ul>
                  </div>
                  <div>
                    <h4 className="text-xs font-bold text-yellow-400 uppercase tracking-wider mb-2">Development Gaps</h4>
                    <ul className="space-y-1.5 text-xs text-gray-300">
                      {insights.weaknesses?.map((item, idx) => (
                        <li key={idx} className="flex items-start gap-1.5">
                          <span className="text-yellow-400">⚠</span> {item}
                        </li>
                      ))}
                    </ul>
                  </div>
                </div>

                {insights.concerns?.length > 0 && (
                  <div className="pt-2 border-t border-white/5">
                    <h4 className="text-xs font-bold text-red-400 uppercase tracking-wider mb-2">Potential Concerns</h4>
                    <ul className="space-y-1.5 text-xs text-gray-300">
                      {insights.concerns.map((item, idx) => (
                        <li key={idx} className="flex items-start gap-1.5">
                          <span className="text-red-400">🚩</span> {item}
                        </li>
                      ))}
                    </ul>
                  </div>
                )}
              </div>
            </MagneticCard>

            <MagneticCard className="p-8 border-black/10 dark:border-white/10 bg-[#13131f]">
              <h3 className="mb-3 text-xl font-semibold text-white">AI Summary</h3>
              <p className="text-gray-400 leading-relaxed text-sm">{candidate?.summary || 'No summary available.'}</p>
            </MagneticCard>

            {/* Feature B: AI-Driven Technical Interview Q&A */}
            <MagneticCard className="p-8 border-black/10 dark:border-white/10 bg-[#13131f]">
              <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 mb-6">
                <div>
                  <h3 className="text-xl font-semibold text-white flex items-center gap-2">
                    🧠 AI Technical Q&A Generator
                  </h3>
                  <p className="text-xs text-gray-500 mt-1">Generates customized, deep technical interview questions testing skill gaps</p>
                </div>
                <button 
                  onClick={handleGenerateQA} 
                  disabled={qaLoading}
                  className="rounded-xl bg-gradient-to-r from-violet to-fuchsia-600 hover:from-violet/90 hover:to-fuchsia-600/90 text-white font-semibold px-4 py-2.5 text-sm flex items-center justify-center gap-2 transition-all active:scale-95 disabled:opacity-50 shadow-lg shadow-violet/20"
                >
                  {qaLoading ? (
                    <><Loader2 className="h-4 w-4 animate-spin" /> Analyzing Gaps...</>
                  ) : (
                    <>Run AI Assessment</>
                  )}
                </button>
              </div>

              {qaList.length > 0 ? (
                <div className="space-y-4">
                  {qaList.map((qa, index) => (
                    <QACard key={index} qa={qa} index={index} />
                  ))}
                </div>
              ) : (
                <div className="text-center py-10 border border-dashed border-white/10 rounded-xl bg-white/5">
                  <p className="text-2xl mb-2">📋</p>
                  <p className="text-gray-400 text-sm">No Q&A generated yet. Click above to run the AI skill gap interview generator.</p>
                </div>
              )}
            </MagneticCard>

            <MagneticCard className="p-8 border-black/10 dark:border-white/10 bg-[#13131f]">
              <h3 className="mb-6 text-xl font-semibold text-white">Experience Timeline</h3>
              <div className="relative border-l border-black/10 dark:border-white/10 pl-6 ml-3 space-y-8">
                {candidate?.experience?.length > 0 ? candidate.experience.map((exp, i) => (
                  <motion.div variants={listItem} key={i} className="relative">
                    <span className="absolute -left-10 flex h-8 w-8 items-center justify-center rounded-full border-4 border-[#13131f] bg-[#1e1e2f] text-emerald-400">
                      {i === 0 ? <Layout className="h-4 w-4" /> : <Terminal className="h-4 w-4" />}
                    </span>
                    <h4 className="text-base font-bold text-white mb-1">{exp?.title}</h4>
                    <div className="flex items-center gap-2 mb-2">
                      <span className="text-sm font-medium text-emerald-500">{exp?.company}</span>
                      <span className="text-gray-600">•</span>
                      <span className="text-sm text-gray-400">{exp?.date}</span>
                    </div>
                    <p className="text-gray-500 text-sm">{exp?.description}</p>
                  </motion.div>
                )) : <p className="text-gray-500 text-sm">No experience data available.</p>}
              </div>
            </MagneticCard>

            {/* Team Interviewer Feedback Section */}
            <MagneticCard className="p-8 border-black/10 dark:border-white/10 bg-[#13131f]">
              <h3 className="mb-4 text-xl font-semibold text-white flex items-center gap-2">
                💬 Team Interviewer Feedback
              </h3>
              <p className="text-xs text-gray-500 mb-6">Collaborative rating and screening notes from interviewers</p>

              {/* Form to add note */}
              <form onSubmit={handleAddNote} className="mb-6 space-y-4 p-4 rounded-xl border border-white/5 bg-white/5">
                <div className="flex gap-4">
                  <div className="flex-1">
                    <label className="block text-xs font-semibold text-gray-400 mb-1">Interviewer Name</label>
                    <input 
                      type="text" 
                      value={interviewerName} 
                      onChange={e => setInterviewerName(e.target.value)}
                      placeholder="Your Name / Role"
                      className="w-full text-xs rounded-lg border border-white/10 bg-[#0d0d1a] px-3 py-2 text-white outline-none focus:border-violet/40 transition-colors"
                      required
                    />
                  </div>
                  <div>
                    <label className="block text-xs font-semibold text-gray-400 mb-1">Rating</label>
                    <select 
                      value={newRating} 
                      onChange={e => setNewRating(Number(e.target.value))}
                      className="rounded-lg border border-white/10 bg-[#0d0d1a] px-3 py-2 text-xs text-white outline-none focus:border-violet/40 transition-colors cursor-pointer"
                    >
                      <option value={5}>⭐️⭐️⭐️⭐️⭐️ (5/5)</option>
                      <option value={4}>⭐️⭐️⭐️⭐️ (4/5)</option>
                      <option value={3}>⭐️⭐️⭐️ (3/5)</option>
                      <option value={2}>⭐️⭐️ (2/5)</option>
                      <option value={1}>⭐️ (1/5)</option>
                    </select>
                  </div>
                </div>
                <div>
                  <label className="block text-xs font-semibold text-gray-400 mb-1">Interview Comments / Scorecard Notes</label>
                  <textarea 
                    value={newComment} 
                    onChange={e => setNewComment(e.target.value)}
                    placeholder="Describe candidate technical execution, communication, and overall culture fit..."
                    rows={3}
                    className="w-full text-xs rounded-lg border border-white/10 bg-[#0d0d1a] p-3 text-white outline-none focus:border-violet/40 transition-colors resize-none"
                    required
                  />
                </div>
                <button 
                  type="submit"
                  className="rounded-lg bg-emerald-600 hover:bg-emerald-700 text-white font-semibold px-4 py-2 text-xs transition-all active:scale-95 flex items-center gap-1.5"
                >
                  Save Feedback
                </button>
              </form>

              {/* Feed timeline */}
              {notes.length > 0 ? (
                <div className="space-y-4">
                  {notes.map(note => (
                    <div key={note.id} className="p-4 border border-white/5 bg-white/[0.02] rounded-xl flex flex-col gap-2 relative group">
                      <div className="flex items-center justify-between gap-2">
                        <div>
                          <span className="text-xs font-bold text-white">{note.author}</span>
                          <span className="text-gray-500 text-[10px] ml-2">{note.date}</span>
                        </div>
                        <div className="flex items-center gap-2">
                          <span className="text-yellow-400 text-xs">{'★'.repeat(note.rating)}{'☆'.repeat(5 - note.rating)}</span>
                          <button 
                            type="button"
                            onClick={() => handleDeleteNote(note.id)}
                            className="opacity-0 group-hover:opacity-100 text-red-400 hover:text-red-300 text-xs transition-opacity p-1 ml-1"
                            title="Delete note"
                          >
                            ✕
                          </button>
                        </div>
                      </div>
                      <p className="text-gray-300 text-xs leading-relaxed font-sans whitespace-pre-wrap">{note.comment}</p>
                    </div>
                  ))}
                </div>
              ) : (
                <div className="text-center py-6 border border-dashed border-white/5 rounded-xl bg-white/[0.01]">
                  <p className="text-gray-500 text-xs">No feedback logged yet. Log notes using the form above.</p>
                </div>
              )}
            </MagneticCard>

            <MagneticCard className="p-8 border-black/10 dark:border-white/10 bg-[#13131f]">
              <h3 className="mb-5 text-xl font-semibold text-white">Top Skills Matched</h3>
              <div className="space-y-3">
                {(candidate?.skills?.slice(0, 4) || []).map((skill, i) => {
                  const conf = [90, 85, 80, 75][i];
                  return (
                    <div key={skill}>
                      <div className="flex justify-between text-xs text-gray-400 mb-1">
                        <span>{skill}</span><span>{conf}%</span>
                      </div>
                      <div className="w-full bg-white/5 rounded-full h-1.5">
                        <div className="h-1.5 rounded-full bg-gradient-to-r from-green-400 to-cyan-400" style={{ width: `${conf}%` }} />
                      </div>
                    </div>
                  );
                })}
              </div>
            </MagneticCard>
          </motion.div>
        </motion.div>

        {/* Skill Gap */}
        <motion.div variants={fadeUp} className="mt-8">
          <SkillGapCard candidateSkills={candidate?.skills} role={candidate?.role} />
        </motion.div>

        {/* ── Recommended Roles ── */}
        <motion.div variants={fadeUp} className="mt-6">
          <div className="bg-[#13131f] border border-black/10 dark:border-white/10 rounded-2xl p-6">
            <h3 className="text-white font-semibold text-lg mb-1">Recommended Roles</h3>
            <p className="text-gray-500 text-xs mb-4">Based on skill overlap with open positions</p>
            <div className="space-y-3">
              {topJobs.map(job => (
                <div key={job.id} className="flex items-center justify-between p-3 bg-white/5 rounded-xl">
                  <div>
                    <p className="text-white text-sm font-medium">{job.title}</p>
                    <p className="text-gray-400 text-xs">{job.department} · {job.location}</p>
                  </div>
                  <div className="flex items-center gap-2">
                    <span className={`text-xs px-2.5 py-1 rounded-full font-medium ${
                      job.matchScore >= 70 ? 'bg-green-500/20 text-green-400' :
                      job.matchScore >= 40 ? 'bg-yellow-500/20 text-yellow-400' :
                                             'bg-red-500/20 text-red-400'
                    }`}>
                      {job.matchScore}% match
                    </span>
                    <button onClick={() => navigate(`/jobs/${job.id}/matches`)}
                      className="text-xs text-emerald-400 hover:text-emerald-300 transition-colors">
                      View Job →
                    </button>
                  </div>
                </div>
              ))}
              {topJobs.length === 0 && (
                <p className="text-gray-500 text-xs italic">No open positions available</p>
              )}
            </div>
          </div>
        </motion.div>

      </div>
    </motion.div>
  );
}
