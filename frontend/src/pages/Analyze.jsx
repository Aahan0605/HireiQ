import React, { useState, useEffect, useCallback } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { useDropzone } from 'react-dropzone';
import { useNavigate, Link } from 'react-router-dom';
import { UploadCloud, FileText, Loader2, Sparkles, CheckCircle2, XCircle, Files, ShieldAlert, Lock, Zap, Check, X } from 'lucide-react';
import { toast } from 'sonner';
import MagneticCard from '../components/MagneticCard';
import { addCandidateFromCV } from '../data/candidates';
import { apiFetch } from '../lib/apiFetch';

const API = '/api/v1';

export default function Analyze() {
  const navigate = useNavigate();
  const [files, setFiles] = useState([]);
  const [mode, setMode] = useState('single'); // 'single' | 'bulk'
  const [analyzing, setAnalyzing] = useState(false);
  const [progress, setProgress] = useState(0);
  const [currentStep, setCurrentStep] = useState(0);

  // SaaS Quota and Billing States
  const [quotaUsed, setQuotaUsed] = useState(0);
  const [plan, setPlan] = useState('Free');
  const [showUpgradeModal, setShowUpgradeModal] = useState(false);

  // Sync active quota and plan from database
  useEffect(() => {
    apiFetch(`${API}/settings/analytics`)
      .then(r => r.ok ? r.json() : { total_candidates: 0 })
      .then(data => {
        setQuotaUsed(data.total_candidates ?? 0);
        if (data.plan_name) {
          setPlan(data.plan_name);
        }
      })
      .catch(() => {});
  }, []);

  const analysisSteps = [
    'Scanning semantic structure...',
    'Extracting technical expertise...',
    'Cross-referencing GitHub activity...',
    'Calculating TF-IDF match scores...',
    'Persisting to database...',
    'Finalizing profiles...',
  ];

  const onDrop = useCallback((accepted) => {
    if (plan === 'Free' && quotaUsed >= 5) {
      toast.error('Resume parsing limit reached. Upgrade to Pro to upload more candidates!');
      setShowUpgradeModal(true);
      return;
    }
    if (mode === 'single') {
      setFiles(accepted.slice(0, 1));
    } else {
      setFiles(accepted.slice(0, 1000));
    }
  }, [mode, plan, quotaUsed]);

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      'application/pdf': ['.pdf'],
      'application/msword': ['.doc'],
      'application/vnd.openxmlformats-officedocument.wordprocessingml.document': ['.docx'],
    },
    maxFiles: mode === 'single' ? 1 : 1000,
    multiple: mode === 'bulk',
  });

  // ── Single upload (existing flow) ────────────────────────────
  const handleSingle = async () => {
    if (!files[0]) return;
    setAnalyzing(true);
    setProgress(10);
    setCurrentStep(0);

    try {
      const formData = new FormData();
      formData.append('file', files[0]);

      const uploadRes = await apiFetch(`${API}/candidates/upload-resume`, {
        method: 'POST',
        body: formData,
      });

      if (!uploadRes.ok) {
        const err = await uploadRes.json().catch(() => ({}));
        if (uploadRes.status === 402) {
          setShowUpgradeModal(true);
          setAnalyzing(false);
          return;
        }
        throw new Error(err.detail || 'Upload failed');
      }

      const { candidate_id } = await uploadRes.json();
      setProgress(30);
      setCurrentStep(1);

      const startedAt = Date.now();
      const timeoutMs = 60000;

      const updateProgress = (nextProgress) => {
        const rounded = Math.round(nextProgress);
        setProgress(rounded);
        setCurrentStep(Math.min(Math.floor((rounded / 100) * analysisSteps.length), analysisSteps.length - 1));
      };

      const poll = setInterval(async () => {
        const elapsed = Date.now() - startedAt;
        if (elapsed >= timeoutMs) {
          clearInterval(poll);
          toast.error('Analysis is taking longer than expected. Check the Candidates page.');
          setAnalyzing(false);
          return;
        }

        try {
          const statusRes = await apiFetch(`${API}/candidates/${candidate_id}`);
          if (!statusRes.ok) return;
          const candidate = await statusRes.json();

          const status = String(candidate.status || '').toLowerCase();
          const summary = String(candidate.summary || '').toLowerCase();
          const score = Number(candidate.score ?? candidate.final_score ?? candidate.baseScore ?? 0);
          const isProcessing = ['processing', 'pending', 'analyzing'].includes(status) || summary.includes('analyzing resume');
          const isError = ['error', 'failed'].includes(status) || summary.includes('encountered an error');
          const isAnalyzed = status === 'analyzed' || score > 0;

          if (isError) {
            clearInterval(poll);
            setProgress(0);
            setCurrentStep(0);
            setAnalyzing(false);
            toast.error('Analysis failed. Please try uploading the resume again.');
            return;
          }

          if (isAnalyzed && !isProcessing) {
            clearInterval(poll);
            setProgress(100);
            setCurrentStep(analysisSteps.length - 1);
            setTimeout(() => {
              toast.success('Analysis complete!');
              navigate(`/candidate/${candidate_id}`);
            }, 600);
            return;
          }

          const processingProgress = 30 + Math.min(40, (elapsed / timeoutMs) * 40);
          updateProgress(Math.min(processingProgress, 70));
        } catch (e) {
          // silent - keep polling
        }
      }, 2000);

    } catch (err) {
      toast.error(err.message || 'Upload failed. Please try again.');
      setAnalyzing(false);
    }
  };

  // ── Bulk upload ───────────────────────────────────────────────
  const handleBulk = async () => {
    if (!files.length) return;
    setAnalyzing(true);
    setProgress(0);

    const formData = new FormData();
    files.forEach((f) => formData.append('files', f));

    try {
      const res = await apiFetch(`${API}/candidates/upload-bulk`, {
        method: 'POST',
        body: formData,
      });
      if (!res.ok) throw new Error('Bulk upload failed');
      const data = await res.json();
      setProgress(100);
      toast.success(`Successfully enqueued ${files.length} resumes for background analysis!`);
      setTimeout(() => navigate('/candidates'), 800);
    } catch (e) {
      toast.error(e.message || 'Error uploading batch.');
    } finally {
      setAnalyzing(false);
    }
  };

  const handleAnalyze = () => {
    if (plan === 'Free' && quotaUsed >= 5) {
      toast.error('Resume parsing limit reached. Upgrade to Pro to upload more candidates!');
      setShowUpgradeModal(true);
      return;
    }
    mode === 'single' ? handleSingle() : handleBulk();
  };

  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      transition={{ duration: 0.3 }}
      className="flex min-h-screen items-center justify-center p-6 bg-bg overflow-hidden relative"
    >
      <div className="absolute top-1/4 left-1/4 h-96 w-96 rounded-full bg-violet/10 blur-[120px] mix-blend-screen" />
      <div className="absolute bottom-1/4 right-1/4 h-[400px] w-[400px] rounded-full bg-mint/10 blur-[140px] mix-blend-screen" />

      <main className="w-full max-w-2xl relative z-10">
        <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} className="text-center mb-8">
          <h1 className="font-display text-4xl font-bold tracking-tight text-white mb-3">
            New Candidate Analysis
          </h1>
          <p className="text-text-2 text-lg">Upload one resume or hundreds at once.</p>
        </motion.div>

        {/* Mode toggle */}
        <div className="flex justify-center gap-3 mb-6">
          {['single', 'bulk'].map((m) => (
            <button
              key={m}
              onClick={() => { setMode(m); setFiles([]); }}
              disabled={plan === 'Free' && quotaUsed >= 5}
              className={`flex items-center gap-2 px-5 py-2 rounded-xl text-sm font-medium transition-all ${
                mode === m ? 'bg-violet text-white' : 'bg-surface-2 text-text-2 hover:text-white'
              } disabled:opacity-50 disabled:cursor-not-allowed`}
            >
              {m === 'single' ? <FileText size={15} /> : <Files size={15} />}
              {m === 'single' ? 'Single CV' : 'Bulk Upload (up to 1000)'}
            </button>
          ))}
        </div>

        <MagneticCard className="p-8 border-border bg-surface-2/60 backdrop-blur-xl" maxTilt={3}>
          <AnimatePresence mode="wait">
            {!analyzing ? (
              /* ── Upload view ── */
              <motion.div key="upload" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0, scale: 0.95 }} className="flex flex-col items-center">
                <div
                  {...(plan === 'Free' && quotaUsed >= 5 ? {} : getRootProps())}
                  className={`w-full rounded-2xl border-2 border-dashed p-12 text-center transition-colors ${
                    plan === 'Free' && quotaUsed >= 5
                      ? 'border-rose-500/20 bg-rose-500/5 cursor-default'
                      : isDragActive
                      ? 'border-mint bg-mint/5 cursor-pointer'
                      : 'border-border hover:border-violet/50 hover:bg-surface-3 cursor-pointer'
                  }`}
                >
                  {plan === 'Free' && quotaUsed >= 5 ? (
                    <div className="flex flex-col items-center gap-4 py-4" onClick={(e) => e.stopPropagation()}>
                      <div className="flex h-16 w-16 items-center justify-center rounded-full bg-rose-500/10 text-rose-400 border border-rose-500/20 shadow-glow-rose/10">
                        <ShieldAlert className="h-8 w-8" />
                      </div>
                      <div className="space-y-2">
                        <p className="text-white font-bold text-xl">Resume Parsing Limit Reached</p>
                        <p className="text-text-2 text-sm max-w-md mx-auto leading-relaxed">
                          You have used all <strong>{quotaUsed} / 5</strong> free CV parses on this workspace. Upgrade to Pro for unlimited candidate analysis, advanced filters, and GitHub footprint tracking!
                        </p>
                      </div>
                      <button
                        onClick={() => setShowUpgradeModal(true)}
                        className="mt-2 px-6 py-2.5 rounded-xl bg-gradient-to-r from-emerald-500 to-cyan-500 font-bold text-white shadow-lg shadow-emerald-500/20 hover:scale-[1.02] active:scale-95 transition-all duration-200 text-xs flex items-center gap-1.5"
                      >
                        <Zap size={13} /> Upgrade to Pro
                      </button>
                    </div>
                  ) : (
                    <>
                      <input {...getInputProps()} />
                      {files.length > 0 ? (
                        <div className="flex flex-col items-center gap-3">
                          <div className="flex h-16 w-16 items-center justify-center rounded-full bg-surface-3 text-violet">
                            {mode === 'bulk' ? <Files className="h-8 w-8" /> : <FileText className="h-8 w-8" />}
                          </div>
                          {mode === 'single' ? (
                            <>
                              <p className="text-white font-medium text-lg">{files[0].name}</p>
                              <p className="text-text-3 text-sm">{(files[0].size / 1024 / 1024).toFixed(2)} MB</p>
                            </>
                          ) : (
                            <>
                              <p className="text-white font-medium text-lg">{files.length} files selected</p>
                              <p className="text-text-3 text-sm">
                                {(files.reduce((a, f) => a + f.size, 0) / 1024 / 1024).toFixed(2)} MB total
                              </p>
                            </>
                          )}
                        </div>
                      ) : (
                        <div className="flex flex-col items-center gap-3">
                          <div className="flex h-16 w-16 items-center justify-center rounded-full bg-surface-3 text-text-2">
                            <UploadCloud className="h-8 w-8" />
                          </div>
                          <p className="text-white font-medium text-lg mt-2">
                            {isDragActive ? 'Drop resumes here' : mode === 'bulk' ? 'Drag & drop up to 1000 resumes' : 'Drag & drop resume here'}
                          </p>
                          <p className="text-text-2 text-sm">PDF or DOCX</p>
                        </div>
                      )}
                    </>
                  )}
                </div>

                {!(plan === 'Free' && quotaUsed >= 5) && (
                  <div className="mt-8 flex w-full justify-end">
                    <button
                      onClick={handleAnalyze}
                      disabled={!files.length}
                      className="group relative h-12 inline-flex items-center justify-center overflow-hidden rounded-xl bg-violet px-8 font-medium text-bg transition-transform hover:scale-[1.02] disabled:opacity-50 disabled:hover:scale-100"
                    >
                      <span className="absolute inset-0 bg-gradient-to-r from-mint to-sky opacity-0 transition-opacity group-hover:opacity-100 disabled:opacity-0" />
                      <span className="relative z-10 flex items-center group-hover:text-bg">
                        {mode === 'bulk' ? `Analyze ${files.length || ''} Resumes` : 'Start Analysis'}
                        <Sparkles className="ml-2 h-4 w-4" />
                      </span>
                    </button>
                  </div>
                )}
              </motion.div>

            ) : (
              /* ── Analyzing view ── */
              <motion.div key="analyzing" initial={{ opacity: 0, scale: 0.95 }} animate={{ opacity: 1, scale: 1 }} className="flex flex-col items-center py-12">
                <div className="relative mb-8 flex h-24 w-24 items-center justify-center rounded-full bg-surface-3">
                  <Loader2 className="h-10 w-10 animate-spin text-mint" />
                  <div className="absolute inset-0 rounded-full border border-mint/30 shadow-glow-mint animate-pulse" />
                </div>
                <h3 className="mb-2 text-2xl font-bold text-white">
                  {mode === 'bulk' ? `Processing ${files.length} Resumes...` : 'Analyzing Profile'}
                </h3>
                <p className="text-theme-2 text-sm text-center mb-8 max-w-sm">
                  {progress < 30 ? 'Uploading resume...' 
                   : progress < 70 ? 'Analyzing candidate profile...' 
                   : progress < 100 ? 'Finalizing results...' 
                   : 'Complete!'}
                </p>
                <div className="w-full max-w-sm">
                  <div className="mb-2 flex justify-between text-sm font-medium">
                    <span className="text-text-1">{mode === 'bulk' ? 'Uploading batch...' : analysisSteps[currentStep]}</span>
                    <span className="text-mint">{Math.round(progress)}%</span>
                  </div>
                  <div className="h-2 w-full overflow-hidden rounded-full bg-surface-3">
                    <motion.div
                      className="h-full rounded-full bg-gradient-to-r from-mint to-sky"
                      initial={{ width: '0%' }}
                      animate={{ width: `${progress}%` }}
                      transition={{ ease: 'linear' }}
                    />
                  </div>
                </div>
              </motion.div>
            )}
          </AnimatePresence>
        </MagneticCard>
      </main>

      {/* Upgrade to Pro Modal */}
      <AnimatePresence>
        {showUpgradeModal && (
          <motion.div 
            initial={{ opacity: 0 }} 
            animate={{ opacity: 1 }} 
            exit={{ opacity: 0 }}
            className="fixed inset-0 bg-black/60 backdrop-blur-md z-50 flex items-center justify-center p-4"
            onClick={() => setShowUpgradeModal(false)}
          >
            <motion.div 
              initial={{ scale: 0.95, opacity: 0 }} 
              animate={{ scale: 1, opacity: 1 }} 
              exit={{ scale: 0.95, opacity: 0 }}
              onClick={e => e.stopPropagation()}
              className="bg-[#13131f] border border-white/10 rounded-2xl p-6 w-full max-w-md shadow-2xl relative space-y-5"
            >
              <div className="flex items-center justify-between">
                <h3 className="text-white font-semibold text-lg flex items-center gap-2">
                  <Zap className="h-5 w-5 text-emerald-400" /> Upgrade to Recruiter Pro
                </h3>
                <button onClick={() => setShowUpgradeModal(false)} className="text-gray-400 hover:text-white transition-colors">
                  <X size={18} />
                </button>
              </div>

              <div className="space-y-4">
                <p className="text-xs text-gray-400 leading-relaxed">
                  Unlock the full potential of HireIQ and scale your hiring workflow. Upgrading to the Recruiter Pro plan includes:
                </p>

                <ul className="space-y-3 text-xs text-gray-300">
                  <li className="flex items-start gap-2.5">
                    <Check size={14} className="text-emerald-400 mt-0.5 flex-shrink-0" />
                    <span><strong>Unlimited CV Resumes</strong>: Parse and analyze as many candidates as you need without any caps.</span>
                  </li>
                  <li className="flex items-start gap-2.5">
                    <Check size={14} className="text-emerald-400 mt-0.5 flex-shrink-0" />
                    <span><strong>Kanban Hiring Pipeline</strong>: Manage candidates through customizable stages with drag & drop.</span>
                  </li>
                  <li className="flex items-start gap-2.5">
                    <Check size={14} className="text-emerald-400 mt-0.5 flex-shrink-0" />
                    <span><strong>Advanced Filter Controls</strong>: Filter candidates by scores, experience, education, and skill tags.</span>
                  </li>
                  <li className="flex items-start gap-2.5">
                    <Check size={14} className="text-emerald-400 mt-0.5 flex-shrink-0" />
                    <span><strong>Real-time GitHub Footprint</strong>: Automatically pull candidates' commit frequencies, public repos, and star metrics.</span>
                  </li>
                </ul>
              </div>

              <div className="flex gap-3 pt-2">
                <button 
                  type="button"
                  onClick={() => setShowUpgradeModal(false)}
                  className="flex-1 py-2.5 rounded-xl border border-white/10 text-xs font-semibold text-gray-400 hover:text-white transition-colors"
                >
                  Maybe Later
                </button>
                <Link 
                  to="/settings?tab=billing"
                  className="flex-1 py-2.5 rounded-xl bg-gradient-to-r from-emerald-500 to-cyan-500 font-bold text-center text-white shadow-lg shadow-emerald-500/10 hover:scale-[1.02] active:scale-95 transition-all duration-200 text-xs flex items-center justify-center gap-1.5"
                >
                  Upgrade Now ⚡
                </Link>
              </div>
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>
    </motion.div>
  );
}
