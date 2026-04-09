import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { useNavigate } from 'react-router-dom';
import { Briefcase, MapPin, Clock, Trash2, Edit2, X } from 'lucide-react';

const API = '/api/v1';

const statusStyle = {
  Open:   'bg-green-500/20 text-green-400',
  Closed: 'bg-gray-500/20 text-gray-400',
  Draft:  'bg-amber-500/20 text-amber-400',
};

const EMPTY_FORM = {
  title: '', department: '', location: '',
  employment_type: 'Full-time', experience_required: 1,
  description: '', required_skills: '', status: 'Open',
};

export default function Jobs() {
  const [jobs, setJobs]           = useState([]);
  const [loading, setLoading]     = useState(true);
  const [error, setError]         = useState('');
  const [search, setSearch]       = useState('');
  const [statusFilter, setStatusFilter] = useState('All');
  const [typeFilter, setTypeFilter]     = useState('All');
  const [showModal, setShowModal]       = useState(false);
  const [form, setForm]                 = useState(EMPTY_FORM);
  const [editingJob, setEditingJob]     = useState(null); // null = create, job = edit
  const [submitting, setSubmitting]     = useState(false);
  const navigate = useNavigate();

  const load = () => {
    setLoading(true);
    fetch(`${API}/jobs`)
      .then(r => { if (!r.ok) throw new Error(); return r.json(); })
      .then(data => { setJobs(data); setError(''); })
      .catch(() => setError('Failed to load jobs. Is the backend running?'))
      .finally(() => setLoading(false));
  };

  useEffect(load, []);

  const filtered = jobs.filter(j => {
    const matchSearch = j.title?.toLowerCase().includes(search.toLowerCase()) ||
                        j.department?.toLowerCase().includes(search.toLowerCase());
    const matchStatus = statusFilter === 'All' || j.status === statusFilter;
    const matchType   = typeFilter   === 'All' || j.employment_type === typeFilter;
    return matchSearch && matchStatus && matchType;
  });

  // Open modal for creating a new job
  const openCreate = () => {
    setEditingJob(null);
    setForm(EMPTY_FORM);
    setShowModal(true);
  };

  // Open modal pre-filled for editing an existing job
  const openEdit = (job) => {
    setEditingJob(job);
    setForm({
      title:               job.title || '',
      department:          job.department || '',
      location:            job.location || '',
      employment_type:     job.employment_type || 'Full-time',
      experience_required: job.experience_required || 1,
      description:         job.description || '',
      required_skills:     job.required_skills || '',
      status:              job.status || 'Open',
    });
    setShowModal(true);
  };

  const closeModal = () => {
    setShowModal(false);
    setEditingJob(null);
    setForm(EMPTY_FORM);
  };

  const handleDelete = async (id) => {
    if (!window.confirm('Delete this job?')) return;
    await fetch(`${API}/jobs/${id}`, { method: 'DELETE' });
    setJobs(prev => prev.filter(j => j.id !== id));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setSubmitting(true);
    const body = { ...form, experience_required: Number(form.experience_required) };
    try {
      let res;
      if (editingJob) {
        // PUT — update existing job
        res = await fetch(`${API}/jobs/${editingJob.id}`, {
          method: 'PUT',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(body),
        });
        if (!res.ok) throw new Error();
        const updated = await res.json();
        setJobs(prev => prev.map(j => j.id === editingJob.id ? updated : j));
      } else {
        // POST — create new job
        res = await fetch(`${API}/jobs`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(body),
        });
        if (!res.ok) throw new Error();
        const created = await res.json();
        setJobs(prev => [...prev, created]);
      }
      closeModal();
    } catch {
      alert(`Failed to ${editingJob ? 'update' : 'create'} job. Is the backend running?`);
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <motion.div initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.2 }}
      className="min-h-screen bg-page p-6 lg:p-10">
      <div className="max-w-5xl mx-auto">

        {/* Header */}
        <div className="mb-8 flex items-start justify-between gap-4">
          <div>
            <h1 className="text-3xl font-bold text-theme-1">Job Listings</h1>
            <p className="text-gray-400 text-sm mt-1">Manage open positions and find the best candidates</p>
          </div>
          <button onClick={openCreate}
            className="flex-shrink-0 px-4 py-2.5 bg-emerald-600 hover:bg-emerald-700 text-white text-sm font-semibold rounded-xl transition-all active:scale-95">
            + Post New Job
          </button>
        </div>

        {/* Error */}
        {error && (
          <div className="mb-5 rounded-xl border border-red-500/30 bg-red-500/10 px-4 py-3 text-red-400 text-sm">
            ⚠️ {error}
          </div>
        )}

        {/* Filters */}
        <div className="mb-6 flex flex-col sm:flex-row gap-3">
          <input type="text" placeholder="Search by title or department..."
            value={search} onChange={e => setSearch(e.target.value)}
            className="flex-1 rounded-xl border border-black/10 dark:border-white/10 bg-card py-2.5 px-4 text-theme-1 text-sm outline-none focus:border-emerald-500/40 transition-colors" />
          <select value={statusFilter} onChange={e => setStatusFilter(e.target.value)}
            className="rounded-xl border border-black/10 dark:border-white/10 bg-card py-2.5 px-3 text-theme-2 text-sm outline-none focus:border-emerald-500/40">
            {['All', 'Open', 'Closed', 'Draft'].map(s => <option key={s}>{s}</option>)}
          </select>
          <select value={typeFilter} onChange={e => setTypeFilter(e.target.value)}
            className="rounded-xl border border-black/10 dark:border-white/10 bg-card py-2.5 px-3 text-theme-2 text-sm outline-none focus:border-emerald-500/40">
            {['All', 'Full-time', 'Part-time', 'Contract'].map(t => <option key={t}>{t}</option>)}
          </select>
        </div>

        {/* Job Grid */}
        {loading ? (
          <div className="grid gap-4 sm:grid-cols-2">
            {Array(4).fill(0).map((_, i) => (
              <div key={i} className="h-44 rounded-2xl border border-black/10 dark:border-white/10 bg-card animate-pulse" />
            ))}
          </div>
        ) : filtered.length === 0 ? (
          <div className="py-24 text-center">
            <p className="text-5xl mb-4">💼</p>
            <p className="text-theme-1 font-semibold text-lg mb-2">No job listings yet</p>
            <button onClick={openCreate}
              className="mt-2 px-5 py-2.5 bg-emerald-600 hover:bg-emerald-700 text-white text-sm rounded-xl transition-all">
              Post Your First Job
            </button>
          </div>
        ) : (
          <div className="grid gap-4 sm:grid-cols-2">
            {filtered.map((job, i) => {
              const skills = job.required_skills?.split(',').map(s => s.trim()) || [];
              const visibleSkills = skills.slice(0, 4);
              const extra = skills.length - 4;
              return (
                <motion.div key={job.id}
                  initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0, transition: { delay: i * 0.05 } }}
                  className="bg-card border border-black/10 dark:border-white/10 rounded-2xl p-5 hover:border-emerald-500/30 transition-all flex flex-col gap-3">

                  {/* Title + status */}
                  <div className="flex items-start justify-between gap-2">
                    <h3 className="text-theme-1 font-semibold text-sm leading-snug">{job.title}</h3>
                    <span className={`text-xs px-2.5 py-1 rounded-full font-medium flex-shrink-0 ${statusStyle[job.status] || statusStyle.Draft}`}>
                      {job.status}
                    </span>
                  </div>

                  {/* Badges */}
                  <div className="flex flex-wrap gap-1.5">
                    {[job.department, job.location, job.employment_type].map(b => (
                      <span key={b} className="text-xs px-2 py-0.5 rounded-full bg-black/5 dark:bg-white/5 text-theme-2">{b}</span>
                    ))}
                  </div>

                  <p className="text-theme-3 text-xs">{job.experience_required}+ years experience</p>

                  {/* Skills */}
                  <div className="flex flex-wrap gap-1.5">
                    {visibleSkills.map(s => (
                      <span key={s} className="text-xs px-2 py-0.5 rounded-full bg-emerald-500/15 text-emerald-600 dark:text-emerald-300">{s}</span>
                    ))}
                    {extra > 0 && (
                      <span className="text-xs px-2 py-0.5 rounded-full bg-black/5 dark:bg-white/5 text-theme-3">+{extra} more</span>
                    )}
                  </div>

                  {/* Actions */}
                  <div className="flex items-center justify-between pt-1 border-t border-black/5 dark:border-white/5 mt-auto">
                    <button onClick={() => navigate(`/jobs/${job.id}/matches`)}
                      className="text-xs px-3 py-1.5 rounded-lg bg-emerald-600/25 hover:bg-emerald-600/45 text-emerald-600 dark:text-emerald-300 transition-all font-medium">
                      View Matches →
                    </button>
                    <div className="flex gap-2">
                      {/* Edit button — opens modal pre-filled */}
                      <button
                        onClick={() => openEdit(job)}
                        className="p-1.5 rounded-lg text-gray-400 hover:text-emerald-500 hover:bg-emerald-500/10 transition-all"
                        title="Edit job">
                        <Edit2 size={14} />
                      </button>
                      <button
                        onClick={() => handleDelete(job.id)}
                        className="p-1.5 rounded-lg text-gray-400 hover:text-red-400 hover:bg-red-500/10 transition-all"
                        title="Delete job">
                        <Trash2 size={14} />
                      </button>
                    </div>
                  </div>
                </motion.div>
              );
            })}
          </div>
        )}
      </div>

      {/* Create / Edit Modal */}
      <AnimatePresence>
        {showModal && (
          <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}
            className="fixed inset-0 bg-black/60 backdrop-blur-sm z-50 flex items-center justify-center p-4"
            onClick={closeModal}>
            <motion.div initial={{ scale: 0.95, opacity: 0 }} animate={{ scale: 1, opacity: 1 }} exit={{ scale: 0.95, opacity: 0 }}
              onClick={e => e.stopPropagation()}
              className="bg-card border border-black/10 dark:border-white/10 rounded-2xl p-6 w-full max-w-lg max-h-[90vh] overflow-y-auto shadow-2xl">

              <div className="flex items-center justify-between mb-5">
                <h2 className="text-theme-1 font-semibold text-lg">
                  {editingJob ? 'Edit Job' : 'Post New Job'}
                </h2>
                <button onClick={closeModal} className="text-gray-400 hover:text-theme-1 transition-colors">
                  <X size={18} />
                </button>
              </div>

              <form onSubmit={handleSubmit} className="space-y-4">
                {[
                  { label: 'Job Title',   key: 'title',      type: 'text' },
                  { label: 'Department',  key: 'department', type: 'text' },
                  { label: 'Location',    key: 'location',   type: 'text' },
                ].map(({ label, key, type }) => (
                  <div key={key}>
                    <label className="block text-xs text-theme-2 mb-1">{label}</label>
                    <input type={type} required value={form[key]}
                      onChange={e => setForm(f => ({ ...f, [key]: e.target.value }))}
                      className="w-full rounded-xl border border-black/10 dark:border-white/10 bg-card-2 px-3 py-2 text-theme-1 text-sm outline-none focus:border-emerald-500/40" />
                  </div>
                ))}

                <div className="grid grid-cols-2 gap-3">
                  <div>
                    <label className="block text-xs text-theme-2 mb-1">Employment Type</label>
                    <select value={form.employment_type}
                      onChange={e => setForm(f => ({ ...f, employment_type: e.target.value }))}
                      className="w-full rounded-xl border border-black/10 dark:border-white/10 bg-card-2 px-3 py-2 text-theme-1 text-sm outline-none focus:border-emerald-500/40">
                      {['Full-time', 'Part-time', 'Contract'].map(t => <option key={t}>{t}</option>)}
                    </select>
                  </div>
                  <div>
                    <label className="block text-xs text-theme-2 mb-1">Experience (years)</label>
                    <input type="number" min="0" max="20" required value={form.experience_required}
                      onChange={e => setForm(f => ({ ...f, experience_required: e.target.value }))}
                      className="w-full rounded-xl border border-black/10 dark:border-white/10 bg-card-2 px-3 py-2 text-theme-1 text-sm outline-none focus:border-emerald-500/40" />
                  </div>
                </div>

                <div>
                  <label className="block text-xs text-theme-2 mb-1">Job Description</label>
                  <textarea rows={4} required value={form.description}
                    onChange={e => setForm(f => ({ ...f, description: e.target.value }))}
                    className="w-full rounded-xl border border-black/10 dark:border-white/10 bg-card-2 px-3 py-2 text-theme-1 text-sm outline-none focus:border-emerald-500/40 resize-none" />
                </div>

                <div>
                  <label className="block text-xs text-theme-2 mb-1">Required Skills</label>
                  <input type="text" placeholder="e.g. React, Python, Docker" required value={form.required_skills}
                    onChange={e => setForm(f => ({ ...f, required_skills: e.target.value }))}
                    className="w-full rounded-xl border border-black/10 dark:border-white/10 bg-card-2 px-3 py-2 text-theme-1 text-sm outline-none focus:border-emerald-500/40" />
                </div>

                <div>
                  <label className="block text-xs text-theme-2 mb-1">Status</label>
                  <select value={form.status} onChange={e => setForm(f => ({ ...f, status: e.target.value }))}
                    className="w-full rounded-xl border border-black/10 dark:border-white/10 bg-card-2 px-3 py-2 text-theme-1 text-sm outline-none focus:border-emerald-500/40">
                    {['Open', 'Closed', 'Draft'].map(s => <option key={s}>{s}</option>)}
                  </select>
                </div>

                <div className="flex gap-3 pt-2">
                  <button type="button" onClick={closeModal}
                    className="flex-1 py-2.5 rounded-xl border border-black/10 dark:border-white/10 text-theme-2 text-sm hover:bg-black/5 dark:hover:bg-white/5 transition-all">
                    Cancel
                  </button>
                  <button type="submit" disabled={submitting}
                    className="flex-1 py-2.5 rounded-xl bg-emerald-600 hover:bg-emerald-700 text-white text-sm font-semibold transition-all disabled:opacity-50">
                    {submitting ? (editingJob ? 'Saving...' : 'Posting...') : (editingJob ? 'Save Changes' : 'Post Job')}
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
