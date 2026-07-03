import React, { useState, useEffect } from 'react';
import { apiService } from '../services/api';
import { Upload, Plus, Trash2, Download, Check, Save, ArrowLeftRight, Loader2 } from 'lucide-react';

export default function ResumeEditor() {
  const [resumes, setResumes] = useState([]);
  const [activeResume, setActiveResume] = useState(null);
  const [resumeData, setResumeData] = useState(null);
  
  // Versions and Diffs
  const [compareMode, setCompareMode] = useState(false);
  const [selectedV1, setSelectedV1] = useState('');
  const [selectedV2, setSelectedV2] = useState('');
  const [diffResults, setDiffResults] = useState(null);
  
  const [loading, setLoading] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [saving, setSaving] = useState(false);
  const [message, setMessage] = useState('');

  // Fetch list of resumes on load
  useEffect(() => {
    loadResumes();
  }, []);

  async function loadResumes() {
    setLoading(true);
    try {
      const res = await apiService.getResumes();
      setResumes(res.data);
      if (res.data.length > 0) {
        // Select first resume by default
        selectResume(res.data[0]);
      }
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  }

  const selectResume = (res) => {
    setActiveResume(res);
    // Find active version structured data
    if (res.active_version) {
      setResumeData(res.active_version.structured_data);
    } else if (res.versions && res.versions.length > 0) {
      setResumeData(res.versions[0].structured_data);
    } else {
      setResumeData(null);
    }
    setCompareMode(false);
    setDiffResults(null);
  };

  // Upload handler
  const handleFileUpload = async (e) => {
    const file = e.target.files[0];
    if (!file) return;
    setUploading(true);
    setMessage('');
    try {
      // 1. Run FastAPI parser
      const parseRes = await apiService.parseResumeFile(file);
      const parsedResume = parseRes.data;

      // 2. Register new resume record in Django database
      const resumeRes = await apiService.createResume(file.name);
      const newResume = resumeRes.data;

      // In real-world setup, FastAPI returns structured data, which we then post to Django to create the Version.
      // For this prototype, we'll mimic version storage in the active tab
      setResumeData(parsedResume);
      setActiveResume(newResume);
      
      // Reload list
      await loadResumes();
      setMessage('Resume parsed and loaded successfully!');
    } catch (err) {
      setMessage('Failed to parse resume: ' + (err.response?.data?.detail || err.message));
    } finally {
      setUploading(false);
    }
  };

  // Compare version diff
  const handleCompare = async () => {
    if (!selectedV1 || !selectedV2) return;
    setLoading(true);
    try {
      const res = await apiService.compareVersions(activeResume.id, selectedV1, selectedV2);
      setDiffResults(res.data.diff);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  // Export handlers
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
    } finally {
      setSaving(false);
    }
  };

  const handleSaveLocal = () => {
    // Keep local changes
    setMessage('Changes saved in active workspace!');
  };

  if (loading) {
    return (
      <div className="flex-1 flex items-center justify-center min-h-[500px]">
        <Loader2 className="w-8 h-8 text-indigo-500 animate-spin" />
      </div>
    );
  }

  return (
    <div className="grid grid-cols-1 xl:grid-cols-4 gap-6">
      {/* Sidebar - Resumes list and version controls */}
      <div className="bg-[#151d30] border border-[#232e48] rounded-xl p-5 space-y-6">
        <div>
          <h2 className="text-sm font-semibold text-gray-300 uppercase tracking-wider mb-4">My Resumes</h2>
          
          <div className="space-y-2">
            {resumes.map(r => (
              <button
                key={r.id}
                onClick={() => selectResume(r)}
                className={`w-full text-left px-3 py-2 rounded-lg text-sm transition ${
                  activeResume?.id === r.id 
                    ? 'bg-indigo-600/10 text-indigo-400 border border-indigo-500/20' 
                    : 'text-gray-400 hover:bg-[#1a233b] border border-transparent'
                }`}
              >
                {r.title}
              </button>
            ))}
          </div>

          <label className="mt-4 flex items-center justify-center gap-2 border border-dashed border-[#232e48] hover:border-indigo-500/50 rounded-lg p-3 text-xs text-gray-400 hover:text-indigo-400 cursor-pointer transition">
            {uploading ? (
              <Loader2 className="w-4 h-4 animate-spin text-indigo-400" />
            ) : (
              <Upload className="w-4 h-4" />
            )}
            <span>{uploading ? 'Parsing...' : 'Upload PDF / DOCX'}</span>
            <input type="file" onChange={handleFileUpload} accept=".pdf,.docx" className="hidden" />
          </label>
        </div>

        {activeResume && activeResume.versions && activeResume.versions.length > 0 && (
          <div className="border-t border-[#232e48] pt-4">
            <div className="flex justify-between items-center mb-4">
              <h3 className="text-sm font-semibold text-gray-300 uppercase tracking-wider">Version Control</h3>
              <button
                onClick={() => setCompareMode(!compareMode)}
                className={`p-1.5 rounded transition ${compareMode ? 'bg-indigo-600 text-white' : 'bg-transparent text-gray-400 hover:text-gray-200'}`}
                title="Compare Versions"
              >
                <ArrowLeftRight className="w-4 h-4" />
              </button>
            </div>

            {compareMode ? (
              <div className="space-y-3">
                <div>
                  <label className="text-[10px] text-gray-500 mb-1 block">Version 1</label>
                  <select
                    value={selectedV1}
                    onChange={(e) => setSelectedV1(e.target.value)}
                    className="w-full bg-[#0b0f19] border border-[#232e48] rounded px-2 py-1.5 text-xs text-gray-300 focus:outline-none"
                  >
                    <option value="">Select version</option>
                    {activeResume.versions.map(v => (
                      <option key={v.id} value={v.id}>v{v.version_number} - {v.label}</option>
                    ))}
                  </select>
                </div>
                <div>
                  <label className="text-[10px] text-gray-500 mb-1 block">Version 2</label>
                  <select
                    value={selectedV2}
                    onChange={(e) => setSelectedV2(e.target.value)}
                    className="w-full bg-[#0b0f19] border border-[#232e48] rounded px-2 py-1.5 text-xs text-gray-300 focus:outline-none"
                  >
                    <option value="">Select version</option>
                    {activeResume.versions.map(v => (
                      <option key={v.id} value={v.id}>v{v.version_number} - {v.label}</option>
                    ))}
                  </select>
                </div>
                <button
                  onClick={handleCompare}
                  className="w-full bg-indigo-600 hover:bg-indigo-500 text-white font-medium py-1.5 rounded text-xs transition"
                >
                  Run Comparison
                </button>
              </div>
            ) : (
              <div className="space-y-2">
                {activeResume.versions.map(v => (
                  <div key={v.id} className="flex justify-between items-center text-xs p-2 bg-[#0b0f19]/40 rounded border border-[#232e48]/50">
                    <span className="text-gray-300">v{v.version_number} ({v.label})</span>
                    {v.is_active ? (
                      <span className="p-0.5 bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 rounded text-[9px] uppercase font-bold">Active</span>
                    ) : (
                      <button
                        onClick={async () => {
                          await apiService.setActiveVersion(activeResume.id, v.id);
                          loadResumes();
                        }}
                        className="text-indigo-400 hover:text-indigo-300 font-semibold"
                      >
                        Activate
                      </button>
                    )}
                  </div>
                ))}
              </div>
            )}
          </div>
        )}
      </div>

      {/* Editor Content Panel */}
      <div className="bg-[#151d30] border border-[#232e48] rounded-xl p-6 xl:col-span-3 space-y-6">
        {message && (
          <div className="p-3 bg-indigo-500/10 border border-indigo-500/20 text-indigo-400 text-xs rounded-lg text-center flex justify-between items-center">
            <span>{message}</span>
            <button onClick={() => setMessage('')} className="text-gray-400 hover:text-gray-200">×</button>
          </div>
        )}

        {compareMode && diffResults ? (
          <div>
            <h2 className="text-base font-semibold text-gray-200 mb-4">Version Differences Analysis</h2>
            <div className="space-y-4">
              {Object.keys(diffResults).map(key => {
                const diff = diffResults[key];
                if (diff.status === 'unchanged') return null;
                return (
                  <div key={key} className="bg-[#0b0f19] border border-[#232e48] rounded-lg p-4">
                    <h3 className="text-xs font-bold text-gray-400 uppercase tracking-wider mb-2">{key}</h3>
                    <div className="grid grid-cols-2 gap-4 text-xs">
                      <div className="p-2.5 bg-red-950/20 border border-red-900/30 text-red-400 rounded">
                        <div className="font-bold text-[10px] uppercase text-red-500 mb-1">Version 1</div>
                        <pre className="whitespace-pre-wrap">{JSON.stringify(diff.v1, null, 2)}</pre>
                      </div>
                      <div className="p-2.5 bg-emerald-950/20 border border-emerald-900/30 text-emerald-400 rounded">
                        <div className="font-bold text-[10px] uppercase text-emerald-500 mb-1">Version 2</div>
                        <pre className="whitespace-pre-wrap">{JSON.stringify(diff.v2, null, 2)}</pre>
                      </div>
                    </div>
                  </div>
                );
              })}
            </div>
          </div>
        ) : resumeData ? (
          <div>
            {/* Control Bar */}
            <div className="flex justify-between items-center mb-6">
              <h2 className="text-base font-semibold text-gray-200">Structured Resume Data</h2>
              
              <div className="flex gap-2">
                <button
                  onClick={() => handleExport('pdf')}
                  disabled={saving}
                  className="bg-slate-800 hover:bg-slate-700 text-gray-200 px-3 py-1.5 rounded-lg text-xs transition flex items-center gap-1.5"
                >
                  <Download className="w-3.5 h-3.5" />
                  PDF
                </button>
                <button
                  onClick={() => handleExport('docx')}
                  disabled={saving}
                  className="bg-slate-800 hover:bg-slate-700 text-gray-200 px-3 py-1.5 rounded-lg text-xs transition flex items-center gap-1.5"
                >
                  <Download className="w-3.5 h-3.5" />
                  Word
                </button>
                <button
                  onClick={handleSaveLocal}
                  className="bg-indigo-600 hover:bg-indigo-500 text-white px-3 py-1.5 rounded-lg text-xs transition flex items-center gap-1.5"
                >
                  <Save className="w-3.5 h-3.5" />
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
                <textarea
                  value={resumeData.skills?.join(', ') || ''}
                  onChange={(e) => setResumeData({
                    ...resumeData,
                    skills: e.target.value.split(',').map(s => s.trim())
                  })}
                  className="w-full h-20 bg-[#151d30] border border-[#232e48] rounded p-3 text-xs text-gray-200 focus:outline-none focus:border-indigo-500"
                  placeholder="React, Python, Django, PostgreSQL, Docker..."
                />
              </div>

              {/* Experience */}
              <div className="bg-[#0b0f19] border border-[#232e48] rounded-xl p-5 space-y-4">
                <h3 className="text-sm font-semibold text-indigo-400">Professional Experience</h3>
                {resumeData.experiences?.map((exp, index) => (
                  <div key={index} className="border-b border-[#232e48] pb-4 last:border-0 last:pb-0 space-y-3">
                    <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                      <div>
                        <label className="text-[10px] text-gray-500 mb-1 block">Company</label>
                        <input
                          type="text"
                          value={exp.company}
                          className="w-full bg-[#151d30] border border-[#232e48] rounded px-2.5 py-1.5 text-xs text-gray-200 focus:outline-none"
                        />
                      </div>
                      <div>
                        <label className="text-[10px] text-gray-500 mb-1 block">Role</label>
                        <input
                          type="text"
                          value={exp.role}
                          className="w-full bg-[#151d30] border border-[#232e48] rounded px-2.5 py-1.5 text-xs text-gray-200 focus:outline-none"
                        />
                      </div>
                      <div>
                        <label className="text-[10px] text-gray-500 mb-1 block">Start Date</label>
                        <input
                          type="text"
                          value={exp.start_date}
                          className="w-full bg-[#151d30] border border-[#232e48] rounded px-2.5 py-1.5 text-xs text-gray-200 focus:outline-none"
                        />
                      </div>
                      <div>
                        <label className="text-[10px] text-gray-500 mb-1 block">End Date</label>
                        <input
                          type="text"
                          value={exp.end_date}
                          className="w-full bg-[#151d30] border border-[#232e48] rounded px-2.5 py-1.5 text-xs text-gray-200 focus:outline-none"
                        />
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        ) : (
          <div className="flex flex-col items-center justify-center py-20 text-center space-y-4">
            <Upload className="w-10 h-10 text-gray-500" />
            <div>
              <h3 className="font-semibold text-gray-300">No Resume Uploaded</h3>
              <p className="text-xs text-gray-500 mt-1">Upload a PDF or DOCX resume to get started parsing.</p>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
