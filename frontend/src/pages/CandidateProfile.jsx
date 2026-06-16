import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { useParams, Link, useNavigate } from 'react-router-dom';
import { ResponsiveContainer, RadarChart, PolarGrid, PolarAngleAxis, Radar } from 'recharts';
import { Mail, Github, Linkedin, MapPin, Award, ArrowLeft, Terminal, Layout, Loader2, Calendar, Download, Star, GitBranch, Activity, X, AlertCircle } from 'lucide-react';
import { toast } from 'sonner';
import MagneticCard from '../components/MagneticCard';
import SkillGapCard from '../components/SkillGapCard';
import { fadeUp, staggerContainer, listItem } from '../lib/animations';
import { getCandidateById } from '../data/candidates';
import { apiFetch } from '../lib/apiFetch';

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
  const [error, setError] = useState(null);

  const [showEmailModal, setShowEmailModal] = useState(false);
  const [emailSubject, setEmailSubject] = useState('');
  const [emailBody, setEmailBody] = useState('');
  const [selectedTemplate, setSelectedTemplate] = useState('');

  const emailTemplates = {
    screening: {
      name: "📅 Schedule Technical Screening",
      subject: `Interview Invitation: [Role] - HireIQ Corp`,
      body: `Dear [Name],

Thank you for your interest in the [Role] position at HireIQ Corp.

Our recruitment and engineering teams recently completed a comprehensive review of your profile and resume. We are pleased to inform you that your qualifications, particularly your strong expertise in [Skills], stood out to us. Our HireIQ platform assessed a [Score]% matching score for your profile, indicating exceptional alignment with our core requirements.

We would love to invite you to a 30-minute technical screening call. This call will be a great opportunity for us to learn more about your career journey, discuss your technical experience, and share details about our engineering culture and the [Role] position.

Please let us know your general availability over the next few business days. If you use a scheduling tool or have specific time slots that work best, please feel free to share them.

We look forward to speaking with you soon!

Best regards,
HireIQ Recruitment Team`
    },
    assessment: {
      name: "🚀 Onboarding & Skill Assessment",
      subject: `Technical Assessment Phase: [Role] - HireIQ Corp`,
      body: `Dear [Name],

We appreciate your participation in the initial screening phase for the [Role] position. As the next step in our evaluation process, we would like to invite you to complete a take-home technical assessment.

This evaluation is designed to help us understand:
1. Your approach to system design, scalability, and code architecture.
2. Code quality, organization, and adherence to modern testing best practices.
3. Your practical experience implementing solutions with [Skills].

Please allocate approximately 2 to 3 hours of focused time to complete this exercise. Detailed instructions, repository templates, and submission guidelines are available in your candidate dashboard. We kindly request that you submit your completed solution within the next 3 business days.

If you have any questions or require any adjustments during this phase, please do not hesitate to contact us.

Thank you again for your time and dedication. We look forward to reviewing your solution.

Best regards,
HireIQ Engineering Team`
    },
    rejection: {
      name: "✉️ Polite Rejection",
      subject: `Application Update: [Role] - HireIQ Corp`,
      body: `Dear [Name],

Thank you very much for taking the time to apply for the [Role] position at HireIQ Corp and for participating in our interview process.

Our hiring team was highly impressed by your experience and your technical background, especially your knowledge of [Skills]. We received a large volume of applications from talented professionals, making our decision-making process extremely difficult.

After careful consideration, we have decided to move forward with other candidates whose experience more closely matches the specific specialized requirements of the position at this stage.

We want to thank you again for your patience and transparency throughout this process. We will keep your profile in our talent pool and may reach out if a future position opens up that aligns with your background.

We wish you the absolute best in your future career endeavors and hope our paths cross again.

Best regards,
HireIQ Hiring Team`
    }
  };

  useEffect(() => {
    if (selectedTemplate && emailTemplates[selectedTemplate] && candidate) {
      const templ = emailTemplates[selectedTemplate];
      const rawSkills = candidate.skills;
      const skillsListLocal = Array.isArray(rawSkills)
        ? rawSkills
        : typeof rawSkills === 'string'
        ? rawSkills.split(',').map(s => s.trim())
        : [];
      const skillsStr = skillsListLocal.slice(0, 4).join(', ') || 'software engineering';
      const roleStr = candidate.role || 'Software Engineer';
      const scoreStr = candidate.score || '75';

      const subjectText = templ.subject.replace(/\[Role\]/g, roleStr);
      const bodyText = templ.body
        .replace(/\[Name\]/g, candidate.name || 'Candidate')
        .replace(/\[Role\]/g, roleStr)
        .replace(/\[Score\]/g, scoreStr)
        .replace(/\[Skills\]/g, skillsStr);

      setEmailSubject(subjectText);
      setEmailBody(bodyText);
    }
  }, [selectedTemplate, candidate]);

  const [blindReview] = useState(() => {
    return localStorage.getItem('hireiq_blind_review') === 'true';
  });

  const [notes, setNotes] = useState(() => {
    try {
      const parsed = JSON.parse(localStorage.getItem(`hireiq_notes_${id}`) || '[]');
      return Array.isArray(parsed) ? parsed : [];
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

  const handleSendEmail = (e) => {
    e.preventDefault();
    if (!emailSubject.trim() || !emailBody.trim()) {
      toast.error("Please fill in email subject and message body.");
      return;
    }

    const note = {
      id: Date.now().toString(),
      author: "System (Email Dispatched)",
      comment: `📬 Subject: ${emailSubject}\n\n${emailBody}`,
      rating: 5,
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
    toast.success("Simulated email dispatched successfully!");
    setShowEmailModal(false);
    setSelectedTemplate('');
    setEmailSubject('');
    setEmailBody('');
  };

  // Fetch open jobs for Recommended Roles section
  useEffect(() => {
    apiFetch(`${API}/jobs`)
      .then(r => r.ok ? r.json() : [])
      .then(data => setJobs(Array.isArray(data) ? data.filter(j => j.status === 'Open') : []))
      .catch(() => {});
  }, []);

  // Fetch candidate details dynamically
  useEffect(() => {
    const fetchCandidate = async () => {
      setLoading(true);
      setError(null);
      try {
        const res = await apiFetch(`${API}/candidates/${id}`);
        if (!res.ok) {
          if (res.status === 404) {
            setError('Candidate not found. They may have been deleted.');
          } else {
            setError('Failed to load profile. Please try again.');
          }
          setLoading(false);
          return;
        }
        const data = await res.json();
        setCandidate(data);
        if (data.qa) {
          setQaList(data.qa);
        }
      } catch (err) {
        setError(err.message || 'Failed to load candidate profile.');
        setLoading(false);
      } finally {
        setLoading(false);
      }
    };
    fetchCandidate();
  }, [id]);

  // Fetch GitHub stats once we know the candidate's github handle
  useEffect(() => {
    if (!candidate?.github) return;
    setGithubLoading(true);
    apiFetch(`${API}/candidates/github/${encodeURIComponent(candidate.github)}`)
      .then(r => r.ok ? r.json() : null)
      .then(data => { if (data && !data.error) setGithub(data); })
      .catch(() => {})
      .finally(() => setGithubLoading(false));
  }, [candidate?.github]);

  if (loading) {
    return (
      <div className="min-h-screen bg-page px-6 py-8 sm:px-10 lg:py-12">
        <div className="mx-auto max-w-4xl space-y-6 animate-pulse">
          <div className="h-8 w-48 bg-white/10 rounded-xl" />
          <div className="h-40 rounded-2xl bg-white/5 border border-white/5" />
          <div className="grid grid-cols-3 gap-4">
            {[...Array(3)].map((_, i) => (
              <div key={i} className="h-24 rounded-2xl bg-white/5 border border-white/5" />
            ))}
          </div>
          <div className="h-64 rounded-2xl bg-white/5 border border-white/5" />
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="min-h-screen bg-page flex items-center justify-center px-6">
        <div className="text-center space-y-4 max-w-md">
          <div className="mx-auto h-14 w-14 rounded-2xl bg-rose-500/10 flex items-center justify-center text-rose-400">
            <AlertCircle className="h-7 w-7" />
          </div>
          <h2 className="font-display text-xl font-bold text-theme-1">Profile Unavailable</h2>
          <p className="text-theme-2 text-sm">{error}</p>
          <button
            onClick={() => navigate('/candidates')}
            className="inline-flex h-10 items-center gap-2 rounded-xl bg-emerald-600 hover:bg-emerald-700 px-5 text-white text-sm font-semibold transition-all"
          >
            <ArrowLeft className="h-4 w-4" /> Back to Candidates
          </button>
        </div>
      </div>
    );
  }

  const baseScore = candidate?.baseScore || candidate?.score || 75;

  const skillsList = Array.isArray(candidate?.skills)
    ? candidate.skills
    : typeof candidate?.skills === 'string'
    ? candidate.skills.split(',').map(s => s.trim())
    : [];
  const experienceList = Array.isArray(candidate?.experience) ? candidate.experience : [];

  const defaultInsights = {
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

  const rawInsights = candidate?.insights && typeof candidate.insights === 'object' && !Array.isArray(candidate.insights) ? candidate.insights : {};
  const aiSummary = rawInsights.ai_summary || {};
  const skillConfidence = rawInsights.skill_confidence || {};
  const githubAnalysis = rawInsights.github_analysis || {};
  const matchBreakdown = rawInsights.match_breakdown || {};

  const insights = {
    ...defaultInsights,
    ...rawInsights,
    strengths: Array.isArray(aiSummary.strengths) ? aiSummary.strengths : (Array.isArray(rawInsights.strengths) ? rawInsights.strengths : defaultInsights.strengths),
    weaknesses: Array.isArray(aiSummary.concerns) ? aiSummary.concerns : (Array.isArray(rawInsights.weaknesses) ? rawInsights.weaknesses : defaultInsights.weaknesses),
    concerns: Array.isArray(aiSummary.concerns) ? aiSummary.concerns : (Array.isArray(rawInsights.concerns) ? rawInsights.concerns : defaultInsights.concerns),
    career_progression: aiSummary.career_tier || rawInsights.career_progression || defaultInsights.career_progression,
    executive_summary: aiSummary.executive_summary || rawInsights.executive_summary || candidate?.summary || '',
    interview_focus: aiSummary.interview_focus || rawInsights.interview_focus || [],
    hiring_recommendation: aiSummary.verdict || rawInsights.hiring_recommendation || '',
    ranking_justification: rawInsights.ranking?.justification || rawInsights.ranking_justification || '',
    
    github_details: githubAnalysis,
    linkedin_details: rawInsights.linkedin_details || null,
    skill_confidence: skillConfidence,
    match_breakdown: matchBreakdown,
  };

  // Build radar data from skills
  let radarData = candidate.radarData || candidate.radar_data;
  if (Array.isArray(radarData)) {
    radarData = radarData.filter(item => item && typeof item === 'object');
  }
  if (!radarData || !Array.isArray(radarData) || radarData.length === 0) {
    const topSkills = skillsList.slice(0, 6);
    radarData = topSkills.map(skill => {
      const skillStr = String(skill || '');
      return {
        subject: skillStr.substring(0, 12) || 'Skill',
        A: Math.min(100, baseScore + (skillStr.length % 15) - 5),
        fullMark: 100,
      };
    });
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
  const candidateSkillsLower = skillsList.map(s => s?.toLowerCase() || '');
  const topJobs = jobs
    .map(job => {
      let reqSkillsStr = '';
      if (typeof job.required_skills === 'string') {
        reqSkillsStr = job.required_skills;
      } else if (Array.isArray(job.required_skills)) {
        reqSkillsStr = job.required_skills.join(',');
      }
      const jobSkills = reqSkillsStr.split(',').map(s => s.trim().toLowerCase()).filter(Boolean);
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
      const res = await apiFetch(`${API}/candidates/${id}/generate-qa`, {
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
      const res = await apiFetch(`${API}/candidates/${id}/webhook/github-sync`, {
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
        status: data.overall_score > 85 ? 'Strong Match' : 'Match',
        insights: data.insights || prev.insights,
        skills: data.skills || prev.skills,
        experience: data.experience || prev.experience,
        job_matches: data.job_matches || prev.job_matches,
        jobMatches: data.job_matches || prev.jobMatches,
        radar_data: data.radar_data || prev.radar_data,
        radarData: data.radar_data || prev.radarData,
      }));

      if (data.signals || (data.insights && data.insights.github_analysis)) {
        const ga = data.insights?.github_analysis || {};
        setGithub(prev => ({
          ...prev,
          username: prev?.username || ga.username || '',
          total_repos: data.signals?.public_repos ?? prev?.total_repos,
          total_stars: data.signals?.stars ?? prev?.total_stars,
          commit_frequency_per_week: data.signals?.commit_frequency ?? prev?.commit_frequency_per_week,
          score: data.github_score ?? prev?.score,
          engineering_score: ga.engineering_score !== undefined ? Math.round(ga.engineering_score) : prev?.engineering_score,
          open_source_score: ga.open_source_score !== undefined ? Math.round(ga.open_source_score) : prev?.open_source_score,
          project_maturity_score: ga.project_maturity_score !== undefined ? Math.round(ga.project_maturity_score) : prev?.project_maturity_score,
          verified_skills: ga.verified_skills || prev?.verified_skills || [],
          unsupported_claims: ga.unsupported_claims || prev?.unsupported_claims || [],
          languages: data.signals?.languages || prev?.languages || ga.languages || [],
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
                <button onClick={() => setShowEmailModal(true)}
                  className="w-full rounded-xl border border-emerald-500/20 bg-emerald-500/10 px-4 py-2.5 text-sm font-semibold text-emerald-400 hover:bg-emerald-500/20 transition-all flex items-center justify-center gap-2">
                  <Mail className="h-4 w-4" /> Contact Candidate
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
              {skillsList.length > 0 ? (
                <div className="mb-5 flex flex-wrap gap-2">
                  {skillsList.map((skill, i) => (
                    <span key={i} className="inline-flex items-center rounded-full bg-green-500/10 px-3 py-1 text-xs font-medium text-green-400 border border-green-500/20">
                      {skill}
                    </span>
                  ))}
                </div>
              ) : <p className="text-gray-500 text-sm mb-4">No skills extracted.</p>}
              <div className="h-56 w-full" role="img" aria-label="Radar chart showing candidate skill scores across key technical subjects">
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
              ) : (github || (insights.github_details && Object.keys(insights.github_details).length > 0)) ? (
                <div className="space-y-4">
                  {/* Score bar */}
                  <div className="flex items-center justify-between">
                    <span className="text-gray-400 text-xs font-semibold">GitHub Score</span>
                    <span className={`text-sm font-bold ${
                      (github?.score ?? insights.github_details?.engineering_score ?? 0) >= 70 ? 'text-green-400' :
                      (github?.score ?? insights.github_details?.engineering_score ?? 0) >= 40 ? 'text-yellow-400' : 'text-red-400'
                    }`}>{github?.score ?? insights.github_details?.engineering_score ?? 0}/100</span>
                  </div>
                  <div className="w-full bg-white/5 rounded-full h-1.5">
                    <div className="h-1.5 rounded-full bg-gradient-to-r from-emerald-500 to-cyan-400 transition-all"
                      style={{ width: `${github?.score ?? insights.github_details?.engineering_score ?? 0}%` }} />
                  </div>

                  {/* Stats grid */}
                  {github && (
                    <div className="grid grid-cols-2 gap-2 mt-3">
                      {[
                        { icon: <GitBranch className="h-3 w-3" />, label: 'Repos',   value: github.total_repos },
                        { icon: <Star className="h-3 w-3" />,      label: 'Stars',   value: github.total_stars },
                        { icon: <Activity className="h-3 w-3" />,  label: 'Commits/wk', value: github.commit_frequency_per_week },
                        { icon: <Github className="h-3 w-3" />,    label: 'PRs',     value: github.open_source_prs_estimate },
                      ].map(stat => (
                        <div key={stat.label} className="flex items-center gap-2 bg-white/5 rounded-lg px-2 py-1.5">
                          <span className="text-gray-500">{stat.icon}</span>
                          <div>
                            <p className="text-[#9D74FF] text-xs font-semibold">{stat.value ?? '—'}</p>
                            <p className="text-gray-500 text-[10px]">{stat.label}</p>
                          </div>
                        </div>
                      ))}
                    </div>
                  )}

                  {/* Detailed Scores */}
                  {(github?.engineering_score !== undefined || insights.github_details?.engineering_score !== undefined) && (
                    <div className="space-y-2 pt-2 border-t border-white/5 text-xs">
                      <div className="flex justify-between">
                        <span className="text-gray-400">Engineering Score</span>
                        <span className="text-white font-bold">{github?.engineering_score ?? insights.github_details?.engineering_score}/100</span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-gray-400">Open Source Score</span>
                        <span className="text-white font-bold">{github?.open_source_score ?? insights.github_details?.open_source_score}/100</span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-gray-400">Project Maturity</span>
                        <span className="text-white font-bold">{github?.project_maturity_score ?? insights.github_details?.project_maturity_score}/100</span>
                      </div>
                    </div>
                  )}

                  {/* Verified Skills */}
                  {(github?.verified_skills?.length > 0 || insights.github_details?.verified_skills?.length > 0) && (
                    <div className="pt-1 text-xs">
                      <span className="text-gray-400 block mb-1 font-semibold">Verified Skills (GitHub):</span>
                      <div className="flex flex-wrap gap-1">
                        {(github?.verified_skills ?? insights.github_details?.verified_skills).map(skill => (
                          <span key={skill} className="text-[10px] px-1.5 py-0.5 rounded bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
                            {skill}
                          </span>
                        ))}
                      </div>
                    </div>
                  )}

                  {/* Unsupported Claims */}
                  {(github?.unsupported_claims?.length > 0 || insights.github_details?.unsupported_claims?.length > 0) && (
                    <div className="pt-1 text-xs">
                      <span className="text-red-400 block mb-1 font-semibold">Unverified Stack Claims:</span>
                      <div className="flex flex-wrap gap-1">
                        {(github?.unsupported_claims ?? insights.github_details?.unsupported_claims).map(skill => (
                          <span key={skill} className="text-[10px] px-1.5 py-0.5 rounded bg-red-500/10 text-red-400 border border-red-500/20">
                            {skill}
                          </span>
                        ))}
                      </div>
                    </div>
                  )}

                  {/* Languages */}
                  {github && Array.isArray(github.languages) && github.languages.length > 0 && (
                    <div className="mt-2 pt-2 border-t border-white/5">
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
                  {github?.raw_bio && (
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
            
            {/* AI Summary Card */}
            <MagneticCard className="p-8 border-black/10 dark:border-white/10 bg-[#13131f] relative overflow-hidden">
              <div className="flex items-center justify-between mb-4 border-b border-white/5 pb-4">
                <div>
                  <h3 className="text-xl font-semibold text-white">AI Recruiter Summary</h3>
                  <p className="text-xs text-gray-500 mt-0.5">Synthesized executive intelligence summary and interview guidelines</p>
                </div>
                <div className="flex gap-2">
                  <span className="text-[10px] px-2 py-0.5 rounded-full bg-violet/15 text-violet border border-violet/20 font-medium">
                    AI Generated
                  </span>
                  {insights.sources_used && (
                    <span className="text-[10px] px-2 py-0.5 rounded-full bg-[#1e1e2f] text-gray-400 border border-white/5 font-medium">
                      Sources: {[
                        insights.sources_used.resume && 'Resume',
                        insights.sources_used.github && 'GitHub',
                        insights.sources_used.linkedin && 'LinkedIn'
                      ].filter(Boolean).join(' + ')}
                    </span>
                  )}
                </div>
              </div>
              
              <div className="space-y-4 text-sm leading-relaxed text-gray-300">
                <p>{insights.executive_summary || candidate?.summary || 'No summary available.'}</p>
                
                {insights.ranking_justification && (
                  <div className="bg-white/5 border border-white/5 rounded-xl p-4">
                    <span className="text-xs font-bold text-gray-400 block mb-1">Ranking Justification</span>
                    <p className="text-xs text-gray-300 italic">{insights.ranking_justification}</p>
                  </div>
                )}

                <div className="grid grid-cols-1 sm:grid-cols-2 gap-6 pt-2">
                  {insights.interview_focus?.length > 0 && (
                    <div>
                      <h4 className="text-xs font-bold text-violet uppercase tracking-wider mb-2">Interview Focus Areas</h4>
                      <ul className="space-y-1.5 text-xs text-gray-300 list-decimal pl-4">
                        {insights.interview_focus.map((item, idx) => (
                          <li key={idx}>{item}</li>
                        ))}
                      </ul>
                    </div>
                  )}
                  {insights.hiring_recommendation && (
                    <div>
                      <h4 className="text-xs font-bold text-gray-400 uppercase tracking-wider mb-2">Hiring Recommendation</h4>
                      <span className={`inline-flex items-center rounded-full px-3 py-1 text-xs font-semibold border ${
                        insights.hiring_recommendation.includes("Proceed") ? "bg-emerald-500/10 text-emerald-400 border-emerald-500/20" :
                        insights.hiring_recommendation.includes("Verify") ? "bg-yellow-500/10 text-yellow-400 border-yellow-500/20" :
                        "bg-red-500/10 text-red-400 border-red-500/20"
                      }`}>
                        {insights.hiring_recommendation}
                      </span>
                    </div>
                  )}
                </div>
              </div>
            </MagneticCard>

            {/* Match Breakdown Card */}
            {insights.match_breakdown && (
              <MagneticCard className="p-8 border-black/10 dark:border-white/10 bg-[#13131f]">
                <h3 className="mb-1 text-xl font-semibold text-white flex items-center gap-2">
                  📊 Job Description Match Breakdown
                </h3>
                <p className="text-xs text-gray-500 mb-6">Candidate compatibility metrics across primary role attributes</p>
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                  {[
                    { label: "Overall Match Score", value: insights.match_breakdown.overall_match_percentage, color: "bg-gradient-to-r from-violet to-fuchsia-600" },
                    { label: "Skills Alignment", value: insights.match_breakdown.skills_match, color: "bg-emerald-500" },
                    { label: "Experience Relevance", value: insights.match_breakdown.experience_match, color: "bg-blue-500" },
                    { label: "Education Fit", value: insights.match_breakdown.education_match, color: "bg-yellow-500" },
                    { label: "Projects Matching", value: insights.match_breakdown.projects_match, color: "bg-purple-500" },
                    { label: "GitHub Presence Strength", value: insights.match_breakdown.github_match, color: "bg-cyan-500" },
                  ].map(item => (
                    <div key={item.label} className="bg-white/5 border border-white/5 rounded-xl p-4">
                      <div className="flex justify-between text-xs mb-1">
                        <span className="text-gray-400 font-medium">{item.label}</span>
                        <span className="text-white font-bold">{item.value}%</span>
                      </div>
                      <div className="w-full bg-white/10 h-1.5 rounded-full overflow-hidden">
                        <div className={`h-full ${item.color} rounded-full`} style={{ width: `${item.value}%` }} />
                      </div>
                    </div>
                  ))}
                </div>
              </MagneticCard>
            )}

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
                <div className="bg-white/5 border border-white/5 rounded-xl p-4 flex flex-col justify-between">
                  <div className="flex justify-between items-center w-full mb-2">
                    <span className="text-xs text-gray-400 font-medium">Completeness Score</span>
                    <span className="text-sm font-bold text-white tabular-nums">{insights.completeness_score}%</span>
                  </div>
                  <div className="w-full bg-white/10 h-2 rounded-full overflow-hidden">
                    <div className="h-full bg-emerald-500 rounded-full" style={{ width: `${insights.completeness_score}%` }} />
                  </div>
                  <span className="text-[10px] text-gray-500 mt-2">
                    {insights.completeness_score >= 85 ? 'Recruiter-Grade Detail Profile' :
                     insights.completeness_score >= 60 ? 'Standard Profile Completeness' : 'Insufficient Profile Context'}
                  </span>
                </div>
                <div className="bg-white/5 border border-white/5 rounded-xl p-4 flex flex-col justify-between">
                  <div className="flex justify-between items-center w-full mb-2">
                    <span className="text-xs text-gray-400 font-medium">ATS Optimization Score</span>
                    <span className="text-sm font-bold text-white tabular-nums">{insights.ats_score}%</span>
                  </div>
                  <div className="w-full bg-white/10 h-2 rounded-full overflow-hidden">
                    <div className="h-full bg-violet rounded-full" style={{ width: `${insights.ats_score}%` }} />
                  </div>
                  <span className="text-[10px] text-gray-500 mt-2">
                    {insights.ats_score >= 80 ? 'Highly Formatted Compliance' :
                     insights.ats_score >= 50 ? 'Moderate Layout Alignment' : 'Suboptimal ATS Presentation'}
                  </span>
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

            {/* LinkedIn Verification (Redesigned as full width) */}
            {insights.linkedin_details && Object.keys(insights.linkedin_details).length > 0 && (
              <MagneticCard className="p-8 border-black/10 dark:border-white/10 bg-[#13131f]">
                <h3 className="mb-1 text-xl font-semibold text-blue-400 flex items-center gap-2">
                  <Linkedin className="h-5 w-5" /> LinkedIn Verification
                </h3>
                <p className="text-xs text-gray-500 mb-6">Cross-referenced verification of professional profile metrics and history</p>
                <div className="space-y-4 text-sm leading-relaxed">
                  <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 mb-4">
                    <div className="bg-white/5 border border-white/5 rounded-xl p-4 flex flex-col justify-between">
                      <span className="text-xs text-gray-400 block mb-1">Profile Strength</span>
                      <span className="text-lg font-bold text-white tabular-nums">{insights.linkedin_details.profile_strength_score}/100</span>
                      <div className="w-full bg-white/10 h-1.5 rounded-full overflow-hidden mt-2">
                        <div className="h-full bg-blue-500 rounded-full" style={{ width: `${insights.linkedin_details.profile_strength_score}%` }} />
                      </div>
                    </div>
                    <div className="bg-white/5 border border-white/5 rounded-xl p-4 flex flex-col justify-between">
                      <span className="text-xs text-gray-400 block mb-1">Career Progression</span>
                      <span className="text-lg font-bold text-white tabular-nums">{insights.linkedin_details.career_progression_score}/100</span>
                      <div className="w-full bg-white/10 h-1.5 rounded-full overflow-hidden mt-2">
                        <div className="h-full bg-blue-500 rounded-full" style={{ width: `${insights.linkedin_details.career_progression_score}%` }} />
                      </div>
                    </div>
                    <div className="bg-white/5 border border-white/5 rounded-xl p-4 flex flex-col justify-between">
                      <span className="text-xs text-gray-400 block mb-1">Industry Relevance</span>
                      <span className="text-lg font-bold text-white tabular-nums">{insights.linkedin_details.industry_relevance_score}/100</span>
                      <div className="w-full bg-white/10 h-1.5 rounded-full overflow-hidden mt-2">
                        <div className="h-full bg-blue-500 rounded-full" style={{ width: `${insights.linkedin_details.industry_relevance_score}%` }} />
                      </div>
                    </div>
                  </div>
                  {insights.linkedin_details.leadership_indicators?.length > 0 && (
                    <div className="pt-2">
                      <span className="text-gray-400 text-xs block mb-2 font-semibold">Leadership Signals:</span>
                      <ul className="list-disc pl-4 space-y-1 text-xs text-gray-300">
                        {insights.linkedin_details.leadership_indicators.map((ind, i) => (
                          <li key={i}>{ind}</li>
                        ))}
                      </ul>
                    </div>
                  )}
                  {insights.linkedin_details.inconsistencies?.length > 0 && (
                    <div className="pt-2 border-t border-white/5">
                      <span className="text-red-400 text-xs block mb-2 font-semibold">Timeline Discrepancies:</span>
                      <ul className="list-disc pl-4 space-y-1 text-xs text-red-300">
                        {insights.linkedin_details.inconsistencies.map((inc, i) => (
                          <li key={i}>{inc.message}</li>
                        ))}
                      </ul>
                    </div>
                  )}
                </div>
              </MagneticCard>
            )}

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
                {experienceList.length > 0 ? experienceList.map((exp, i) => (
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
                          <span className="text-yellow-400 text-xs">
                            {'★'.repeat(Math.max(0, Math.min(5, Number(note.rating) || 0)))}
                            {'☆'.repeat(Math.max(0, Math.min(5, 5 - (Number(note.rating) || 0))))}
                          </span>
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
                {(skillsList.slice(0, 4)).map((skill, i) => {
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
          <SkillGapCard candidateSkills={skillsList} role={candidate?.role} />
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

      {/* Simulated Email Modal */}
      <AnimatePresence>
        {showEmailModal && (
          <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}
            className="fixed inset-0 bg-black/60 backdrop-blur-sm z-50 flex items-center justify-center p-4"
            onClick={() => setShowEmailModal(false)}>
            <motion.div initial={{ scale: 0.95, opacity: 0 }} animate={{ scale: 1, opacity: 1 }} exit={{ scale: 0.95, opacity: 0 }}
              onClick={e => e.stopPropagation()}
              className="bg-[#13131f] border border-white/10 rounded-2xl p-6 w-full max-w-lg shadow-2xl relative space-y-4">
              <div className="flex items-center justify-between">
                <h3 className="text-white font-semibold text-lg flex items-center gap-2">
                  <Mail className="h-5 w-5 text-emerald-400" /> Contact Candidate
                </h3>
                <button onClick={() => setShowEmailModal(false)} className="text-gray-400 hover:text-white transition-colors">
                  <X size={18} />
                </button>
              </div>

              <form onSubmit={handleSendEmail} className="space-y-4">
                <div className="flex flex-col gap-1.5">
                  <label className="text-xs font-semibold text-gray-400">Recipient Email</label>
                  <input 
                    type="text" 
                    disabled 
                    value={candidate?.email || 'No email available'}
                    className="bg-[#0e0e1a]/50 border border-white/5 rounded-xl px-3 py-2 text-xs text-gray-400 outline-none w-full"
                  />
                </div>

                <div className="flex flex-col gap-1.5">
                  <label className="text-xs font-semibold text-gray-400">Choose Template</label>
                  <select 
                    value={selectedTemplate}
                    onChange={(e) => setSelectedTemplate(e.target.value)}
                    className="bg-[#0e0e1a] border border-white/10 rounded-xl px-3 py-2 text-xs text-white focus:border-emerald-500/50 outline-none cursor-pointer"
                  >
                    <option value="">Select a template...</option>
                    {Object.entries(emailTemplates).map(([key, value]) => (
                      <option key={key} value={key}>{value.name}</option>
                    ))}
                  </select>
                </div>

                <div className="flex flex-col gap-1.5">
                  <label className="text-xs font-semibold text-gray-400">Email Subject</label>
                  <input 
                    type="text" 
                    required
                    value={emailSubject}
                    onChange={(e) => setEmailSubject(e.target.value)}
                    placeholder="Enter email subject..."
                    className="bg-[#0e0e1a] border border-white/10 rounded-xl px-3 py-2 text-xs text-white focus:border-emerald-500/50 outline-none w-full"
                  />
                </div>

                <div className="flex flex-col gap-1.5">
                  <label className="text-xs font-semibold text-gray-400">Email Body</label>
                  <textarea 
                    rows="8"
                    required
                    value={emailBody}
                    onChange={(e) => setEmailBody(e.target.value)}
                    placeholder="Write your email here..."
                    className="bg-[#0e0e1a] border border-white/10 rounded-xl px-3 py-2 text-xs text-white focus:border-emerald-500/50 outline-none w-full font-sans leading-relaxed resize-none"
                  />
                </div>

                <div className="flex justify-end gap-3 pt-2">
                  <button 
                    type="button"
                    onClick={() => setShowEmailModal(false)}
                    className="px-4 py-2 text-xs font-semibold text-gray-400 hover:text-white transition-colors"
                  >
                    Cancel
                  </button>
                  <button 
                    type="submit"
                    className="px-6 py-2 rounded-xl bg-gradient-to-r from-emerald-500 to-cyan-500 font-bold text-white shadow-lg shadow-emerald-500/10 hover:scale-[1.02] active:scale-95 transition-all duration-200 text-xs"
                  >
                    Send Email (Simulated)
                  </button>
                </div>
              </form>
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>
    </motion.div>
  );
}
