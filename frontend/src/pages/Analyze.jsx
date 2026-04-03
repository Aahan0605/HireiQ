import React, { useState, useCallback } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { useDropzone } from 'react-dropzone';
import { useNavigate } from 'react-router-dom';
import { UploadCloud, FileText, Loader2, Sparkles } from 'lucide-react';
import MagneticCard from '../components/MagneticCard';
import { addCandidateFromCV } from '../data/candidates';

export default function Analyze() {
  const navigate = useNavigate();
  const [file, setFile] = useState(null);
  const [analyzing, setAnalyzing] = useState(false);
  const [progress, setProgress] = useState(0);
  const [currentStep, setCurrentStep] = useState(0);

  const analysisSteps = [
    "Scanning semantic structure...",
    "Extracting technical expertise...",
    "Cross-referencing GitHub activity...",
    "Correlating LinkedIn milestones...",
    "Calculating match score...",
    "Finalizing deep-dive profile..."
  ];

  const onDrop = useCallback((acceptedFiles) => {
    if (acceptedFiles.length > 0) {
      setFile(acceptedFiles[0]);
    }
  }, []);

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      'application/pdf': ['.pdf'],
      'application/msword': ['.doc'],
      'application/vnd.openxmlformats-officedocument.wordprocessingml.document': ['.docx'],
    },
    maxFiles: 1,
  });

  const handleAnalyze = async () => {
    if (!file) return;
    setAnalyzing(true);
    
    // Mock analysis progress
    let currentProgress = 0;
    const interval = setInterval(() => {
      if (currentProgress < 90) {
        currentProgress += Math.random() * 8;
      }
      setProgress(Math.min(currentProgress, 90));
      const stepIndex = Math.floor((Math.min(currentProgress, 90) / 100) * analysisSteps.length);
      setCurrentStep(Math.min(stepIndex, analysisSteps.length - 1));
    }, 200);

    // Create the new candidate analysis result via API
    const newCandidate = await addCandidateFromCV(file);
    
    clearInterval(interval);
    setProgress(100);
    setCurrentStep(analysisSteps.length - 1);
    
    setTimeout(() => {
      navigate(`/candidate/${newCandidate.id}`);
    }, 800);
  };

  return (
    <div className="flex min-h-screen items-center justify-center p-6 bg-bg overflow-hidden relative">
      <div className="absolute top-1/4 left-1/4 h-96 w-96 rounded-full bg-violet/10 blur-[120px] mix-blend-screen" />
      <div className="absolute bottom-1/4 right-1/4 h-[400px] w-[400px] rounded-full bg-mint/10 blur-[140px] mix-blend-screen" />

      <main className="w-full max-w-2xl relative z-10">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="text-center mb-10"
        >
          <h1 className="font-display text-4xl font-bold tracking-tight text-white mb-3">
            New Candidate Analysis
          </h1>
          <p className="text-text-2 text-lg">Upload a resume to instantly generate an AI-powered insights report.</p>
        </motion.div>

        <MagneticCard className="p-8 border-border bg-surface-2/60 backdrop-blur-xl" maxTilt={3}>
          <AnimatePresence mode="wait">
            {!analyzing ? (
              <motion.div
                key="upload"
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                exit={{ opacity: 0, scale: 0.95 }}
                className="flex flex-col items-center"
              >
                <div
                  {...getRootProps()}
                  className={`w-full cursor-pointer rounded-2xl border-2 border-dashed p-12 text-center transition-colors ${
                    isDragActive ? 'border-mint bg-mint/5' : 'border-border hover:border-violet/50 hover:bg-surface-3'
                  }`}
                >
                  <input {...getInputProps()} />
                  
                  {file ? (
                    <div className="flex flex-col items-center gap-3">
                      <div className="flex h-16 w-16 items-center justify-center rounded-full bg-surface-3 text-violet">
                        <FileText className="h-8 w-8" />
                      </div>
                      <p className="text-white font-medium text-lg">{file.name}</p>
                      <p className="text-text-3 text-sm">{(file.size / 1024 / 1024).toFixed(2)} MB</p>
                    </div>
                  ) : (
                    <div className="flex flex-col items-center gap-3">
                      <div className="flex h-16 w-16 items-center justify-center rounded-full bg-surface-3 text-text-2 group-hover:text-violet transition-colors">
                        <UploadCloud className="h-8 w-8" />
                      </div>
                      <p className="text-white font-medium text-lg mt-2">
                        {isDragActive ? 'Drop resume here' : 'Drag & drop resume here'}
                      </p>
                      <p className="text-text-2 text-sm">Or click to browse files (PDF, DOCX)</p>
                    </div>
                  )}
                </div>

                <div className="mt-8 flex w-full justify-end">
                  <button
                    onClick={handleAnalyze}
                    disabled={!file}
                    className="group relative h-12 inline-flex items-center justify-center overflow-hidden rounded-xl bg-violet px-8 font-medium text-bg transition-transform hover:scale-[1.02] disabled:opacity-50 disabled:hover:scale-100"
                  >
                    <span className="absolute inset-0 bg-gradient-to-r from-mint to-sky opacity-0 transition-opacity group-hover:opacity-100 disabled:opacity-0" />
                    <span className="relative z-10 flex items-center group-hover:text-bg">
                      Start Analysis <Sparkles className="ml-2 h-4 w-4" />
                    </span>
                  </button>
                </div>
              </motion.div>
            ) : (
              <motion.div
                key="analyzing"
                initial={{ opacity: 0, scale: 0.95 }}
                animate={{ opacity: 1, scale: 1 }}
                className="flex flex-col items-center py-12"
              >
                <div className="relative mb-8 flex h-24 w-24 items-center justify-center rounded-full bg-surface-3">
                  <Loader2 className="h-10 w-10 animate-spin text-mint" />
                  <div className="absolute inset-0 rounded-full border border-mint/30 shadow-glow-mint animate-pulse" />
                </div>
                
                <h3 className="mb-2 text-2xl font-bold text-white">Analyzing Profile</h3>
                <p className="mb-8 text-center text-text-2 max-w-sm">
                  Parsing resume history, querying GitHub contributions, and running NLP matching models...
                </p>

                <div className="w-full max-w-sm">
                  <div className="mb-2 flex justify-between text-sm font-medium">
                    <span className="text-text-1">{analysisSteps[currentStep]}</span>
                    <span className="text-mint">{Math.round(progress)}%</span>
                  </div>
                  <div className="h-2 w-full overflow-hidden rounded-full bg-surface-3">
                    <motion.div
                      className="h-full rounded-full bg-gradient-to-r from-mint to-sky"
                      initial={{ width: '0%' }}
                      animate={{ width: `${progress}%` }}
                      transition={{ ease: "linear" }}
                    />
                  </div>
                </div>
              </motion.div>
            )}
          </AnimatePresence>
        </MagneticCard>
      </main>
    </div>
  );
}
