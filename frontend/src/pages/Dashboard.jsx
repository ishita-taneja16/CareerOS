import React, { useState, useEffect } from 'react';
import { apiService } from '../services/api';
import { Briefcase, Bookmark, FileSpreadsheet, CheckCircle2, Trophy, Loader2 } from 'lucide-react';

export default function Dashboard() {
  const [stats, setStats] = useState(null);
  const [recentApplications, setRecentApplications] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function loadData() {
      try {
        const statsRes = await apiService.getDashboardStats();
        setStats(statsRes.data);
        
        const appsRes = await apiService.getJobApplications();
        setRecentApplications(appsRes.data.slice(0, 4));
      } catch (e) {
        console.error(e);
      } finally {
        setLoading(false);
      }
    }
    loadData();
  }, []);

  if (loading) {
    return (
      <div className="flex-1 flex items-center justify-center min-h-[500px]">
        <Loader2 className="w-8 h-8 text-indigo-500 animate-spin" />
      </div>
    );
  }

  // Pre-calculate SVG values for visual data displays
  const total = stats?.total || 0;
  const values = [
    { label: 'Saved', count: stats?.saved || 0, color: '#f59e0b' },
    { label: 'Applied', count: stats?.applied || 0, color: '#3b82f6' },
    { label: 'Interviews', count: stats?.interviewing || 0, color: '#8b5cf6' },
    { label: 'Offers', count: stats?.offered || 0, color: '#10b981' }
  ];

  return (
    <div className="space-y-6">
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-gray-100">Career Insights Dashboard</h1>
          <p className="text-sm text-gray-400">Track and optimize your job applications in real time.</p>
        </div>
      </div>

      {/* Metric Cards Grid */}
      <div className="grid grid-cols-2 lg:grid-cols-5 gap-4">
        <div className="bg-[#151d30] border border-[#232e48] rounded-xl p-4 flex items-center gap-3">
          <div className="p-2 bg-indigo-500/10 rounded-lg text-indigo-400">
            <Briefcase className="w-5 h-5" />
          </div>
          <div>
            <div className="text-xl font-bold text-gray-100">{stats?.total || 0}</div>
            <div className="text-xs text-gray-400">Total Jobs</div>
          </div>
        </div>

        <div className="bg-[#151d30] border border-[#232e48] rounded-xl p-4 flex items-center gap-3">
          <div className="p-2 bg-amber-500/10 rounded-lg text-amber-400">
            <Bookmark className="w-5 h-5" />
          </div>
          <div>
            <div className="text-xl font-bold text-gray-100">{stats?.saved || 0}</div>
            <div className="text-xs text-gray-400">Saved</div>
          </div>
        </div>

        <div className="bg-[#151d30] border border-[#232e48] rounded-xl p-4 flex items-center gap-3">
          <div className="p-2 bg-blue-500/10 rounded-lg text-blue-400">
            <FileSpreadsheet className="w-5 h-5" />
          </div>
          <div>
            <div className="text-xl font-bold text-gray-100">{stats?.applied || 0}</div>
            <div className="text-xs text-gray-400">Applied</div>
          </div>
        </div>

        <div className="bg-[#151d30] border border-[#232e48] rounded-xl p-4 flex items-center gap-3">
          <div className="p-2 bg-violet-500/10 rounded-lg text-violet-400">
            <CheckCircle2 className="w-5 h-5" />
          </div>
          <div>
            <div className="text-xl font-bold text-gray-100">{stats?.interviewing || 0}</div>
            <div className="text-xs text-gray-400">Interviewing</div>
          </div>
        </div>

        <div className="bg-[#151d30] border border-[#232e48] rounded-xl p-4 flex items-center gap-3 col-span-2 lg:col-span-1">
          <div className="p-2 bg-emerald-500/10 rounded-lg text-emerald-400">
            <Trophy className="w-5 h-5" />
          </div>
          <div>
            <div className="text-xl font-bold text-gray-100">{stats?.average_ats_score || 0}%</div>
            <div className="text-xs text-gray-400">Avg ATS Score</div>
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Dynamic Interactive SVG chart */}
        <div className="bg-[#151d30] border border-[#232e48] rounded-xl p-6 lg:col-span-2">
          <h2 className="text-base font-semibold text-gray-200 mb-6">Application Pipelines</h2>
          
          <div className="flex flex-col md:flex-row items-center gap-8 justify-around">
            <div className="relative w-48 h-48">
              {/* Doughnut SVG representation */}
              <svg width="192" height="192" className="transform -rotate-90">
                <circle cx="96" cy="96" r="75" stroke="#1d263b" strokeWidth="18" fill="none" />
                {total > 0 ? (
                  values.map((v, i) => {
                    let accumulated = 0;
                    for (let j = 0; j < i; j++) accumulated += values[j].count;
                    const strokeDasharray = `${(v.count / total) * 471.2} 471.2`;
                    const strokeDashoffset = -((accumulated / total) * 471.2);
                    return (
                      <circle
                        key={v.label}
                        cx="96"
                        cy="96"
                        r="75"
                        stroke={v.color}
                        strokeWidth="18"
                        strokeDasharray={strokeDasharray}
                        strokeDashoffset={strokeDashoffset}
                        fill="none"
                        className="transition-all duration-500 ease-out"
                      />
                    );
                  })
                ) : (
                  <circle cx="96" cy="96" r="75" stroke="#374151" strokeWidth="18" fill="none" />
                )}
              </svg>
              <div className="absolute inset-0 flex flex-col items-center justify-center">
                <div className="text-3xl font-bold text-gray-200">{total}</div>
                <div className="text-xs text-gray-500">Applications</div>
              </div>
            </div>

            {/* Custom Legend */}
            <div className="space-y-3 w-full max-w-[200px]">
              {values.map((val) => (
                <div key={val.label} className="flex items-center justify-between text-sm">
                  <div className="flex items-center gap-2">
                    <span className="w-3 h-3 rounded-full" style={{ backgroundColor: val.color }} />
                    <span className="text-gray-400">{val.label}</span>
                  </div>
                  <span className="font-semibold text-gray-200">{val.count}</span>
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* Recent Applications Pane */}
        <div className="bg-[#151d30] border border-[#232e48] rounded-xl p-6">
          <h2 className="text-base font-semibold text-gray-200 mb-4">Recent Submissions</h2>
          
          {recentApplications.length === 0 ? (
            <div className="text-center py-8 text-sm text-gray-500">
              No applications submitted yet.
            </div>
          ) : (
            <div className="space-y-4">
              {recentApplications.map((app) => (
                <div key={app.id} className="border-b border-[#232e48] pb-3 last:border-0 last:pb-0">
                  <div className="flex justify-between items-start">
                    <div>
                      <h3 className="font-medium text-sm text-gray-200">{app.role_title}</h3>
                      <p className="text-xs text-gray-400 mt-0.5">{app.company}</p>
                    </div>
                    <span className={`text-[10px] px-2 py-0.5 rounded-full font-medium ${
                      app.status === 'offered' ? 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/20' :
                      app.status === 'interviewing' ? 'bg-violet-500/10 text-violet-400 border border-violet-500/20' :
                      app.status === 'applied' ? 'bg-blue-500/10 text-blue-400 border border-blue-500/20' :
                      'bg-amber-500/10 text-amber-400 border border-amber-500/20'
                    }`}>
                      {app.status}
                    </span>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
