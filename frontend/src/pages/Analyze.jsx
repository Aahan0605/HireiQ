import React, { useState, useCallback } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { useDropzone } from 'react-dropzone';
import { useNavigate } from 'react-router-dom';
import { UploadCloud, FileText, Loader2, Sparkles, CheckCircle2, XCircle, Files } from 'lucide-react';
import { toast } from 'sonner';
import MagneticCard from '../components/MagneticCard';
import { addCandidateFromCV } from '../data/candidates';

const API = '/api/v1';

export default function Analyze() {
  const navigate = useNavigate();
  const [files, setFiles] = useState([]);
  const [mode, setMode] = useState('single'); // 'single' | 'bulk'
  const [analyzing, setAnalyzing] = useState(false);
  const [progress, setProgress] = useState(0);
  const [currentStep, setCurrentStep] = useState(0);

  const analysisSteps = [
    'Scanning semantic structure...',
    'Extracting technical expertise...',
    'Cross-referencing GitHub activity...',
    'Calculating TF-IDF match scores...',
    'Persisting to database...',
    'Finalizing profiles...',
  ];

  const onDrop = useCallback((accepted) => {
    if (mode === 'single') {
      setFiles(accepted.slice(0, 1));
    } else {
      setFiles(accepted.slice(0, 1000));
    }
  }, [mode]);

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
    let p = 0;
    const iv = setInterval(() => {
      p = Math.min(p + Math.random() * 8, 90);
      setProgress(p);
      setCurrentStep(Math.min(Math.floor((p / 100) * analysisSteps.length), analysisSteps.length - 1));
    }, 200);

    try {
      const newCandidate = await addCandidateFromCV(files[0]);
      clearInterval(iv);
      setProgress(100);
      setCurrentStep(analysisSteps.length - 1);
      setTimeout(() => navigate('/candidates'), 800);
    } catch (e) {
      clearInterval(iv);
      setAnalyzing(false);
      setProgress(0);
      toast.error('Failed to start candidate analysis.');
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
      const res = await fetch(`${API}/candidates/upload-bulk`, {
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

  const handleAnalyze = () => (mode === 'single' ? handleSingle() : handleBulk());

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
              className={`flex items-center gap-2 px-5 py-2 rounded-xl text-sm font-medium transition-all ${
                mode === m ? 'bg-violet text-white' : 'bg-surface-2 text-text-2 hover:text-white'
              }`}
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
                  {...getRootProps()}
                  className={`w-full cursor-pointer rounded-2xl border-2 border-dashed p-12 text-center transition-colors ${
                    isDragActive ? 'border-mint bg-mint/5' : 'border-border hover:border-violet/50 hover:bg-surface-3'
                  }`}
                >
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
                </div>

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
                <p className="mb-8 text-center text-text-2 max-w-sm">
                  {mode === 'bulk'
                    ? 'Running TF-IDF scoring on all resumes concurrently and saving to database...'
                    : analysisSteps[currentStep]}
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
    </motion.div>
  );
}
