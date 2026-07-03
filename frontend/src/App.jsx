import React, { useState } from 'react';
import { AuthProvider, useAuth } from './context/AuthContext';
import Auth from './pages/Auth';
import Dashboard from './pages/Dashboard';
import ResumeEditor from './pages/ResumeEditor';
import JobBoard from './pages/JobBoard';
import InterviewPrep from './pages/InterviewPrep';
import { Briefcase, FileText, LayoutDashboard, LogOut, ShieldAlert, Sparkles, User } from 'lucide-react';

function AppContent() {
  const { user, logout, loading } = useAuth();
  const [activeTab, setActiveTab] = useState('overview');
  
  // Track active resume details globally for matcher/interview connections
  const [globalResume, setGlobalResume] = useState(null);

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
        return <ResumeEditor onResumeLoaded={setGlobalResume} />;
      case 'jobs':
        return <JobBoard resume={globalResume} />;
      case 'interviews':
        return <InterviewPrep resume={globalResume} />;
      default:
        return <Dashboard />;
    }
  };

  return (
    <div className="min-h-screen bg-[#0b0f19] text-gray-200 flex flex-col md:flex-row">
      {/* Sidebar navigation */}
      <aside className="w-full md:w-64 bg-[#151d30] border-b md:border-b-0 md:border-r border-[#232e48]/80 flex flex-col justify-between">
        <div className="p-5 space-y-8">
          <div className="flex items-center gap-3 border-b border-[#232e48] pb-4">
            <div className="p-2 bg-indigo-500/10 rounded-lg border border-indigo-500/20 text-indigo-400">
              <Sparkles className="w-5 h-5" />
            </div>
            <div>
              <span className="font-bold text-sm text-gray-100 block">Career Copilot</span>
              <span className="text-[10px] text-gray-500 font-semibold uppercase">Workspace v1.0</span>
            </div>
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
