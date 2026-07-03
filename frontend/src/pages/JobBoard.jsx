import React, { useState } from 'react';
import { apiService } from '../services/api';
import { Search, MapPin, Sparkles, Plus, Check, Loader2 } from 'lucide-react';

export default function JobBoard({ resume }) {
  const [query, setQuery] = useState('React Developer');
  const [location, setLocation] = useState('Remote');
  const [results, setResults] = useState([]);
  const [loading, setLoading] = useState(false);
  
  // Tracking saved jobs
  const [savedJobKeys, setSavedJobKeys] = useState({});
  const [message, setMessage] = useState('');

  const handleSearch = async (e) => {
    e.preventDefault();
    if (!resume) {
      setMessage('Please upload a resume in the Resume Editor tab first to enable similarity scoring.');
      return;
    }
    setLoading(true);
    setResults([]);
    setMessage('');
    try {
      const res = await apiService.searchJobsOnline(query, location, resume);
      setResults(res.data.results);
    } catch (err) {
      setMessage('Job search failed: ' + (err.response?.data?.detail || err.message));
    } finally {
      setLoading(false);
    }
  };

  const handleSaveJob = async (job, index) => {
    try {
      await apiService.addJobApplication(
        job.company,
        job.role_title,
        job.job_description,
        'saved'
      );
      setSavedJobKeys(prev => ({ ...prev, [index]: true }));
      setMessage(`Saved job for ${job.role_title} at ${job.company}!`);
    } catch (err) {
      console.error(err);
    }
  };

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-100">Job Board & Matcher</h1>
        <p className="text-sm text-gray-400">Search vacancies online and compute similarity ratings against your resume.</p>
      </div>

      {message && (
        <div className="p-3 bg-indigo-500/10 border border-indigo-500/20 text-indigo-400 text-xs rounded-lg text-center flex justify-between items-center">
          <span>{message}</span>
          <button onClick={() => setMessage('')} className="text-gray-400 hover:text-gray-200">×</button>
        </div>
      )}

      {/* Search Header */}
      <form onSubmit={handleSearch} className="bg-[#151d30] border border-[#232e48] rounded-xl p-5 flex flex-col md:flex-row gap-4 items-end">
        <div className="flex-1 space-y-1.5 w-full">
          <label className="text-[10px] text-gray-500 uppercase tracking-wider font-semibold">Job Title / Skill</label>
          <div className="relative">
            <Search className="absolute left-3 top-3 w-4 h-4 text-gray-500" />
            <input
              type="text"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              placeholder="e.g. AI Engineer, Python..."
              className="w-full bg-[#0b0f19] border border-[#232e48] rounded-lg py-2 pl-10 pr-4 text-xs text-gray-200 focus:outline-none focus:border-indigo-500"
            />
          </div>
        </div>

        <div className="flex-1 space-y-1.5 w-full">
          <label className="text-[10px] text-gray-500 uppercase tracking-wider font-semibold">Location</label>
          <div className="relative">
            <MapPin className="absolute left-3 top-3 w-4 h-4 text-gray-500" />
            <input
              type="text"
              value={location}
              onChange={(e) => setLocation(e.target.value)}
              placeholder="e.g. Remote, Hybrid..."
              className="w-full bg-[#0b0f19] border border-[#232e48] rounded-lg py-2 pl-10 pr-4 text-xs text-gray-200 focus:outline-none focus:border-indigo-500"
            />
          </div>
        </div>

        <button
          type="submit"
          disabled={loading}
          className="w-full md:w-auto bg-indigo-600 hover:bg-indigo-500 text-white font-semibold py-2 px-6 rounded-lg text-xs transition duration-150 flex items-center justify-center gap-2 h-10"
        >
          {loading ? (
            <Loader2 className="w-4 h-4 animate-spin text-white" />
          ) : (
            <Sparkles className="w-4 h-4" />
          )}
          Find Matches
        </button>
      </form>

      {/* Results Listings */}
      {loading ? (
        <div className="flex items-center justify-center py-20">
          <Loader2 className="w-8 h-8 text-indigo-500 animate-spin" />
        </div>
      ) : results.length > 0 ? (
        <div className="space-y-4">
          {results.map((job, idx) => (
            <div key={idx} className="bg-[#151d30] border border-[#232e48] rounded-xl p-5 flex flex-col md:flex-row justify-between gap-4 items-start md:items-center hover:border-indigo-500/30 transition">
              <div className="space-y-2 flex-1">
                <div className="flex items-center gap-3">
                  <h3 className="text-base font-semibold text-gray-200">{job.role_title}</h3>
                  <span className="text-[10px] px-2 py-0.5 rounded bg-indigo-500/10 text-indigo-400 border border-indigo-500/20 font-bold uppercase">{job.source}</span>
                </div>
                <div className="text-xs text-gray-400 flex flex-wrap gap-x-4 gap-y-1">
                  <span>🏢 {job.company}</span>
                  <span>📍 {job.location}</span>
                  {job.salary !== 'N/A' && <span>💰 {job.salary}</span>}
                </div>
                <p className="text-xs text-gray-400 line-clamp-2">{job.job_description}</p>
                <div className="text-[11px] bg-[#0b0f19] border border-[#232e48]/50 p-2.5 rounded text-indigo-400 italic">
                  💡 {job.explanation}
                </div>
              </div>

              <div className="flex flex-row md:flex-col items-center justify-between md:justify-center gap-4 w-full md:w-auto border-t md:border-t-0 border-[#232e48] pt-3 md:pt-0">
                <div className="text-center">
                  <div className="text-2xl font-bold text-gray-100">{job.match_percentage}%</div>
                  <div className="text-[9px] text-gray-500 uppercase font-semibold">Match Score</div>
                </div>
                {savedJobKeys[idx] ? (
                  <button className="bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 py-1.5 px-4 rounded-lg text-xs font-semibold flex items-center gap-1">
                    <Check className="w-3.5 h-3.5" />
                    Saved
                  </button>
                ) : (
                  <button
                    onClick={() => handleSaveJob(job, idx)}
                    className="bg-indigo-600 hover:bg-indigo-500 text-white py-1.5 px-4 rounded-lg text-xs font-semibold flex items-center gap-1"
                  >
                    <Plus className="w-3.5 h-3.5" />
                    Save Job
                  </button>
                )}
              </div>
            </div>
          ))}
        </div>
      ) : (
        <div className="bg-[#151d30] border border-[#232e48] rounded-xl p-16 text-center text-gray-500 text-xs">
          No matches loaded. Run search to crawl and check listings.
        </div>
      )}
    </div>
  );
}
