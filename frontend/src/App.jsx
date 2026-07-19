import React, { useState, useEffect } from 'react';
import { AuthProvider, useAuth } from './context/AuthContext';
import Auth from './pages/Auth';
import Dashboard from './pages/Dashboard';
import ResumeEditor from './pages/ResumeEditor';
import JobBoard from './pages/JobBoard';
import InterviewPrep from './pages/InterviewPrep';
import { apiService } from './services/api';
import { Briefcase, FileText, LayoutDashboard, LogOut, ShieldAlert, Sparkles, User, FileJson } from 'lucide-react';

function AppContent() {
  const { user, logout, loading } = useAuth();
  const [activeTab, setActiveTab] = useState('overview');
  
  const [showDropdown, setShowDropdown] = useState(false);
  const [globalResumeLoading, setGlobalResumeLoading] = useState(false);
  const [globalResumeError, setGlobalResumeError] = useState(null);

  // Track active resume details globally for matcher/interview connections
  const [globalResume, setGlobalResume] = useState(() => {
    const saved = localStorage.getItem('parsed_resume');
    try {
      return saved ? JSON.parse(saved) : null;
    } catch (e) {
      console.error('Failed to parse saved resume:', e);
      return null;
    }
  });

  const [libraryResumes, setLibraryResumes] = useState([]);
  const [activeResumeId, setActiveResumeId] = useState(() => {
    return localStorage.getItem('active_resume_id') || '';
  });

  const loadLibraryResumes = async () => {
    try {
      const res = await apiService.getLibraryResumes();
      setLibraryResumes(res.data || []);
    } catch (e) {
      console.error('Failed to load library resumes:', e);
    }
  };

  const fetchActiveResumeData = async (resumeId) => {
    if (!resumeId) {
      setGlobalResume(null);
      setGlobalResumeError(null);
      setGlobalResumeLoading(false);
      localStorage.removeItem('parsed_resume');
      return;
    }
    
    setGlobalResumeLoading(true);
    setGlobalResumeError(null);
    localStorage.removeItem('parsed_resume');
    
    const timeout = new Promise((_, reject) => 
      setTimeout(() => reject(new Error('Timeout loading parsed resume')), 10000)
    );
    
    try {
      const res = await Promise.race([
        apiService.getLibraryResumeData(resumeId),
        timeout
      ]);
      
      setGlobalResume(res.data);
      localStorage.setItem('parsed_resume', JSON.stringify(res.data));
      setGlobalResumeError(null);
    } catch (err) {
      console.error("Failed to load parsed resume data", err);
      setGlobalResume(null);
      setGlobalResumeError("Unable to load parsed resume.");
    } finally {
      setGlobalResumeLoading(false);
    }
  };

  useEffect(() => {
    if (libraryResumes.length > 0 && activeResumeId) {
      const activeObj = libraryResumes.find(r => r.id === activeResumeId);
      if (activeObj && activeObj.parsed && !globalResume) {
        fetchActiveResumeData(activeResumeId);
      }
    }
  }, [libraryResumes, activeResumeId]);

  const formatDateTime = (dateStr) => {
    if (!dateStr) return 'N/A';
    const date = new Date(dateStr);
    const day = String(date.getDate()).padStart(2, '0');
    const months = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"];
    const month = months[date.getMonth()];
    const year = date.getFullYear();
    let hours = date.getHours();
    const minutes = String(date.getMinutes()).padStart(2, '0');
    const ampm = hours >= 12 ? 'PM' : 'AM';
    hours = hours % 12;
    hours = hours ? hours : 12;
    return `${day} ${month} ${year} ${hours}:${minutes} ${ampm}`;
  };

  const handleRenameClick = async (e, r) => {
    e.stopPropagation();
    const newName = prompt("Enter new name for resume file:", r.filename);
    if (newName && newName.trim()) {
      try {
        await apiService.renameLibraryResume(r.id, newName.trim());
        await loadLibraryResumes();
      } catch (err) {
        alert("Failed to rename: " + err.message);
      }
    }
  };

  const handleDeleteClick = async (e, r) => {
    e.stopPropagation();
    if (confirm(`Are you sure you want to delete "${r.filename}"?`)) {
      try {
        await apiService.deleteLibraryResume(r.id);
        if (r.id === activeResumeId) {
          handleSetActiveResume('');
        }
        await loadLibraryResumes();
      } catch (err) {
        alert("Failed to delete: " + err.message);
      }
    }
  };

  const handleReParseClick = async (e, r) => {
    e.stopPropagation();
    try {
      alert("Re-parsing started. Please wait a moment...");
      const res = await apiService.parseExistingLibraryResume(r.id);
      await loadLibraryResumes();
      if (r.id === activeResumeId) {
        setGlobalResume(res.data);
      }
      alert("Resume parsed successfully!");
    } catch (err) {
      alert("Re-parse failed: " + err.message);
    }
  };

  const handleDownloadClick = (e, r) => {
    e.stopPropagation();
    const link = document.createElement('a');
    link.href = apiService.getLibraryResumeDownloadUrl(r.id);
    link.setAttribute('download', r.filename);
    document.body.appendChild(link);
    link.click();
    link.remove();
  };

  const handleUploadClick = async (e) => {
    const file = e.target.files[0];
    if (!file) return;
    try {
      alert("Uploading and parsing new resume...");
      const res = await apiService.uploadResumeToLibrary(file);
      await loadLibraryResumes();
      
      // Auto-activate the newly uploaded resume
      const latestRes = await apiService.getLibraryResumes();
      const newest = (latestRes.data || []).reduce((prev, current) => {
        return (new Date(prev.upload_date) > new Date(current.upload_date)) ? prev : current;
      }, { upload_date: '1970-01-01T00:00:00' });
      
      if (newest && newest.id) {
        await handleSetActiveResume(newest.id);
      }
      alert("Resume uploaded and parsed successfully!");
    } catch (err) {
      alert("Upload failed: " + err.message);
    }
  };

  useEffect(() => {
    if (user) {
      loadLibraryResumes();
    }
  }, [user]);

  const handleSetActiveResume = async (resumeId) => {
    if (!resumeId) {
      setActiveResumeId('');
      localStorage.removeItem('active_resume_id');
      await fetchActiveResumeData(null);
      return;
    }
    setActiveResumeId(resumeId);
    localStorage.setItem('active_resume_id', resumeId);
    
    // Find the resume object
    const resumeObj = libraryResumes.find(r => r.id === resumeId);
    if (resumeObj && resumeObj.parsed) {
      await fetchActiveResumeData(resumeId);
    } else {
      setGlobalResume(null);
      setGlobalResumeError(null);
      setGlobalResumeLoading(false);
      localStorage.removeItem('parsed_resume');
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-[#0b0f19] flex items-center justify-center">
        <div className="flex flex-col items-center gap-3">
          <div className="w-8 h-8 border-4 border-indigo-500 border-t-transparent rounded-full animate-spin" />
          <span className="text-xs text-gray-500">Checking session credentials...</span>
        </div>
      </div>
    );
  }

  if (!user) {
    return <Auth />;
  }

  const renderContent = () => {
    switch (activeTab) {
      case 'overview':
        return <Dashboard />;
      case 'editor':
        return (
          <ResumeEditor 
            onResumeLoaded={setGlobalResume} 
            activeResumeId={activeResumeId}
            setActiveResumeId={handleSetActiveResume}
            libraryResumes={libraryResumes}
            onRefreshLibrary={loadLibraryResumes}
            resumeLoading={globalResumeLoading}
            resumeError={globalResumeError}
            onRetryLoadResume={() => fetchActiveResumeData(activeResumeId)}
          />
        );
      case 'jobs':
        return (
          <JobBoard 
            resume={globalResume} 
            activeResumeId={activeResumeId} 
            libraryResumes={libraryResumes}
            resumeLoading={globalResumeLoading}
            resumeError={globalResumeError}
            onRetryLoadResume={() => fetchActiveResumeData(activeResumeId)}
          />
        );
      case 'interviews':
        return (
          <InterviewPrep 
            resume={globalResume} 
            activeResumeId={activeResumeId} 
            libraryResumes={libraryResumes}
            resumeLoading={globalResumeLoading}
            resumeError={globalResumeError}
            onRetryLoadResume={() => fetchActiveResumeData(activeResumeId)}
          />
        );
      default:
        return <Dashboard />;
    }
  };

  return (
    <div className="min-h-screen bg-[#0b0f19] text-gray-200 flex flex-col md:flex-row">
      {/* Sidebar navigation */}
      <aside className="w-full md:w-64 bg-[#151d30] border-b md:border-b-0 md:border-r border-[#232e48]/80 flex flex-col justify-between">
        <div className="p-5 space-y-6">
          <div className="flex items-center gap-3 border-b border-[#232e48] pb-4">
            <div className="p-2 bg-indigo-500/10 rounded-lg border border-indigo-500/20 text-indigo-400">
              <Sparkles className="w-5 h-5" />
            </div>
            <div>
              <span className="font-bold text-sm text-gray-100 block">Career Copilot</span>
              <span className="text-[10px] text-gray-500 font-semibold uppercase">Workspace v1.0</span>
            </div>
          </div>

          {/* Active Resume Panel */}
          {activeResumeId && (
            (() => {
              const activeObj = libraryResumes.find(r => r.id === activeResumeId);
              if (!activeObj) return null;
              return (
                <div className="bg-[#0b0f19] border border-[#232e48]/80 rounded-xl p-3.5 space-y-2.5">
                  <div className="text-[10px] text-gray-500 uppercase tracking-wider font-bold">Active Resume</div>
                  <div className="flex gap-2.5 items-start">
                    <FileText className="w-5 h-5 text-indigo-400 mt-0.5 shrink-0" />
                    <div className="min-w-0 flex-1">
                      <h4 className="text-xs font-bold text-gray-200 truncate" title={activeObj.filename}>{activeObj.filename}</h4>
                      <div className="flex items-center gap-1 mt-1 text-[10px]">
                        {activeObj.parsed ? (
                          <span className="text-emerald-400 font-semibold flex items-center gap-0.5">✔ Parsed</span>
                        ) : (
                          <span className="text-rose-400 font-semibold flex items-center gap-0.5">✗ Not Parsed</span>
                        )}
                      </div>
                      <div className="text-[9px] text-gray-500 space-y-0.5 mt-2">
                        <p className="font-semibold text-gray-400">Last Parsed:</p>
                        <p>{formatDateTime(activeObj.last_modified)}</p>
                        <p className="font-semibold text-gray-400 mt-1">Upload Date:</p>
                        <p>{formatDateTime(activeObj.upload_date)}</p>
                      </div>
                    </div>
                  </div>
                </div>
              );
            })()
          )}

          {/* Switch Resume Dropdown */}
          <div className="space-y-1.5 relative">
            <label className="text-[10px] text-gray-400 uppercase tracking-wider font-semibold">Switch Resume</label>
            <div 
              onClick={() => setShowDropdown(!showDropdown)}
              className="w-full bg-[#0b0f19] border border-[#232e48] hover:border-indigo-500/50 rounded-lg py-2 px-3 text-xs text-gray-300 flex items-center justify-between cursor-pointer transition select-none"
            >
              <span className="truncate">
                {activeResumeId 
                  ? (libraryResumes.find(r => r.id === activeResumeId)?.filename || 'Select Resume')
                  : 'Select Resume'
                }
              </span>
              <span className="text-[10px] text-gray-500">▼</span>
            </div>

            {showDropdown && (
              <div className="absolute left-0 right-0 mt-1 bg-[#151d30] border border-[#232e48] rounded-xl overflow-hidden shadow-2xl z-50 max-h-72 overflow-y-auto space-y-1 p-2">
                {libraryResumes.length > 0 ? (
                  libraryResumes.map(r => (
                    <div 
                      key={r.id}
                      onClick={() => { handleSetActiveResume(r.id); setShowDropdown(false); }}
                      className={`p-2 rounded-lg cursor-pointer transition flex items-center justify-between text-xs gap-2 group ${
                        r.id === activeResumeId 
                          ? 'bg-indigo-600/10 border border-indigo-500/30 text-indigo-300' 
                          : 'hover:bg-[#0b0f19] text-gray-300'
                      }`}
                    >
                      <div className="min-w-0 flex-1">
                        <div className="font-semibold truncate">{r.filename}</div>
                        <div className="flex items-center gap-1.5 mt-0.5 text-[9px]">
                          {r.parsed ? (
                            <span className="text-emerald-400 font-bold">✔ Parsed</span>
                          ) : (
                            <span className="text-rose-400 font-bold">✗ Not Parsed</span>
                          )}
                          <span className="text-gray-500">•</span>
                          <span className="text-gray-500">{formatDateTime(r.last_modified)}</span>
                        </div>
                      </div>
                      
                      {/* Action buttons inside dropdown */}
                      <div className="flex gap-0.5 opacity-60 group-hover:opacity-100 transition shrink-0">
                        <button 
                          onClick={(e) => { e.stopPropagation(); handleDownloadClick(e, r); }}
                          className="p-1 hover:bg-[#0b0f19] rounded text-gray-400 hover:text-white" 
                          title="Download"
                        >
                          📥
                        </button>
                        <button 
                          onClick={(e) => { e.stopPropagation(); handleReParseClick(e, r); }}
                          className="p-1 hover:bg-[#0b0f19] rounded text-gray-400 hover:text-white" 
                          title="Re-parse"
                        >
                          🔄
                        </button>
                        <button 
                          onClick={(e) => { e.stopPropagation(); handleRenameClick(e, r); }}
                          className="p-1 hover:bg-[#0b0f19] rounded text-gray-400 hover:text-white" 
                          title="Rename"
                        >
                          ✏️
                        </button>
                        <button 
                          onClick={(e) => { e.stopPropagation(); handleDeleteClick(e, r); }}
                          className="p-1 hover:bg-[#0b0f19] rounded text-gray-400 hover:text-rose-400" 
                          title="Delete"
                        >
                          🗑️
                        </button>
                      </div>
                    </div>
                  ))
                ) : (
                  <div className="text-center py-4 text-gray-500 text-[10px] italic">No resumes found.</div>
                )}
                
                {/* Upload inside dropdown */}
                <div className="border-t border-[#232e48]/40 pt-1.5 mt-1">
                  <label className="flex items-center justify-center gap-1.5 py-2 rounded-lg border border-dashed border-[#232e48] hover:border-indigo-500/50 text-[10px] text-gray-400 hover:text-indigo-400 font-bold cursor-pointer transition w-full">
                    <span>+ Upload New Resume</span>
                    <input type="file" onChange={handleUploadClick} accept=".pdf,.docx,.doc" className="hidden" />
                  </label>
                </div>
              </div>
            )}
          </div>

          <nav className="space-y-1">
            <button
              onClick={() => setActiveTab('overview')}
              className={`w-full flex items-center gap-3 px-4 py-2.5 rounded-lg text-xs font-semibold transition ${
                activeTab === 'overview'
                  ? 'bg-indigo-600 text-white'
                  : 'text-gray-400 hover:bg-[#1a233b] hover:text-gray-200'
              }`}
            >
              <LayoutDashboard className="w-4 h-4" />
              Overview
            </button>
            <button
              onClick={() => setActiveTab('editor')}
              className={`w-full flex items-center gap-3 px-4 py-2.5 rounded-lg text-xs font-semibold transition ${
                activeTab === 'editor'
                  ? 'bg-indigo-600 text-white'
                  : 'text-gray-400 hover:bg-[#1a233b] hover:text-gray-200'
              }`}
            >
              <FileText className="w-4 h-4" />
              Resume Assistant
            </button>
            <button
              onClick={() => setActiveTab('jobs')}
              className={`w-full flex items-center gap-3 px-4 py-2.5 rounded-lg text-xs font-semibold transition ${
                activeTab === 'jobs'
                  ? 'bg-indigo-600 text-white'
                  : 'text-gray-400 hover:bg-[#1a233b] hover:text-gray-200'
              }`}
            >
              <Briefcase className="w-4 h-4" />
              Job Matcher
            </button>
            <button
              onClick={() => setActiveTab('interviews')}
              className={`w-full flex items-center gap-3 px-4 py-2.5 rounded-lg text-xs font-semibold transition ${
                activeTab === 'interviews'
                  ? 'bg-indigo-600 text-white'
                  : 'text-gray-400 hover:bg-[#1a233b] hover:text-gray-200'
              }`}
            >
              <ShieldAlert className="w-4 h-4" />
              AI Recruiter Prep
            </button>
          </nav>
        </div>

        {/* User Card */}
        <div className="p-4 border-t border-[#232e48] bg-[#0b0f19]/25 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <div className="w-8 h-8 rounded-full bg-indigo-600/20 text-indigo-400 border border-indigo-500/20 flex items-center justify-center font-bold text-xs uppercase">
              {user.first_name?.[0] || 'U'}
            </div>
            <div>
              <span className="text-xs font-bold text-gray-200 block truncate max-w-[100px]">{user.first_name}</span>
              <span className="text-[9px] text-gray-500 block truncate max-w-[100px]">{user.email}</span>
            </div>
          </div>
          <button
            onClick={logout}
            className="p-1.5 hover:bg-red-500/10 hover:text-red-400 rounded-lg transition text-gray-500"
            title="Log Out"
          >
            <LogOut className="w-4 h-4" />
          </button>
        </div>
      </aside>

      {/* Main View Area */}
      <main className="flex-1 p-6 md:p-8 overflow-y-auto max-h-screen">
        {renderContent()}
      </main>
    </div>
  );
}

export default function App() {
  return (
    <AuthProvider>
      <AppContent />
    </AuthProvider>
  );
}
