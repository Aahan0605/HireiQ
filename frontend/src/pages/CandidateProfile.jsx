import React, { useState } from 'react';
import { motion } from 'framer-motion';
import { useParams, Link } from 'react-router-dom';
import { ResponsiveContainer, RadarChart, PolarGrid, PolarAngleAxis, Radar } from 'recharts';
import { Mail, Github, Linkedin, MapPin, Award, ArrowLeft, Terminal, Layout, Workflow, Loader2, Calendar } from 'lucide-react';
import { toast } from 'sonner';
import MagneticCard from '../components/MagneticCard';
import SkillGapCard from '../components/SkillGapCard';
import { fadeUp, staggerContainer, listItem } from '../lib/animations';
import { getCandidateById } from '../data/candidates';

export default function CandidateProfile() {
  const { id } = useParams();
  const [isScheduling, setIsScheduling] = useState(false);

  try {
    // Find candidate by ID or default to Alice
    const candidate = getCandidateById(id) || getCandidateById('1');
    
    if (!candidate) {
      return (
        <div className="min-h-screen bg-bg p-6 lg:p-12 flex items-center justify-center">
          <div className="text-center">
            <h1 className="text-3xl font-bold text-white mb-4">Candidate Not Found</h1>
            <p className="text-text-2 mb-6">The candidate you're looking for doesn't exist.</p>
            <Link to="/candidates" className="inline-flex items-center gap-2 bg-violet px-6 py-2 rounded-lg text-white hover:bg-violet/80 transition">
              Back to Candidates
            </Link>
          </div>
        </div>
      );
    }

    // Generate radar data based on the candidate's skills
    const baseScore = candidate?.baseScore || candidate?.score || 75;
  let radarData = candidate.radarData || [
    { subject: 'Frontend', A: Math.min(100, baseScore + Math.floor(Math.random() * 10 - 5)), fullMark: 100 },
    { subject: 'Backend', A: Math.min(100, baseScore + Math.floor(Math.random() * 20 - 15)), fullMark: 100 },
    { subject: 'DevOps', A: Math.min(100, baseScore + Math.floor(Math.random() * 30 - 25)), fullMark: 100 },
    { subject: 'UX Design', A: Math.min(100, baseScore + Math.floor(Math.random() * 15 - 5)), fullMark: 100 },
    { subject: 'Architecture', A: Math.min(100, baseScore + Math.floor(Math.random() * 10 - 5)), fullMark: 100 },
    { subject: 'Testing', A: Math.min(100, baseScore + Math.floor(Math.random() * 10 - 5)), fullMark: 100 },
  ];

  if (!candidate.radarData && candidate.skills && candidate.skills.length > 0) {
      const topSkills = candidate?.skills?.slice(0, 6) || [];
      radarData = topSkills.map((skill) => {
          const variation = (skill?.length || 0) % 15 - 5; 
          return {
              subject: skill?.substring(0, 12) || 'Skill',
              A: Math.min(100, baseScore + variation),
              fullMark: 100
          };
      });
      // Pad to 6 categories if the candidate has fewer than 6 skills
      const defaultSubjects = ['Frontend', 'Backend', 'Database', 'Cloud', 'Algorithms', 'System Design'];
      while (radarData.length < 6) {
          const subject = defaultSubjects[radarData.length] || `Skill ${radarData.length + 1}`;
          radarData.push({ subject: subject, A: baseScore - 5, fullMark: 100 });
      }
  }

  const handleSchedule = () => {
    setIsScheduling(true);
    
    // Simulate API call and email sending
    const promise = new Promise((resolve) => setTimeout(resolve, 2000));
    
    toast.promise(promise, {
      loading: 'Scheduling interview and preparing notification email...',
      success: () => {
        setIsScheduling(false);
        return `Interview scheduled! Confirmation email sent to ${candidate.email}`;
      },
      error: 'Failed to schedule interview. Please try again.',
    });
  };

  return (
    <div className="min-h-screen bg-bg p-6 lg:p-12">
      <div className="mx-auto max-w-6xl">
        <div className="mb-8">
          <Link to="/dashboard" className="inline-flex items-center text-sm font-medium text-text-2 transition-colors hover:text-white">
            <ArrowLeft className="mr-2 h-4 w-4" />
            Back to Dashboard
          </Link>
        </div>

        <motion.div
          variants={staggerContainer}
          initial="initial"
          animate="animate"
          className="grid gap-8 lg:grid-cols-3"
        >
          {/* Profile Sidebar */}
          <motion.div variants={fadeUp} className="flex flex-col gap-6">
            <MagneticCard className="p-8 border-border bg-surface-2/80">
              <div className="mb-6 flex flex-col items-center">
                <div className="mb-4 flex h-24 w-24 items-center justify-center rounded-full bg-gradient-to-br from-violet to-mint text-3xl font-bold text-bg shadow-glow-violet">
                  {candidate?.name?.split(' ')?.map(n => n?.[0])?.join('') || 'C'}
                </div>
                <h1 className="text-2xl font-bold text-white">{candidate?.name || 'Unknown'}</h1>
                <p className="text-text-2">{candidate?.role || 'Role not specified'}</p>
                <div className="mt-4 inline-flex items-center gap-1.5 rounded-full bg-mint/10 px-3 py-1 text-sm font-medium text-mint">
                  <Award className="h-4 w-4" />
                  {candidate?.score || 'N/A'}% Match Score

              <div className="space-y-4 border-t border-border pt-6">
                <div className="flex items-center gap-3 text-sm text-text-1">
                  <MapPin className="h-4 w-4 text-text-3" />
                  {candidate?.location || 'Location not specified'}
                </div>
                <div className="flex items-center gap-3 text-sm text-text-1">
                  <Mail className="h-4 w-4 text-text-3" />
                  {candidate?.email || 'Email not specified'}
                </div>
                <div className="flex items-center gap-3 text-sm text-text-1">
                  <Github className="h-4 w-4 text-text-3" />
                  {candidate?.github || 'GitHub not specified'}
                </div>
                <div className="flex items-center gap-3 text-sm text-text-1">
                  <Linkedin className="h-4 w-4 text-text-3" />
                  {candidate?.linkedin || 'LinkedIn not specified'}
                </div>
              </div>

              <button 
                onClick={handleSchedule}
                disabled={isScheduling}
                className="mt-8 w-full rounded-xl bg-white px-4 py-3 font-semibold text-bg transition-all hover:scale-[1.02] active:scale-[0.98] disabled:opacity-50 disabled:hover:scale-100 flex items-center justify-center gap-2"
              >
                {isScheduling ? (
                  <>
                    <Loader2 className="h-4 w-4 animate-spin text-bg" />
                    Scheduling...
                  </>
                ) : (
                  <>
                    <Calendar className="h-4 w-4" />
                    Schedule Interview
                  </>
                )}
              </button>
            </MagneticCard>
            
            <MagneticCard className="p-8 border-border bg-surface-2/80">
              <h3 className="mb-6 text-lg font-semibold text-white">Skill Analysis</h3>
              
              {/* Skills Pills */}
              {candidate?.skills && candidate.skills.length > 0 ? (
                <div className="mb-6 flex flex-wrap gap-2">
                  {candidate.skills.map((skill, i) => (
                    <span
                      key={i}
                      className="inline-flex items-center rounded-full bg-green-500/15 px-3 py-1.5 text-sm font-medium text-green-400 border border-green-500/30"
                    >
                      {skill}
                    </span>
                  ))}
                </div>
              ) : (
                <p className="mb-6 text-sm text-text-3">No skills extracted. Try re-uploading the resume.</p>
              )}

              {/* Radar Chart */}
              <div className="h-64 w-full">
                <ResponsiveContainer width="100%" height="100%">
                  <RadarChart cx="50%" cy="50%" outerRadius="70%" data={radarData}>
                    <PolarGrid stroke="rgba(255,255,255,0.1)" />
                    <PolarAngleAxis dataKey="subject" tick={{ fill: '#9494B0', fontSize: 12 }} />
                    <Radar name={candidate?.name || 'Candidate'} dataKey="A" stroke="#9D74FF" fill="#9D74FF" fillOpacity={0.4} />
                  </RadarChart>
                </ResponsiveContainer>
              </div>
            </MagneticCard>
          </motion.div>

          {/* Main Content Area */}
          <motion.div variants={fadeUp} className="flex flex-col gap-6 lg:col-span-2">
            <MagneticCard className="p-8 border-border bg-surface-2/80">
              <h3 className="mb-4 text-xl font-semibold text-white">AI Summary Insight</h3>
              <p className="text-text-2 leading-relaxed text-balance">
                {candidate?.summary || 'No summary available for this candidate.'}
              </p>
            </MagneticCard>

            <MagneticCard className="p-8 border-border bg-surface-2/80">
              <h3 className="mb-6 text-xl font-semibold text-white">Experience Timeline</h3>
              
              <div className="relative border-l border-border/50 pl-6 ml-3 space-y-10">
                {candidate?.experience && candidate.experience.length > 0 ? (
                  candidate.experience.map((exp, i) => (
                    <motion.div variants={listItem} key={i} className="relative">
                      <span className="absolute -left-10 flex h-8 w-8 items-center justify-center rounded-full border-4 border-surface-2 bg-surface-3 text-mint">
                        {i === 0 ? <Layout className="h-4 w-4" /> : <Terminal className="h-4 w-4" />}
                      </span>
                      <h4 className="text-lg font-bold text-white mb-1">{exp?.title || 'Position'}</h4>
                      <div className="flex items-center gap-2 mb-3">
                        <span className="text-sm font-medium text-violet">{exp?.company || 'Company'}</span>
                        <span className="text-text-3">&bull;</span>
                        <span className="text-sm text-text-2">{exp?.date || 'Dates'}</span>
                      </div>
                      <p className="text-text-3 text-sm">
                        {exp?.description || 'No description available'}
                      </p>
                    </motion.div>
                  ))
                ) : (
                  <p className="text-text-3 text-sm">No experience data available</p>
                )}
              </div>
            </MagneticCard>
          </motion.div>
        </motion.div>

        {/* Skill Gap Analysis */}
        <motion.div variants={fadeUp} className="mt-8">
          <SkillGapCard />
        </motion.div>
      </div>
    </div>
    );
  } catch (error) {
    console.error("Error rendering CandidateProfile:", error);
    return (
      <div className="min-h-screen bg-bg p-6 lg:p-12 flex items-center justify-center">
        <div className="text-center">
          <h1 className="text-3xl font-bold text-white mb-4">Something Went Wrong</h1>
          <p className="text-text-2 mb-6">We encountered an error loading this candidate's profile.</p>
          <Link to="/candidates" className="inline-flex items-center gap-2 bg-violet px-6 py-2 rounded-lg text-white hover:bg-violet/80 transition">
            Back to Candidates
          </Link>
        </div>
      </div>
    );
  }
}
