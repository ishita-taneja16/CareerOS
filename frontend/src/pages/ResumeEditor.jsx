import React, { useState, useEffect } from 'react';
import { apiService } from '../services/api';
import { 
  Upload, Trash2, Download, Check, Save, Loader2, 
  Sparkles, AlertTriangle, CheckCircle2, XCircle, FileText, 
  Search, RefreshCw, Edit2, FileJson, CheckSquare, Plus 
} from 'lucide-react';

export default function ResumeEditor({ 
  resume,
  onResumeLoaded, 
  activeResumeId, 
  setActiveResumeId, 
  libraryResumes = [], 
  onRefreshLibrary,
  resumeLoading,
  resumeError,
  onRetryLoadResume
}) {
  const [resumeData, setResumeData] = useState(null);
  
  const [loading, setLoading] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [saving, setSaving] = useState(false);
  const [parsingId, setParsingId] = useState('');
  const [message, setMessage] = useState('');

  // Inline rename state
  const [renamingId, setRenamingId] = useState('');
  const [renameValue, setRenameValue] = useState('');

  // Search & Filter state
  const [searchQuery, setSearchQuery] = useState('');
  const [statusFilter, setStatusFilter] = useState('all'); // all, parsed, not_parsed
  const [formatFilter, setFormatFilter] = useState('all'); // all, pdf, docx

  // ATS Analysis State
  const [jobDescription, setJobDescription] = useState('');
  const [atsResult, setAtsResult] = useState(null);
  const [analyzingATS, setAnalyzingATS] = useState(false);

  // Sync state when active resume changes
  useEffect(() => {
    setResumeData(resume);
  }, [resume]);

  // Auto-refresh ATS score when active resume changes
  useEffect(() => {
    if (resumeData && jobDescription.trim()) {
      const timer = setTimeout(() => {
        handleAnalyzeATS();
      }, 300);
      return () => clearTimeout(timer);
    } else {
      setAtsResult(null);
    }
  }, [resumeData]);

  // Upload handler
  const handleFileUpload = async (e) => {
    const file = e.target.files[0];
    if (!file) return;
    setUploading(true);
    setMessage('');
    try {
      const res = await apiService.uploadResumeToLibrary(file);
      await onRefreshLibrary();
      
      // Auto-activate the newly uploaded resume
      // Fetch latest list to get the id
      const latestRes = await apiService.getLibraryResumes();
      const newest = (latestRes.data || []).reduce((prev, current) => {
        return (new Date(prev.upload_date) > new Date(current.upload_date)) ? prev : current;
      }, { upload_date: '1970-01-01T00:00:00' });
      
      if (newest && newest.id) {
        await setActiveResumeId(newest.id);
      }
      setResumeData(res.data);
      setMessage('Resume uploaded and parsed successfully!');
    } catch (err) {
      setMessage('Failed to upload/parse resume: ' + (err.response?.data?.detail || err.message));
    } finally {
      setUploading(false);
    }
  };

  const handleParseResume = async (resumeId) => {
    setParsingId(resumeId);
    setMessage('');
    try {
      const res = await apiService.parseExistingLibraryResume(resumeId);
      await onRefreshLibrary();
      if (resumeId === activeResumeId) {
        setResumeData(res.data);
      }
      setMessage('Resume parsed successfully!');
    } catch (err) {
      setMessage('Failed to parse resume: ' + (err.response?.data?.detail || err.message));
    } finally {
      setParsingId('');
    }
  };

  const handleRename = async (resumeId) => {
    if (!renameValue.trim()) return;
    try {
      await apiService.renameLibraryResume(resumeId, renameValue);
      setRenamingId('');
      await onRefreshLibrary();
      setMessage('Resume renamed successfully.');
    } catch (err) {
      setMessage('Failed to rename: ' + (err.response?.data?.detail || err.message));
    }
  };

  const handleDelete = async (resumeId) => {
    if (!confirm('Are you sure you want to delete this resume from your library?')) return;
    try {
      await apiService.deleteLibraryResume(resumeId);
      if (resumeId === activeResumeId) {
        setActiveResumeId('');
        setResumeData(null);
      }
      await onRefreshLibrary();
      setMessage('Resume deleted.');
    } catch (err) {
      setMessage('Failed to delete: ' + (err.response?.data?.detail || err.message));
    }
  };

  const handleSaveLocal = async () => {
    if (!resumeData) return;
    setSaving(true);
    setMessage('');
    try {
      // 1. If there is an active resume in the library, save it back to disk on FastAPI
      if (activeResumeId) {
        await apiService.saveLibraryResumeData(activeResumeId, resumeData);
        await onRefreshLibrary();
      }
      
      // 2. Also update local storage and notify context
      localStorage.setItem('parsed_resume', JSON.stringify(resumeData));
      if (onResumeLoaded) {
        onResumeLoaded(resumeData);
      }
      setMessage('Changes saved persistently!');
    } catch (err) {
      setMessage('Failed to save changes: ' + (err.response?.data?.detail || err.message));
    } finally {
      setSaving(false);
    }
  };

  const handleExport = async (format) => {
    if (!resumeData) return;
    try {
      setSaving(true);
      const blobRes = format === 'pdf' 
        ? await apiService.exportPDF(resumeData) 
        : await apiService.exportDOCX(resumeData);
      
      const blob = new Blob([blobRes.data], { 
        type: format === 'pdf' 
          ? 'application/pdf' 
          : 'application/vnd.openxmlformats-officedocument.wordprocessingml.document' 
      });
      const url = window.URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', `resume_export.${format}`);
      document.body.appendChild(link);
      link.click();
      link.remove();
    } catch (err) {
      console.error(err);
      setMessage('Export failed.');
    } finally {
      setSaving(false);
    }
  };

  const handleAnalyzeATS = async () => {
    if (!resumeData) {
      setMessage('Please select or upload a resume first.');
      return;
    }
    if (!jobDescription.trim()) {
      setMessage('Please enter a job description to analyze against.');
      return;
    }
    setAnalyzingATS(true);
    setAtsResult(null);
    setMessage('');
    try {
      const res = await apiService.evaluateATS(resumeData, jobDescription);
      setAtsResult(res.data);
    } catch (err) {
      setMessage('ATS Analysis failed: ' + (err.response?.data?.detail || err.message));
    } finally {
      setAnalyzingATS(false);
    }
  };

  const formatDate = (dateStr) => {
    if (!dateStr) return 'N/A';
    const date = new Date(dateStr);
    return date.toLocaleDateString('en-US', {
      month: 'short',
      day: 'numeric',
      year: 'numeric'
    });
  };

  // Filter resumes lists
  const filteredResumes = (libraryResumes || []).filter(r => {
    const matchQuery = r.filename.toLowerCase().includes(searchQuery.toLowerCase());
    
    const matchStatus = 
      statusFilter === 'all' ? true :
      statusFilter === 'parsed' ? r.parsed : !r.parsed;
      
    const matchFormat =
      formatFilter === 'all' ? true :
      r.file_type.toLowerCase() === formatFilter.toLowerCase();
      
    return matchQuery && matchStatus && matchFormat;
  });

  return (
    <div className="grid grid-cols-1 xl:grid-cols-4 gap-6 items-start">
      
      {/* Sidebar - Resume Library */}
      <div className="bg-[#151d30] border border-[#232e48] rounded-xl p-5 space-y-5 xl:col-span-1">
        <div className="flex items-center justify-between border-b border-[#232e48]/60 pb-3">
          <h2 className="text-xs font-bold text-gray-200 uppercase tracking-wider flex items-center gap-1.5">
            <FileJson className="w-4 h-4 text-indigo-400" />
            Resume Library
          </h2>
          <label className="flex items-center gap-1.5 px-2.5 py-1 rounded bg-indigo-600 hover:bg-indigo-500 text-white text-[10px] font-bold cursor-pointer transition">
            {uploading ? <Loader2 className="w-3 h-3 animate-spin" /> : <Plus className="w-3 h-3" />}
            <span>Upload New</span>
            <input type="file" onChange={handleFileUpload} accept=".pdf,.docx,.doc" className="hidden" />
          </label>
        </div>

        {/* Search */}
        <div className="relative">
          <Search className="absolute left-2.5 top-2.5 w-3.5 h-3.5 text-gray-500" />
          <input
            type="text"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            placeholder="Search resumes..."
            className="w-full bg-[#0b0f19] border border-[#232e48] rounded-lg py-1.5 pl-8 pr-3 text-xs text-gray-300 focus:outline-none focus:border-indigo-500"
          />
        </div>

        {/* Filters */}
        <div className="space-y-2">
          {/* Status filters */}
          <div className="flex gap-1">
            {['all', 'parsed', 'not_parsed'].map(status => (
              <button
                key={status}
                onClick={() => setStatusFilter(status)}
                className={`flex-1 text-[9px] font-bold uppercase py-1 rounded transition border ${
                  statusFilter === status 
                    ? 'bg-indigo-600/10 text-indigo-400 border-indigo-500/20' 
                    : 'bg-[#0b0f19] text-gray-400 border-transparent hover:text-gray-200'
                }`}
              >
                {status.replace('_', ' ')}
              </button>
            ))}
          </div>
          {/* Format filters */}
          <div className="flex gap-1">
            {['all', 'pdf', 'docx'].map(format => (
              <button
                key={format}
                onClick={() => setFormatFilter(format)}
                className={`flex-1 text-[9px] font-bold uppercase py-1 rounded transition border ${
                  formatFilter === format 
                    ? 'bg-indigo-600/10 text-indigo-400 border-indigo-500/20' 
                    : 'bg-[#0b0f19] text-gray-400 border-transparent hover:text-gray-200'
                }`}
              >
                {format}
              </button>
            ))}
          </div>
        </div>

        {/* List of resumes */}
        <div className="space-y-3 max-h-[500px] overflow-y-auto pr-1">
          {filteredResumes.length > 0 ? (
            filteredResumes.map(r => {
              const isActive = r.id === activeResumeId;
              const isRenaming = renamingId === r.id;
              
              return (
                <div 
                  key={r.id}
                  className={`p-3.5 rounded-lg border transition space-y-3 ${
                    isActive 
                      ? 'bg-indigo-600/10 border-indigo-500/40 text-indigo-200' 
                      : 'bg-[#0b0f19]/60 border-[#232e48] text-gray-300 hover:border-gray-700'
                  }`}
                >
                  {/* Title & Icon */}
                  <div className="flex gap-2.5 items-start">
                    <FileText className={`w-8 h-8 shrink-0 ${isActive ? 'text-indigo-400' : 'text-gray-500'}`} />
                    
                    <div className="flex-1 min-w-0 space-y-0.5">
                      {isRenaming ? (
                        <div className="flex gap-1.5 items-center">
                          <input
                            type="text"
                            value={renameValue}
                            onChange={(e) => setRenameValue(e.target.value)}
                            className="bg-[#0b0f19] border border-indigo-500 rounded px-1.5 py-0.5 text-xs text-gray-200 w-full"
                          />
                          <button 
                            onClick={() => handleRename(r.id)}
                            className="text-emerald-400 hover:text-emerald-300 text-xs font-bold"
                          >
                            Save
                          </button>
                          <button 
                            onClick={() => setRenamingId('')}
                            className="text-gray-500 hover:text-gray-300 text-xs"
                          >
                            ×
                          </button>
                        </div>
                      ) : (
                        <h4 className="text-xs font-semibold truncate" title={r.filename}>{r.filename}</h4>
                      )}
                      
                      <div className="text-[9px] text-gray-500 space-y-0.5">
                        <p>Uploaded: {formatDate(r.upload_date)}</p>
                        <p>Modified: {formatDate(r.last_modified)}</p>
                      </div>
                    </div>
                  </div>

                  {/* Badges & Actions */}
                  <div className="flex items-center justify-between border-t border-[#232e48]/40 pt-2.5 gap-2">
                    <span className={`text-[9px] px-1.5 py-0.5 rounded font-bold uppercase ${
                      r.parsed 
                        ? 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/20' 
                        : 'bg-rose-500/10 text-rose-400 border border-rose-500/20'
                    }`}>
                      {r.parsed ? 'Parsed' : 'Not Parsed'}
                    </span>

                    <div className="flex gap-1">
                      {/* Rename */}
                      <button
                        onClick={() => { setRenamingId(r.id); setRenameValue(r.filename); }}
                        className="p-1 text-gray-500 hover:text-indigo-400 transition"
                        title="Rename Resume"
                      >
                        <Edit2 className="w-3 h-3" />
                      </button>

                      {/* Download */}
                      <a
                        href={apiService.getLibraryResumeDownloadUrl(r.id)}
                        className="p-1 text-gray-500 hover:text-indigo-400 transition"
                        title="Download Original File"
                        download
                      >
                        <Download className="w-3 h-3" />
                      </a>

                      {/* Re-Parse */}
                      <button
                        onClick={() => handleParseResume(r.id)}
                        disabled={parsingId === r.id}
                        className="p-1 text-gray-500 hover:text-indigo-400 transition"
                        title="Re-Parse Resume"
                      >
                        <RefreshCw className={`w-3 h-3 ${parsingId === r.id ? 'animate-spin text-indigo-400' : ''}`} />
                      </button>

                      {/* Delete */}
                      <button
                        onClick={() => handleDelete(r.id)}
                        className="p-1 text-gray-500 hover:text-rose-400 transition"
                        title="Delete Resume"
                      >
                        <Trash2 className="w-3 h-3" />
                      </button>
                    </div>
                  </div>

                  {/* Primary Loader / Action Button */}
                  <div className="pt-1.5">
                    {r.parsed ? (
                      isActive ? (
                        <div className="w-full text-center text-[10px] font-bold bg-indigo-600/20 border border-indigo-500/30 text-indigo-400 py-1.5 rounded-lg flex items-center justify-center gap-1">
                          <Check className="w-3.5 h-3.5" />
                          Active Resume
                        </div>
                      ) : (
                        <button
                          onClick={() => setActiveResumeId(r.id)}
                          className="w-full text-center text-[10px] font-bold bg-[#0b0f19] hover:bg-[#131b2e] border border-[#232e48] text-gray-300 hover:text-white py-1.5 rounded-lg transition"
                        >
                          Load Resume
                        </button>
                      )
                    ) : (
                      <button
                        onClick={() => handleParseResume(r.id)}
                        disabled={parsingId === r.id}
                        className="w-full text-center text-[10px] font-bold bg-indigo-600 hover:bg-indigo-500 text-white py-1.5 rounded-lg transition flex items-center justify-center gap-1"
                      >
                        {parsingId === r.id ? (
                          <>
                            <Loader2 className="w-3 h-3 animate-spin text-white" />
                            Parsing...
                          </>
                        ) : (
                          'Parse Resume'
                        )}
                      </button>
                    )}
                  </div>
                </div>
              );
            })
          ) : (
            <div className="text-center py-6 text-gray-500 text-[11px] italic">
              No matching resumes.
            </div>
          )}
        </div>
      </div>

      {/* Editor Content Panel */}
      <div className="bg-[#151d30] border border-[#232e48] rounded-xl p-6 xl:col-span-3 space-y-6">
        {message && (
          <div className="p-3 bg-indigo-500/10 border border-indigo-500/20 text-indigo-400 text-xs rounded-lg text-center flex justify-between items-center z-10 relative">
            <span>{message}</span>
            <button onClick={() => setMessage('')} className="text-gray-400 hover:text-gray-200">×</button>
          </div>
        )}

        {resumeError ? (
          <div className="p-4 bg-rose-500/10 border border-rose-500/20 text-rose-400 text-xs rounded-xl flex items-center justify-between gap-4">
            <div className="flex items-center gap-2">
              <XCircle className="w-5 h-5 shrink-0 text-rose-400" />
              <span>{resumeError}</span>
            </div>
            <button 
              onClick={onRetryLoadResume}
              className="px-3 py-1 bg-rose-600 hover:bg-rose-500 text-white rounded text-[10px] font-bold transition shrink-0"
            >
              Retry
            </button>
          </div>
        ) : resumeLoading ? (
          <div className="flex items-center justify-center min-h-[400px]">
            <Loader2 className="w-8 h-8 text-indigo-500 animate-spin" />
          </div>
        ) : resumeData ? (
          <div className="space-y-6">
            {/* Control Bar */}
            <div className="flex justify-between items-center border-b border-[#232e48]/60 pb-4">
              <div>
                <h2 className="text-sm font-semibold text-gray-200">Structured Resume Data</h2>
                <p className="text-[10px] text-gray-500">Edit fields and click Save Changes to persist backend files.</p>
              </div>
              
              <div className="flex gap-2">
                <button
                  onClick={() => handleExport('pdf')}
                  disabled={saving}
                  className="bg-slate-800 hover:bg-slate-700 text-gray-200 px-3 py-1.5 rounded-lg text-xs font-semibold transition flex items-center gap-1.5"
                >
                  <Download className="w-3.5 h-3.5" />
                  PDF
                </button>
                <button
                  onClick={() => handleExport('docx')}
                  disabled={saving}
                  className="bg-slate-800 hover:bg-slate-700 text-gray-200 px-3 py-1.5 rounded-lg text-xs font-semibold transition flex items-center gap-1.5"
                >
                  <Download className="w-3.5 h-3.5" />
                  Word
                </button>
                <button
                  onClick={handleSaveLocal}
                  disabled={saving}
                  className="bg-indigo-600 hover:bg-indigo-500 text-white px-3 py-1.5 rounded-lg text-xs font-semibold transition flex items-center gap-1.5"
                >
                  {saving ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : <Save className="w-3.5 h-3.5" />}
                  Save Changes
                </button>
              </div>
            </div>

            {/* Editable Form Fields */}
            <div className="space-y-6">
              {/* Contact Info */}
              <div className="bg-[#0b0f19] border border-[#232e48] rounded-xl p-5 space-y-4">
                <h3 className="text-sm font-semibold text-indigo-400">Contact Details</h3>
                <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                  <div>
                    <label className="text-[10px] text-gray-500 mb-1 block">Full Name</label>
                    <input
                      type="text"
                      value={resumeData.contact_info?.name || ''}
                      onChange={(e) => setResumeData({
                        ...resumeData,
                        contact_info: { ...resumeData.contact_info, name: e.target.value }
                      })}
                      className="w-full bg-[#151d30] border border-[#232e48] rounded px-3 py-2 text-xs text-gray-200 focus:outline-none focus:border-indigo-500"
                    />
                  </div>
                  <div>
                    <label className="text-[10px] text-gray-500 mb-1 block">Email</label>
                    <input
                      type="email"
                      value={resumeData.contact_info?.email || ''}
                      onChange={(e) => setResumeData({
                        ...resumeData,
                        contact_info: { ...resumeData.contact_info, email: e.target.value }
                      })}
                      className="w-full bg-[#151d30] border border-[#232e48] rounded px-3 py-2 text-xs text-gray-200 focus:outline-none focus:border-indigo-500"
                    />
                  </div>
                  <div>
                    <label className="text-[10px] text-gray-500 mb-1 block">Phone</label>
                    <input
                      type="text"
                      value={resumeData.contact_info?.phone || ''}
                      onChange={(e) => setResumeData({
                        ...resumeData,
                        contact_info: { ...resumeData.contact_info, phone: e.target.value }
                      })}
                      className="w-full bg-[#151d30] border border-[#232e48] rounded px-3 py-2 text-xs text-gray-200 focus:outline-none focus:border-indigo-500"
                    />
                  </div>
                </div>
              </div>

              {/* Skills */}
              <div className="bg-[#0b0f19] border border-[#232e48] rounded-xl p-5 space-y-4">
                <h3 className="text-sm font-semibold text-indigo-400">Technical Skills</h3>
                <div>
                  <label className="text-[10px] text-gray-500 mb-1 block">Skills (Comma-separated)</label>
                  <input
                    type="text"
                    value={resumeData.skills?.join(', ') || ''}
                    onChange={(e) => setResumeData({
                      ...resumeData,
                      skills: e.target.value.split(',').map(s => s.trim()).filter(Boolean)
                    })}
                    className="w-full bg-[#151d30] border border-[#232e48] rounded px-3 py-2 text-xs text-gray-200 focus:outline-none focus:border-indigo-500"
                  />
                </div>
              </div>

              {/* Experience */}
              <div className="bg-[#0b0f19] border border-[#232e48] rounded-xl p-5 space-y-4">
                <div className="flex justify-between items-center">
                  <h3 className="text-sm font-semibold text-indigo-400">Professional Experience</h3>
                  <button
                    onClick={() => setResumeData({
                      ...resumeData,
                      experiences: [...(resumeData.experiences || []), { company: '', role: '', start_date: '', end_date: '', description_bullets: [] }]
                    })}
                    className="text-[10px] text-indigo-400 hover:text-indigo-300 font-semibold flex items-center gap-1"
                  >
                    + Add Experience
                  </button>
                </div>
                {resumeData.experiences?.map((exp, index) => (
                  <div key={index} className="border-b border-[#232e48] pb-4 last:border-0 last:pb-0 space-y-3">
                    <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                      <div>
                        <label className="text-[10px] text-gray-500 mb-1 block">Company</label>
                        <input
                          type="text"
                          value={exp.company || ''}
                          onChange={(e) => {
                            const newExp = [...(resumeData.experiences || [])];
                            newExp[index] = { ...newExp[index], company: e.target.value };
                            setResumeData({ ...resumeData, experiences: newExp });
                          }}
                          className="w-full bg-[#151d30] border border-[#232e48] rounded px-2.5 py-1.5 text-xs text-gray-200 focus:outline-none focus:border-indigo-500"
                        />
                      </div>
                      <div>
                        <label className="text-[10px] text-gray-500 mb-1 block">Role Title</label>
                        <input
                          type="text"
                          value={exp.role || ''}
                          onChange={(e) => {
                            const newExp = [...(resumeData.experiences || [])];
                            newExp[index] = { ...newExp[index], role: e.target.value };
                            setResumeData({ ...resumeData, experiences: newExp });
                          }}
                          className="w-full bg-[#151d30] border border-[#232e48] rounded px-2.5 py-1.5 text-xs text-gray-200 focus:outline-none focus:border-indigo-500"
                        />
                      </div>
                      <div>
                        <label className="text-[10px] text-gray-500 mb-1 block">Start Date</label>
                        <input
                          type="text"
                          value={exp.start_date || ''}
                          onChange={(e) => {
                            const newExp = [...(resumeData.experiences || [])];
                            newExp[index] = { ...newExp[index], start_date: e.target.value };
                            setResumeData({ ...resumeData, experiences: newExp });
                          }}
                          className="w-full bg-[#151d30] border border-[#232e48] rounded px-2.5 py-1.5 text-xs text-gray-200 focus:outline-none focus:border-indigo-500"
                        />
                      </div>
                      <div>
                        <label className="text-[10px] text-gray-500 mb-1 block">End Date</label>
                        <input
                          type="text"
                          value={exp.end_date || ''}
                          onChange={(e) => {
                            const newExp = [...(resumeData.experiences || [])];
                            newExp[index] = { ...newExp[index], end_date: e.target.value };
                            setResumeData({ ...resumeData, experiences: newExp });
                          }}
                          className="w-full bg-[#151d30] border border-[#232e48] rounded px-2.5 py-1.5 text-xs text-gray-200 focus:outline-none focus:border-indigo-500"
                        />
                      </div>
                    </div>
                    <div>
                      <label className="text-[10px] text-gray-500 mb-1 block">Description Bullets (One per line)</label>
                      <textarea
                        rows={3}
                        value={exp.description_bullets?.join('\n') || ''}
                        onChange={(e) => {
                          const newExp = [...(resumeData.experiences || [])];
                          newExp[index] = { ...newExp[index], description_bullets: e.target.value.split('\n') };
                          setResumeData({ ...resumeData, experiences: newExp });
                        }}
                        className="w-full bg-[#151d30] border border-[#232e48] rounded px-2.5 py-1.5 text-xs text-gray-200 focus:outline-none focus:border-indigo-500"
                      />
                    </div>
                  </div>
                ))}
              </div>

              {/* Education */}
              <div className="bg-[#0b0f19] border border-[#232e48] rounded-xl p-5 space-y-4">
                <div className="flex justify-between items-center">
                  <h3 className="text-sm font-semibold text-indigo-400">Education</h3>
                  <button
                    onClick={() => setResumeData({
                      ...resumeData,
                      education: [...(resumeData.education || []), { institution: '', degree: '', field_of_study: '', location: '', start_date: '', end_date: '', gpa: '' }]
                    })}
                    className="text-[10px] text-indigo-400 hover:text-indigo-300 font-semibold flex items-center gap-1"
                  >
                    + Add Education
                  </button>
                </div>
                {resumeData.education?.map((edu, index) => (
                  <div key={index} className="border-b border-[#232e48] pb-4 last:border-0 last:pb-0 space-y-3">
                    <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                      <div>
                        <label className="text-[10px] text-gray-500 mb-1 block">Institution</label>
                        <input
                          type="text"
                          value={edu.institution || ''}
                          onChange={(e) => {
                            const newEdu = [...(resumeData.education || [])];
                            newEdu[index] = { ...newEdu[index], institution: e.target.value };
                            setResumeData({ ...resumeData, education: newEdu });
                          }}
                          className="w-full bg-[#151d30] border border-[#232e48] rounded px-2.5 py-1.5 text-xs text-gray-200 focus:outline-none focus:border-indigo-500"
                        />
                      </div>
                      <div>
                        <label className="text-[10px] text-gray-500 mb-1 block">Degree</label>
                        <input
                          type="text"
                          value={edu.degree || ''}
                          onChange={(e) => {
                            const newEdu = [...(resumeData.education || [])];
                            newEdu[index] = { ...newEdu[index], degree: e.target.value };
                            setResumeData({ ...resumeData, education: newEdu });
                          }}
                          className="w-full bg-[#151d30] border border-[#232e48] rounded px-2.5 py-1.5 text-xs text-gray-200 focus:outline-none focus:border-indigo-500"
                        />
                      </div>
                      <div>
                        <label className="text-[10px] text-gray-500 mb-1 block">Field of Study</label>
                        <input
                          type="text"
                          value={edu.field_of_study || ''}
                          onChange={(e) => {
                            const newEdu = [...(resumeData.education || [])];
                            newEdu[index] = { ...newEdu[index], field_of_study: e.target.value };
                            setResumeData({ ...resumeData, education: newEdu });
                          }}
                          className="w-full bg-[#151d30] border border-[#232e48] rounded px-2.5 py-1.5 text-xs text-gray-200 focus:outline-none focus:border-indigo-500"
                        />
                      </div>
                      <div>
                        <label className="text-[10px] text-gray-500 mb-1 block">Location</label>
                        <input
                          type="text"
                          value={edu.location || ''}
                          onChange={(e) => {
                            const newEdu = [...(resumeData.education || [])];
                            newEdu[index] = { ...newEdu[index], location: e.target.value };
                            setResumeData({ ...resumeData, education: newEdu });
                          }}
                          className="w-full bg-[#151d30] border border-[#232e48] rounded px-2.5 py-1.5 text-xs text-gray-200 focus:outline-none focus:border-indigo-500"
                        />
                      </div>
                    </div>
                    <div className="grid grid-cols-3 gap-4">
                      <div>
                        <label className="text-[10px] text-gray-500 mb-1 block">Start Date</label>
                        <input
                          type="text"
                          value={edu.start_date || ''}
                          onChange={(e) => {
                            const newEdu = [...(resumeData.education || [])];
                            newEdu[index] = { ...newEdu[index], start_date: e.target.value };
                            setResumeData({ ...resumeData, education: newEdu });
                          }}
                          className="w-full bg-[#151d30] border border-[#232e48] rounded px-2.5 py-1.5 text-xs text-gray-200 focus:outline-none focus:border-indigo-500"
                        />
                      </div>
                      <div>
                        <label className="text-[10px] text-gray-500 mb-1 block">End Date</label>
                        <input
                          type="text"
                          value={edu.end_date || ''}
                          onChange={(e) => {
                            const newEdu = [...(resumeData.education || [])];
                            newEdu[index] = { ...newEdu[index], end_date: e.target.value };
                            setResumeData({ ...resumeData, education: newEdu });
                          }}
                          className="w-full bg-[#151d30] border border-[#232e48] rounded px-2.5 py-1.5 text-xs text-gray-200 focus:outline-none focus:border-indigo-500"
                        />
                      </div>
                      <div>
                        <label className="text-[10px] text-gray-500 mb-1 block">GPA</label>
                        <input
                          type="text"
                          value={edu.gpa || ''}
                          onChange={(e) => {
                            const newEdu = [...(resumeData.education || [])];
                            newEdu[index] = { ...newEdu[index], gpa: e.target.value };
                            setResumeData({ ...resumeData, education: newEdu });
                          }}
                          className="w-full bg-[#151d30] border border-[#232e48] rounded px-2.5 py-1.5 text-xs text-gray-200 focus:outline-none focus:border-indigo-500"
                        />
                      </div>
                    </div>
                  </div>
                ))}
              </div>

              {/* Projects */}
              <div className="bg-[#0b0f19] border border-[#232e48] rounded-xl p-5 space-y-4">
                <div className="flex justify-between items-center">
                  <h3 className="text-sm font-semibold text-indigo-400">Projects</h3>
                  <button
                    onClick={() => setResumeData({
                      ...resumeData,
                      projects: [...(resumeData.projects || []), { project_name: '', technologies: [], description_bullets: [] }]
                    })}
                    className="text-[10px] text-indigo-400 hover:text-indigo-300 font-semibold flex items-center gap-1"
                  >
                    + Add Project
                  </button>
                </div>
                {resumeData.projects?.map((proj, index) => (
                  <div key={index} className="border-b border-[#232e48] pb-4 last:border-0 last:pb-0 space-y-3">
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                      <div>
                        <label className="text-[10px] text-gray-500 mb-1 block">Project Name</label>
                        <input
                          type="text"
                          value={proj.project_name || ''}
                          onChange={(e) => {
                            const newProj = [...(resumeData.projects || [])];
                            newProj[index] = { ...newProj[index], project_name: e.target.value };
                            setResumeData({ ...resumeData, projects: newProj });
                          }}
                          className="w-full bg-[#151d30] border border-[#232e48] rounded px-2.5 py-1.5 text-xs text-gray-200 focus:outline-none focus:border-indigo-500"
                        />
                      </div>
                      <div>
                        <label className="text-[10px] text-gray-500 mb-1 block">Technologies Used (Comma-separated)</label>
                        <input
                          type="text"
                          value={proj.technologies?.join(', ') || ''}
                          onChange={(e) => {
                            const newProj = [...(resumeData.projects || [])];
                            newProj[index] = { ...newProj[index], technologies: e.target.value.split(',').map(t => t.trim()).filter(Boolean) };
                            setResumeData({ ...resumeData, projects: newProj });
                          }}
                          className="w-full bg-[#151d30] border border-[#232e48] rounded px-2.5 py-1.5 text-xs text-gray-200 focus:outline-none focus:border-indigo-500"
                        />
                      </div>
                    </div>
                    <div>
                      <label className="text-[10px] text-gray-500 mb-1 block">Project Description Bullets (One per line)</label>
                      <textarea
                        rows={3}
                        value={proj.description_bullets?.join('\n') || ''}
                        onChange={(e) => {
                          const newProj = [...(resumeData.projects || [])];
                          newProj[index] = { ...newProj[index], description_bullets: e.target.value.split('\n') };
                          setResumeData({ ...resumeData, projects: newProj });
                        }}
                        className="w-full bg-[#151d30] border border-[#232e48] rounded px-2.5 py-1.5 text-xs text-gray-200 focus:outline-none focus:border-indigo-500"
                      />
                    </div>
                  </div>
                ))}
              </div>

              {/* Certifications */}
              <div className="bg-[#0b0f19] border border-[#232e48] rounded-xl p-5 space-y-4">
                <div className="flex justify-between items-center">
                  <h3 className="text-sm font-semibold text-indigo-400">Certifications</h3>
                  <button
                    onClick={() => setResumeData({
                      ...resumeData,
                      certifications: [...(resumeData.certifications || []), { name: '', organization: '', issue_date: '', expiration_date: '' }]
                    })}
                    className="text-[10px] text-indigo-400 hover:text-indigo-300 font-semibold flex items-center gap-1"
                  >
                    + Add Certification
                  </button>
                </div>
                {resumeData.certifications?.map((cert, index) => (
                  <div key={index} className="border-b border-[#232e48] pb-4 last:border-0 last:pb-0 grid grid-cols-2 md:grid-cols-4 gap-4">
                    <div>
                      <label className="text-[10px] text-gray-500 mb-1 block">Certification Name</label>
                      <input
                        type="text"
                        value={cert.name || ''}
                        onChange={(e) => {
                          const newCert = [...(resumeData.certifications || [])];
                          newCert[index] = { ...newCert[index], name: e.target.value };
                          setResumeData({ ...resumeData, certifications: newCert });
                        }}
                        className="w-full bg-[#151d30] border border-[#232e48] rounded px-2.5 py-1.5 text-xs text-gray-200 focus:outline-none focus:border-indigo-500"
                      />
                    </div>
                    <div>
                      <label className="text-[10px] text-gray-500 mb-1 block">Organization</label>
                      <input
                        type="text"
                        value={cert.organization || ''}
                        onChange={(e) => {
                          const newCert = [...(resumeData.certifications || [])];
                          newCert[index] = { ...newCert[index], organization: e.target.value };
                          setResumeData({ ...resumeData, certifications: newCert });
                        }}
                        className="w-full bg-[#151d30] border border-[#232e48] rounded px-2.5 py-1.5 text-xs text-gray-200 focus:outline-none focus:border-indigo-500"
                      />
                    </div>
                    <div>
                      <label className="text-[10px] text-gray-500 mb-1 block">Issue Date</label>
                      <input
                        type="text"
                        value={cert.issue_date || ''}
                        onChange={(e) => {
                          const newCert = [...(resumeData.certifications || [])];
                          newCert[index] = { ...newCert[index], issue_date: e.target.value };
                          setResumeData({ ...resumeData, certifications: newCert });
                        }}
                        className="w-full bg-[#151d30] border border-[#232e48] rounded px-2.5 py-1.5 text-xs text-gray-200 focus:outline-none focus:border-indigo-500"
                      />
                    </div>
                    <div>
                      <label className="text-[10px] text-gray-500 mb-1 block">Expiration Date</label>
                      <input
                        type="text"
                        value={cert.expiration_date || ''}
                        onChange={(e) => {
                          const newCert = [...(resumeData.certifications || [])];
                          newCert[index] = { ...newCert[index], expiration_date: e.target.value };
                          setResumeData({ ...resumeData, certifications: newCert });
                        }}
                        className="w-full bg-[#151d30] border border-[#232e48] rounded px-2.5 py-1.5 text-xs text-gray-200 focus:outline-none focus:border-indigo-500"
                      />
                    </div>
                  </div>
                ))}
              </div>

              {/* Achievements */}
              <div className="bg-[#0b0f19] border border-[#232e48] rounded-xl p-5 space-y-4">
                <div className="flex justify-between items-center">
                  <h3 className="text-sm font-semibold text-indigo-400">Achievements & Publications</h3>
                  <button
                    onClick={() => setResumeData({
                      ...resumeData,
                      achievements: [...(resumeData.achievements || []), '']
                    })}
                    className="text-[10px] text-indigo-400 hover:text-indigo-300 font-semibold flex items-center gap-1"
                  >
                    + Add Achievement
                  </button>
                </div>
                <div className="space-y-2">
                  {resumeData.achievements?.map((ach, index) => (
                    <div key={index} className="flex gap-2">
                      <input
                        type="text"
                        value={ach || ''}
                        onChange={(e) => {
                          const newAch = [...(resumeData.achievements || [])];
                          newAch[index] = e.target.value;
                          setResumeData({ ...resumeData, achievements: newAch });
                        }}
                        className="w-full bg-[#151d30] border border-[#232e48] rounded px-3 py-1.5 text-xs text-gray-200 focus:outline-none focus:border-indigo-500"
                        placeholder="Award, honor, patent, or published paper..."
                      />
                      <button
                        onClick={() => {
                          const newAch = (resumeData.achievements || []).filter((_, i) => i !== index);
                          setResumeData({ ...resumeData, achievements: newAch });
                        }}
                        className="p-2 bg-red-950/20 hover:bg-red-900/30 text-rose-400 border border-red-900/20 rounded transition"
                      >
                        Delete
                      </button>
                    </div>
                  ))}
                </div>
              </div>

              {/* ATS Analyzer Section */}
              <div className="bg-[#0b0f19] border border-[#232e48] rounded-xl p-5 space-y-4">
                <h3 className="text-sm font-semibold text-indigo-400 flex items-center gap-1.5">
                  <Sparkles className="w-4 h-4 text-indigo-400" />
                  ATS Match Analyzer
                </h3>
                <p className="text-xs text-gray-400">Evaluate match score against a target job description.</p>
                
                <div className="space-y-3">
                  <div>
                    <label className="text-[10px] text-gray-500 mb-1.5 block uppercase tracking-wider font-semibold">Job Description</label>
                    <textarea
                      rows={6}
                      value={jobDescription}
                      onChange={(e) => setJobDescription(e.target.value)}
                      placeholder="Paste target job description here..."
                      className="w-full bg-[#151d30] border border-[#232e48] rounded-lg p-3 text-xs text-gray-200 focus:outline-none focus:border-indigo-500"
                    />
                  </div>
                  <button
                    onClick={handleAnalyzeATS}
                    disabled={analyzingATS}
                    className="w-full bg-indigo-600 hover:bg-indigo-500 text-white font-semibold py-2 rounded-lg text-xs transition flex items-center justify-center gap-1.5 h-10"
                  >
                    {analyzingATS ? (
                      <>
                        <Loader2 className="w-3.5 h-3.5 animate-spin" />
                        <span>Analyzing...</span>
                      </>
                    ) : (
                      <span>Analyze ATS</span>
                    )}
                  </button>
                </div>

                {atsResult && (
                  <div className="mt-4 pt-4 border-t border-[#232e48] space-y-4">
                    {/* Overall score */}
                    <div className="flex items-center justify-between bg-[#151d30] p-4 rounded-lg border border-[#232e48]">
                      <div>
                        <h4 className="text-sm font-semibold text-gray-200">Overall ATS Score</h4>
                        <p className="text-xs text-gray-400 mt-1">Based on keyword matching, semantic context, formatting, and experience alignment.</p>
                      </div>
                      <div className="text-right">
                        <span className="text-3xl font-extrabold text-indigo-400">{atsResult.ats_score}%</span>
                      </div>
                    </div>

                    {/* Insights Grid */}
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                      {/* Strengths */}
                      <div className="bg-[#151d30]/60 border border-[#232e48] rounded-lg p-4 space-y-2">
                        <div className="flex items-center gap-1.5 text-emerald-400">
                          <CheckCircle2 className="w-4 h-4" />
                          <h5 className="text-xs font-semibold uppercase tracking-wider font-bold">Strengths</h5>
                        </div>
                        <ul className="list-disc list-inside space-y-1.5 text-xs text-gray-300">
                          {(atsResult.strengths || []).map((strength, index) => (
                            <li key={index} className="leading-relaxed">{strength}</li>
                          ))}
                          {(atsResult.strengths || []).length === 0 && (
                            <li className="text-gray-500 italic">No specific strengths identified.</li>
                          )}
                        </ul>
                      </div>

                      {/* Weaknesses */}
                      <div className="bg-[#151d30]/60 border border-[#232e48] rounded-lg p-4 space-y-2">
                        <div className="flex items-center gap-1.5 text-rose-400">
                          <XCircle className="w-4 h-4" />
                          <h5 className="text-xs font-semibold uppercase tracking-wider font-bold">Weaknesses</h5>
                        </div>
                        <ul className="list-disc list-inside space-y-1.5 text-xs text-gray-300">
                          {(atsResult.weaknesses || []).map((weakness, index) => (
                            <li key={index} className="leading-relaxed">{weakness}</li>
                          ))}
                          {(atsResult.weaknesses || []).length === 0 && (
                            <li className="text-gray-500 italic">No specific weaknesses identified.</li>
                          )}
                        </ul>
                      </div>

                      {/* Missing Keywords */}
                      <div className="bg-[#151d30]/60 border border-[#232e48] rounded-lg p-4 space-y-2">
                        <div className="flex items-center gap-1.5 text-amber-400">
                          <AlertTriangle className="w-4 h-4" />
                          <h5 className="text-xs font-semibold uppercase tracking-wider font-bold">Missing Keywords</h5>
                        </div>
                        <ul className="list-disc list-inside space-y-1.5 text-xs text-gray-300">
                          {(atsResult.missing_keywords || []).map((kw, index) => (
                            <li key={index} className="leading-relaxed">{kw}</li>
                          ))}
                          {(atsResult.missing_keywords || []).length === 0 && (
                            <li className="text-gray-500 italic">No missing keywords identified.</li>
                          )}
                        </ul>
                      </div>

                      {/* Suggestions */}
                      <div className="bg-[#151d30]/60 border border-[#232e48] rounded-lg p-4 space-y-2">
                        <div className="flex items-center gap-1.5 text-indigo-400">
                          <Sparkles className="w-4 h-4" />
                          <h5 className="text-xs font-semibold uppercase tracking-wider font-bold">Suggestions</h5>
                        </div>
                        <ul className="list-disc list-inside space-y-1.5 text-xs text-gray-300">
                          {(atsResult.suggestions || []).map((suggestion, index) => (
                            <li key={index} className="leading-relaxed">{suggestion}</li>
                          ))}
                          {(atsResult.suggestions || []).length === 0 && (
                            <li className="text-gray-500 italic">No suggestions available.</li>
                          )}
                        </ul>
                      </div>
                    </div>
                  </div>
                )}
              </div>
            </div>
          </div>
        ) : (
          <div className="text-center py-20 text-gray-500 flex flex-col items-center justify-center gap-3">
            <AlertTriangle className="w-12 h-12 text-gray-600" />
            <div>
              <p className="text-sm font-semibold text-gray-400">No active resume loaded</p>
              <p className="text-xs text-gray-500 mt-1">Please upload a document or load one from your Resume Library in the sidebar.</p>
            </div>
          </div>
        )}
      </div>

    </div>
  );
}
