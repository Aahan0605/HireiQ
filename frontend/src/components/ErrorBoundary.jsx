import React from 'react';
import { ShieldAlert, RefreshCw, LayoutDashboard } from 'lucide-react';

export default class ErrorBoundary extends React.Component {
  constructor(props) {
    super(props);
    this.state = { hasError: false, error: null };
  }

  static getDerivedStateFromError(error) {
    return { hasError: true, error };
  }

  componentDidCatch(error, errorInfo) {
    console.error("ErrorBoundary caught an unhandled rendering exception:", error, errorInfo);
  }

  handleReset = () => {
    // Hard redirect to dashboard to clear any corrupted React state
    window.location.href = '/dashboard';
  };

  handleReload = () => {
    window.location.reload();
  };

  render() {
    if (this.state.hasError) {
      return (
        <div className="min-h-screen bg-[#0d0d1a] flex items-center justify-center p-6 text-[var(--text-1)]">
          <div className="absolute top-1/4 left-1/4 h-96 w-96 rounded-full bg-red-500/10 blur-[120px] mix-blend-screen pointer-events-none" />
          <div className="absolute bottom-1/4 right-1/4 h-[400px] w-[400px] rounded-full bg-violet/10 blur-[140px] mix-blend-screen pointer-events-none" />
          
          <div className="relative z-10 max-w-md w-full bg-[#13131f] border border-red-500/20 rounded-2xl p-8 text-center shadow-2xl backdrop-blur-xl">
            <div className="mx-auto mb-4 flex h-16 w-16 items-center justify-center rounded-full bg-red-500/10 text-red-400 border border-red-500/20 shadow-glow-rose/10">
              <ShieldAlert className="h-8 w-8" />
            </div>
            
            <h1 className="text-xl font-bold text-white mb-2">Application Error</h1>
            <p className="text-gray-400 text-sm leading-relaxed mb-6">
              Something went wrong while rendering this section. Our system has logged the diagnostic exception.
            </p>

            {this.state.error?.message && (
              <div className="mb-6 p-4 rounded-xl border border-white/5 bg-black/40 text-left">
                <span className="text-[10px] uppercase font-bold text-red-400 block mb-1">Diagnostic Log:</span>
                <p className="text-xs text-gray-300 font-mono break-all line-clamp-3">
                  {this.state.error.message}
                </p>
              </div>
            )}

            <div className="flex flex-col sm:flex-row gap-3">
              <button
                onClick={this.handleReload}
                className="flex-1 py-2.5 rounded-xl border border-white/10 hover:border-white/20 text-xs font-semibold text-gray-300 hover:text-white transition-all duration-200 flex items-center justify-center gap-1.5"
              >
                <RefreshCw size={13} /> Retry Page
              </button>
              <button
                onClick={this.handleReset}
                className="flex-1 py-2.5 rounded-xl bg-gradient-to-r from-emerald-500 to-cyan-500 font-bold text-white shadow-lg shadow-emerald-500/10 hover:scale-[1.02] active:scale-95 transition-all duration-200 text-xs flex items-center justify-center gap-1.5"
              >
                <LayoutDashboard size={13} /> Go to Dashboard
              </button>
            </div>
          </div>
        </div>
      );
    }

    return this.props.children;
  }
}
