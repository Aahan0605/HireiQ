import React from 'react';
import { motion } from 'framer-motion';
import { Settings as SettingsIcon, Bell, Shield, User, Globe, ArrowLeft, Save } from 'lucide-react';
import { Link } from 'react-router-dom';
import { fadeUp, staggerContainer } from '../lib/animations';
import MagneticCard from '../components/MagneticCard';

export default function Settings() {
  return (
    <div className="min-h-screen bg-bg p-6 lg:p-12">
      <div className="mx-auto max-w-4xl">
        <div className="mb-10 flex items-center justify-between">
          <Link to="/dashboard" className="inline-flex items-center text-sm font-medium text-text-2 transition-colors hover:text-white">
            <ArrowLeft className="mr-2 h-4 w-4" />
            Back to Dashboard
          </Link>
          <h1 className="font-display text-4xl font-bold text-white">Settings</h1>
        </div>

        <motion.div
           variants={staggerContainer}
           initial="initial"
           animate="animate"
           className="grid gap-6"
        >
          <motion.div variants={fadeUp}>
            <MagneticCard className="p-8 border-border bg-surface-2/60 backdrop-blur-xl">
              <h2 className="mb-8 text-xl font-semibold text-white flex items-center">
                <User className="mr-3 h-5 w-5 text-violet" /> Profile Information
              </h2>
              <div className="grid gap-6 sm:grid-cols-2">
                <div className="space-y-2">
                  <label className="text-sm font-medium text-text-2">Display Name</label>
                  <input type="text" className="w-full rounded-xl border border-border bg-surface-3 px-4 py-2.5 text-white focus:border-violet/50 outline-none" defaultValue="Admin User" />
                </div>
                <div className="space-y-2">
                  <label className="text-sm font-medium text-text-2">Email Address</label>
                  <input type="email" className="w-full rounded-xl border border-border bg-surface-3 px-4 py-2.5 text-white focus:border-violet/50 outline-none" defaultValue="admin@hireiq.ai" />
                </div>
              </div>
            </MagneticCard>
          </motion.div>

          <motion.div variants={fadeUp}>
            <MagneticCard className="p-8 border-border bg-surface-2/60 backdrop-blur-xl">
              <h2 className="mb-8 text-xl font-semibold text-white flex items-center">
                <Bell className="mr-3 h-5 w-5 text-mint" /> Notifications
              </h2>
              <div className="space-y-4">
                {[
                  { label: 'Email alerts for new matches', active: true },
                  { label: 'Weekly summary reports', active: true },
                  { label: 'Platform update notifications', active: false },
                ].map((item, i) => (
                  <div key={i} className="flex items-center justify-between">
                    <span className="text-sm text-text-1">{item.label}</span>
                    <button className={`h-6 w-11 rounded-full transition-colors relative ${item.active ? 'bg-violet' : 'bg-surface-3'}`}>
                      <span className={`absolute top-1 h-4 w-4 rounded-full bg-white transition-all ${item.active ? 'right-1' : 'left-1'}`} />
                    </button>
                  </div>
                ))}
              </div>
            </MagneticCard>
          </motion.div>

          <motion.div variants={fadeUp}>
            <MagneticCard className="p-8 border-border bg-surface-2/60 backdrop-blur-xl">
              <h2 className="mb-8 text-xl font-semibold text-white flex items-center">
                <Globe className="mr-3 h-5 w-5 text-sky" /> Integrations
              </h2>
              <div className="grid gap-6">
                <div className="flex items-center justify-between rounded-xl bg-surface-3 p-4">
                  <div className="flex items-center gap-3">
                    <div className="h-10 w-10 flex items-center justify-center rounded-lg bg-[#24292e]">
                       <SettingsIcon className="h-5 w-5 text-white" />
                    </div>
                    <div>
                        <p className="font-medium text-white text-sm">GitHub Connector</p>
                        <p className="text-xs text-text-3">Connected as @hireiq-bot</p>
                    </div>
                  </div>
                  <button className="text-sm font-medium text-amber hover:underline">Disconnect</button>
                </div>
              </div>
            </MagneticCard>
          </motion.div>

          <div className="mt-4 flex justify-end">
            <button className="inline-flex h-12 items-center rounded-xl bg-violet px-8 font-semibold text-bg transition-transform hover:scale-105 active:scale-95 shadow-glow-violet">
              <Save className="mr-2 h-4 w-4" />
              Save Changes
            </button>
          </div>
        </motion.div>
      </div>
    </div>
  );
}
