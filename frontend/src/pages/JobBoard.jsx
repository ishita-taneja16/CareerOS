import React, { useState, useEffect } from 'react';
import { apiService } from '../services/api';
import { 
  Search, MapPin, Sparkles, Plus, Check, Loader2, Filter, 
  ChevronDown, ChevronUp, ExternalLink, Calendar, Briefcase, 
  DollarSign, Award, ThumbsUp, AlertCircle, RefreshCw 
} from 'lucide-react';

const SUGGESTED_ROLES = [
  'AI Engineer', 'Machine Learning Engineer', 'LLM Engineer', 
  'Prompt Engineer', 'Generative AI Engineer', 'Python Developer', 
  'Backend AI Engineer', 'Data Scientist', 'Software Engineer', 
  'Frontend Developer', 'Backend Developer', 'Full Stack Developer', 
  'DevOps Engineer', 'Cloud Architect', 'React Developer'
];

const SUGGESTED_LOCATIONS = [
  'India', 'Mohali', 'Mohali, Punjab', 'Bangalore', 
  'Hyderabad', 'Delhi NCR', 'Noida', 'Pune', 'Remote'
];

export default function JobBoard({ 
  resume, 
  activeResumeId, 
  libraryResumes = [], 
  resumeLoading, 
  resumeError, 
  onRetryLoadResume 
}) {
  const activeObj = libraryResumes.find(r => r.id === activeResumeId);
  const isParsedInLibrary = activeObj?.parsed;
  const hasParsedResume = activeResumeId && isParsedInLibrary && resume && !resumeLoading;

  const activeResume = resume;

  const [query, setQuery] = useState('React Developer');
  const [location, setLocation] = useState('Remote');
  
  // Autocomplete Suggestions State
  const [querySuggestions, setQuerySuggestions] = useState([]);
  const [locationSuggestions, setLocationSuggestions] = useState([]);
  const [showQueryDropdown, setShowQueryDropdown] = useState(false);
  const [showLocDropdown, setShowLocDropdown] = useState(false);

  const [results, setResults] = useState([]);
  const [filteredResults, setFilteredResults] = useState([]);
  const [visibleCount, setVisibleCount] = useState(20);
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState('');

  // Expandable JD State
  const [expandedJobIndex, setExpandedJobIndex] = useState(null);

  // Sorting
  const [sortBy, setSortBy] = useState('match'); // match, newest, salary

  // Filters State
  const [filterWorkTypes, setFilterWorkTypes] = useState({ Remote: true, Hybrid: true, Onsite: true });
  const [filterExperience, setFilterExperience] = useState({
    'Fresher': true,
    '0–1 Years': true,
    '1–2 Years': true,
    '2–3 Years': true,
    '3–5 Years': true,
    '5–7 Years': true,
    '7+ Years': true
  });
  const [filterEmployment, setFilterEmployment] = useState({ 'Full-time': true, 'Part-time': true, Contract: true, Internship: true });
  const [filterPosted, setFilterPosted] = useState('all'); // all, 24h, 3d, week, month
  const [filterSalaryMin, setFilterSalaryMin] = useState(0); // minimum in raw value
  const [filterCompanies, setFilterCompanies] = useState({});

  // Tracking saved jobs
  const [savedJobKeys, setSavedJobKeys] = useState({});

  const [loadingStageText, setLoadingStageText] = useState('Searching jobs...');

  // Cycle loading messages during active search
  useEffect(() => {
    if (!loading) return;
    const stages = [
      'Searching Lever...',
      'Searching Greenhouse...',
      'Searching Wellfound...',
      'Searching Company Career Pages...',
      'Merging Results...',
      'Removing Duplicates...',
      'Computing ATS Match...'
    ];
    let current = 0;
    setLoadingStageText(stages[0]);
    const interval = setInterval(() => {
      current += 1;
      if (current < stages.length) {
        setLoadingStageText(stages[current]);
      }
    }, 800);
    return () => clearInterval(interval);
  }, [loading]);

  // Trigger search on mount or when active resume changes
  useEffect(() => {
    if (resume) {
      performSearch();
    }
  }, [resume]);

  // Filter and Sort results client-side for ultra-fast response
  useEffect(() => {
    let filtered = [...results];

    // 1. Filter by Work Type
    filtered = filtered.filter(job => filterWorkTypes[job.work_type]);

    // Helper to map complex experience strings (e.g. "5-8 years") to standard ranges and check overlap
    const getExperienceRangesForJob = (expStr) => {
      if (!expStr || expStr.toLowerCase().includes('not specified')) {
        return ['Fresher', '0–1 Years', '1–2 Years', '2–3 Years', '3–5 Years', '5–7 Years', '7+ Years'];
      }
      const clean = expStr.toLowerCase();
      if (clean.includes('fresher') || clean.includes('entry') || clean.includes('intern')) {
        return ['Fresher', '0–1 Years'];
      }
      const numbers = clean.match(/\d+/g);
      if (!numbers || numbers.length === 0) {
        return ['Fresher', '0–1 Years', '1–2 Years', '2–3 Years', '3–5 Years', '5–7 Years', '7+ Years'];
      }
      const minYears = parseInt(numbers[0]);
      let maxYears = minYears;
      if (clean.includes('+')) {
        maxYears = 99;
      } else if (numbers.length > 1) {
        maxYears = parseInt(numbers[1]);
      }
      const categories = [];
      const checkOverlap = (cMin, cMax) => {
        return Math.max(minYears, cMin) <= Math.min(maxYears, cMax);
      };
      if (checkOverlap(0, 0)) categories.push('Fresher');
      if (checkOverlap(0, 1)) categories.push('0–1 Years');
      if (checkOverlap(1, 2)) categories.push('1–2 Years');
      if (checkOverlap(2, 3)) categories.push('2–3 Years');
      if (checkOverlap(3, 5)) categories.push('3–5 Years');
      if (checkOverlap(5, 7)) categories.push('5–7 Years');
      if (checkOverlap(7, 99)) categories.push('7+ Years');
      return categories;
    };

    // 2. Filter by Experience Level
    filtered = filtered.filter(job => {
      const matchedCategories = getExperienceRangesForJob(job.experience_level);
      return matchedCategories.some(cat => filterExperience[cat]);
    });

    // 3. Filter by Employment Type
    filtered = filtered.filter(job => filterEmployment[job.employment_type]);

    // 4. Filter by Posted Date
    const today = new Date('2026-07-04');
    filtered = filtered.filter(job => {
      if (filterPosted === 'all') return true;
      const posted = new Date(job.posted_date);
      const diffTime = Math.abs(today - posted);
      const diffDays = Math.floor(diffTime / (1000 * 60 * 60 * 24));
      
      if (filterPosted === '24h') return diffDays <= 0;
      if (filterPosted === '3d') return diffDays <= 2;
      if (filterPosted === 'week') return diffDays <= 7;
      if (filterPosted === 'month') return diffDays <= 30;
      return true;
    });

    // 5. Filter by Minimum Salary
    if (filterSalaryMin > 0) {
      filtered = filtered.filter(job => {
        // Handle INR and USD scales
        const maxVal = job.salary_max || 0;
        return maxVal >= filterSalaryMin;
      });
    }

    // 6. Filter by Selected Companies
    const activeCompanies = Object.keys(filterCompanies).filter(c => filterCompanies[c]);
    if (activeCompanies.length > 0) {
      filtered = filtered.filter(job => filterCompanies[job.company]);
    }

    // 7. Sort Results
    filtered.sort((a, b) => {
      if (sortBy === 'match') {
        return b.match_percentage - a.match_percentage;
      }
      if (sortBy === 'newest') {
        return new Date(b.posted_date) - new Date(a.posted_date);
      }
      if (sortBy === 'salary') {
        return b.salary_max - a.salary_max;
      }
      return 0;
    });

    setFilteredResults(filtered);
    setVisibleCount(20);
  }, [results, filterWorkTypes, filterExperience, filterEmployment, filterPosted, filterSalaryMin, filterCompanies, sortBy]);

  // Infinite scroll listener to load 20 more results on scroll
  useEffect(() => {
    const handleScroll = () => {
      if (window.innerHeight + document.documentElement.scrollTop >= document.documentElement.offsetHeight - 100) {
        setVisibleCount(prev => Math.min(prev + 20, filteredResults.length));
      }
    };
    window.addEventListener('scroll', handleScroll);
    return () => window.removeEventListener('scroll', handleScroll);
  }, [filteredResults.length]);

  const handleQueryChange = (val) => {
    setQuery(val);
    if (val.trim()) {
      const filtered = SUGGESTED_ROLES.filter(role => 
        role.toLowerCase().includes(val.toLowerCase())
      );
      setQuerySuggestions(filtered);
      setShowQueryDropdown(true);
    } else {
      setQuerySuggestions([]);
      setShowQueryDropdown(false);
    }
  };

  const handleLocChange = (val) => {
    setLocation(val);
    if (val.trim()) {
      const filtered = SUGGESTED_LOCATIONS.filter(loc => 
        loc.toLowerCase().includes(val.toLowerCase())
      );
      setLocationSuggestions(filtered);
      setShowLocDropdown(true);
    } else {
      setLocationSuggestions([]);
      setShowLocDropdown(false);
    }
  };

  const performSearch = async () => {
    if (!activeResumeId) {
      setMessage('Please select a resume in the left sidebar to enable similarity scoring.');
      return;
    }
    if (activeObj && !activeObj.parsed) {
      setMessage("The active resume has not been parsed. Please click 'Parse Resume' in the Resume Editor tab first.");
      return;
    }
    if (resumeLoading) {
      setMessage('Loading parsed resume data, please wait...');
      return;
    }
    if (resumeError) {
      setMessage('Unable to load parsed resume. Please resolve the load error or click Retry first.');
      return;
    }
    if (!resume) {
      setMessage('Please select or parse a resume first.');
      return;
    }
    setLoading(true);
    setResults([]);
    setMessage('');
    try {
      const res = await apiService.searchJobsOnline(query, location, resume);
      const jobs = res.data.results || [];
      setResults(jobs);
      
      // Initialize company filters
      const uniqueComps = {};
      jobs.forEach(job => {
        uniqueComps[job.company] = false;
      });
      setFilterCompanies(uniqueComps);
      
    } catch (err) {
      setMessage('Job search failed: ' + (err.response?.data?.detail || err.message));
    } finally {
      setLoading(false);
    }
  };

  const handleSearchSubmit = (e) => {
    e.preventDefault();
    performSearch();
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
      setMessage('Failed to save job application.');
    }
  };

  const getRelativeTime = (dateStr) => {
    const today = new Date('2026-07-04');
    const posted = new Date(dateStr);
    const diffTime = today - posted;
    const diffDays = Math.floor(diffTime / (1000 * 60 * 60 * 24));
    
    if (diffDays <= 0) return 'Today';
    if (diffDays === 1) return 'Yesterday';
    if (diffDays < 30) return `${diffDays} days ago`;
    return '1 month ago';
  };

  const toggleCompanyFilter = (companyName) => {
    setFilterCompanies(prev => ({
      ...prev,
      [companyName]: !prev[companyName]
    }));
  };

  const resetFilters = () => {
    setFilterWorkTypes({ Remote: true, Hybrid: true, Onsite: true });
    setFilterExperience({
      'Fresher': true,
      '0–1 Years': true,
      '1–2 Years': true,
      '2–3 Years': true,
      '3–5 Years': true,
      '5–7 Years': true,
      '7+ Years': true
    });
    setFilterEmployment({ 'Full-time': true, 'Part-time': true, Contract: true, Internship: true });
    setFilterPosted('all');
    setFilterSalaryMin(0);
    const resetComps = {};
    results.forEach(j => { resetComps[j.company] = false; });
    setFilterCompanies(resetComps);
  };

  const getAppliedFiltersCount = () => {
    let count = 0;
    
    // Count unchecked work types
    const uncheckedWork = Object.values(filterWorkTypes).filter(v => !v).length;
    count += uncheckedWork;
    
    // Count unchecked experience levels
    const uncheckedExp = Object.values(filterExperience).filter(v => !v).length;
    count += uncheckedExp;
    
    // Count unchecked employment types
    const uncheckedEmp = Object.values(filterEmployment).filter(v => !v).length;
    count += uncheckedEmp;
    
    // Count posted time filter
    if (filterPosted !== 'all') count += 1;
    
    // Count salary filter
    if (filterSalaryMin > 0) count += 1;
    
    // Count checked companies
    const checkedComps = Object.values(filterCompanies).filter(v => v).length;
    count += checkedComps;
    
    return count;
  };

  return (
    <div className="space-y-6">
      {/* Page Title */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-gray-100 flex items-center gap-2">
            <Sparkles className="w-6 h-6 text-indigo-400" />
            AI Job Matcher & Search
          </h1>
          <p className="text-sm text-gray-400">Search online listings and evaluate match compatibility against your parsed resume.</p>
        </div>
        {results.length > 0 && (
          <button 
            onClick={performSearch}
            className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg border border-[#232e48] bg-[#151d30] text-gray-300 hover:text-white text-xs transition"
          >
            <RefreshCw className="w-3.5 h-3.5" />
            Refresh Listings
          </button>
        )}
      </div>

      {/* Loading state for global resume data */}
      {activeResumeId && isParsedInLibrary && resumeLoading && (
        <div className="p-4 bg-indigo-500/10 border border-indigo-500/20 text-indigo-400 text-xs rounded-xl flex items-center gap-2">
          <Loader2 className="w-4 h-4 animate-spin text-indigo-400" />
          <span>Loading parsed resume data...</span>
        </div>
      )}

      {/* Error state for global resume data */}
      {activeResumeId && isParsedInLibrary && resumeError && (
        <div className="p-4 bg-rose-500/10 border border-rose-500/20 text-rose-400 text-xs rounded-xl flex items-center justify-between gap-4">
          <div className="flex items-center gap-2">
            <AlertCircle className="w-5 h-5 shrink-0 text-rose-400" />
            <span>{resumeError}</span>
          </div>
          <button 
            onClick={onRetryLoadResume}
            className="px-3 py-1 bg-rose-600 hover:bg-rose-500 text-white rounded text-[10px] font-bold transition shrink-0"
          >
            Retry
          </button>
        </div>
      )}

      {/* Warning banner when no resume is active or unparsed */}
      {(!activeResumeId || (activeObj && !activeObj.parsed)) && (
        <div className="p-4 bg-amber-500/10 border border-amber-500/20 text-amber-400 text-xs rounded-xl flex items-start gap-2.5">
          <AlertCircle className="w-5 h-5 shrink-0 text-amber-400 mt-0.5" />
          <div>
            <p className="font-semibold text-amber-300">Resume Upload & Parsing Required</p>
            <p className="mt-1 text-gray-400 leading-relaxed">
              {!activeResumeId 
                ? "Please select a resume in the left sidebar first to enable similarity scoring."
                : "The active resume has not been parsed yet. Please parse the resume in the Resume Assistant tab first."
              }
            </p>
          </div>
        </div>
      )}

      {message && (
        <div className="p-3 bg-indigo-500/10 border border-indigo-500/20 text-indigo-400 text-xs rounded-lg text-center flex justify-between items-center">
          <span>{message}</span>
          <button onClick={() => setMessage('')} className="text-gray-400 hover:text-gray-200">×</button>
        </div>
      )}

      {/* Autocomplete Search Header */}
      <form onSubmit={handleSearchSubmit} className="bg-[#151d30] border border-[#232e48] rounded-xl p-5 flex flex-col md:flex-row gap-4 items-end relative z-30">
        
        {/* Job Title Input */}
        <div className="flex-1 space-y-1.5 w-full relative">
          <label className="text-[10px] text-gray-500 uppercase tracking-wider font-semibold">Job Title / Skill</label>
          <div className="relative">
            <Search className="absolute left-3 top-3 w-4 h-4 text-gray-500" />
            <input
              type="text"
              value={query}
              onChange={(e) => handleQueryChange(e.target.value)}
              onFocus={() => setShowQueryDropdown(true)}
              onBlur={() => setTimeout(() => setShowQueryDropdown(false), 200)}
              placeholder="e.g. AI Engineer, React Developer..."
              className="w-full bg-[#0b0f19] border border-[#232e48] rounded-lg py-2 pl-10 pr-4 text-xs text-gray-200 focus:outline-none focus:border-indigo-500"
            />
          </div>
          {showQueryDropdown && querySuggestions.length > 0 && (
            <ul className="absolute left-0 right-0 mt-1 bg-[#151d30] border border-[#232e48] rounded-lg overflow-hidden shadow-lg z-50 max-h-48 overflow-y-auto">
              {querySuggestions.map((role, idx) => (
                <li 
                  key={idx}
                  onMouseDown={() => { setQuery(role); setShowQueryDropdown(false); }}
                  className="px-4 py-2 text-xs text-gray-300 hover:bg-indigo-600 hover:text-white cursor-pointer"
                >
                  {role}
                </li>
              ))}
            </ul>
          )}
        </div>

        {/* Location Input */}
        <div className="flex-1 space-y-1.5 w-full relative">
          <label className="text-[10px] text-gray-500 uppercase tracking-wider font-semibold">Location</label>
          <div className="relative">
            <MapPin className="absolute left-3 top-3 w-4 h-4 text-gray-500" />
            <input
              type="text"
              value={location}
              onChange={(e) => handleLocChange(e.target.value)}
              onFocus={() => setShowLocDropdown(true)}
              onBlur={() => setTimeout(() => setShowLocDropdown(false), 200)}
              placeholder="e.g. Bangalore, Remote, Mohali..."
              className="w-full bg-[#0b0f19] border border-[#232e48] rounded-lg py-2 pl-10 pr-4 text-xs text-gray-200 focus:outline-none focus:border-indigo-500"
            />
          </div>
          {showLocDropdown && locationSuggestions.length > 0 && (
            <ul className="absolute left-0 right-0 mt-1 bg-[#151d30] border border-[#232e48] rounded-lg overflow-hidden shadow-lg z-50 max-h-48 overflow-y-auto">
              {locationSuggestions.map((loc, idx) => (
                <li 
                  key={idx}
                  onMouseDown={() => { setLocation(loc); setShowLocDropdown(false); }}
                  className="px-4 py-2 text-xs text-gray-300 hover:bg-indigo-600 hover:text-white cursor-pointer"
                >
                  {loc}
                </li>
              ))}
            </ul>
          )}
        </div>

        <button
          type="submit"
          disabled={loading}
          className="w-full md:w-auto bg-indigo-600 hover:bg-indigo-500 text-white font-semibold py-2 px-6 rounded-lg text-xs transition duration-150 flex items-center justify-center gap-2 h-10 shrink-0"
        >
          {loading ? (
            <Loader2 className="w-4 h-4 animate-spin text-white" />
          ) : (
            <Sparkles className="w-4 h-4" />
          )}
          Find Matches
        </button>
      </form>

      {/* Main Board Layout */}
      <div className="grid grid-cols-1 lg:grid-cols-4 gap-6 items-start relative z-10">
        
        {/* Filters Panel */}
        <div className="lg:col-span-1 bg-[#151d30] border border-[#232e48] rounded-xl p-5 space-y-6">
          <div className="flex items-center justify-between border-b border-[#232e48] pb-3">
            <span className="text-xs font-bold text-gray-200 uppercase tracking-wider flex items-center gap-1">
              <Filter className="w-3.5 h-3.5 text-indigo-400" />
              Filters ({getAppliedFiltersCount()} Applied)
            </span>
            <button 
              onClick={resetFilters} 
              className="text-[10px] text-indigo-400 hover:text-indigo-300 font-semibold"
            >
              Reset All
            </button>
          </div>

          {/* Work Type Filter */}
          <div className="space-y-2">
            <label className="text-[10px] text-gray-500 uppercase tracking-wider font-semibold">Work Type</label>
            <div className="space-y-1.5">
              {['Remote', 'Hybrid', 'Onsite'].map(type => (
                <label key={type} className="flex items-center gap-2 text-xs text-gray-300 cursor-pointer">
                  <input
                    type="checkbox"
                    checked={filterWorkTypes[type]}
                    onChange={() => setFilterWorkTypes(prev => ({ ...prev, [type]: !prev[type] }))}
                    className="rounded border-[#232e48] text-indigo-600 focus:ring-0 focus:ring-offset-0 bg-[#0b0f19]"
                  />
                  {type}
                </label>
              ))}
            </div>
          </div>

          {/* Experience Level Filter */}
          <div className="space-y-2">
            <label className="text-[10px] text-gray-500 uppercase tracking-wider font-semibold">Experience Level</label>
            <div className="space-y-1.5">
              {['Fresher', '0–1 Years', '1–2 Years', '2–3 Years', '3–5 Years', '5–7 Years', '7+ Years'].map(level => (
                <label key={level} className="flex items-center gap-2 text-xs text-gray-300 cursor-pointer">
                  <input
                    type="checkbox"
                    checked={filterExperience[level]}
                    onChange={() => setFilterExperience(prev => ({ ...prev, [level]: !prev[level] }))}
                    className="rounded border-[#232e48] text-indigo-600 focus:ring-0 focus:ring-offset-0 bg-[#0b0f19]"
                  />
                  {level}
                </label>
              ))}
            </div>
          </div>

          {/* Employment Type Filter */}
          <div className="space-y-2">
            <label className="text-[10px] text-gray-500 uppercase tracking-wider font-semibold">Employment Type</label>
            <div className="space-y-1.5">
              {['Full-time', 'Part-time', 'Contract', 'Internship'].map(type => (
                <label key={type} className="flex items-center gap-2 text-xs text-gray-300 cursor-pointer">
                  <input
                    type="checkbox"
                    checked={filterEmployment[type]}
                    onChange={() => setFilterEmployment(prev => ({ ...prev, [type]: !prev[type] }))}
                    className="rounded border-[#232e48] text-indigo-600 focus:ring-0 focus:ring-offset-0 bg-[#0b0f19]"
                  />
                  {type}
                </label>
              ))}
            </div>
          </div>

          {/* Date Filter */}
          <div className="space-y-2">
            <label className="text-[10px] text-gray-500 uppercase tracking-wider font-semibold">Posted Date</label>
            <select
              value={filterPosted}
              onChange={(e) => setFilterPosted(e.target.value)}
              className="w-full bg-[#0b0f19] border border-[#232e48] rounded-lg py-2 px-3 text-xs text-gray-300 focus:outline-none focus:border-indigo-500"
            >
              <option value="all">Anytime</option>
              <option value="24h">Last 24 Hours</option>
              <option value="3d">Last 3 Days</option>
              <option value="week">Last Week</option>
              <option value="month">Last Month</option>
            </select>
          </div>

          {/* Salary Filter */}
          <div className="space-y-2">
            <label className="text-[10px] text-gray-500 uppercase tracking-wider font-semibold">Minimum Salary</label>
            <select
              value={filterSalaryMin}
              onChange={(e) => setFilterSalaryMin(Number(e.target.value))}
              className="w-full bg-[#0b0f19] border border-[#232e48] rounded-lg py-2 px-3 text-xs text-gray-300 focus:outline-none focus:border-indigo-500"
            >
              <option value="0">Any Salary</option>
              <option value="1000000">₹10L+ / $100k+</option>
              <option value="2000000">₹20L+ / $200k+</option>
              <option value="3000000">₹30L+ / $300k+</option>
            </select>
          </div>

          {/* Company Filter */}
          {Object.keys(filterCompanies).length > 0 && (
            <div className="space-y-2 max-h-48 overflow-y-auto pr-1">
              <label className="text-[10px] text-gray-500 uppercase tracking-wider font-semibold">Companies</label>
              <div className="space-y-1.5">
                {Object.keys(filterCompanies).map(company => (
                  <label key={company} className="flex items-center gap-2 text-xs text-gray-300 cursor-pointer">
                    <input
                      type="checkbox"
                      checked={filterCompanies[company]}
                      onChange={() => toggleCompanyFilter(company)}
                      className="rounded border-[#232e48] text-indigo-600 focus:ring-0 focus:ring-offset-0 bg-[#0b0f19]"
                    />
                    {company}
                  </label>
                ))}
              </div>
            </div>
          )}
        </div>

        {/* Listings column */}
        <div className="lg:col-span-3 space-y-4">
          
          {/* Sorting & Result Counters */}
          {results.length > 0 && (
            <div className="bg-[#151d30]/60 border border-[#232e48]/80 rounded-xl px-4 py-2.5 flex items-center justify-between gap-4">
              <span className="text-xs text-gray-400">
                Found <span className="text-gray-200 font-semibold">{filteredResults.length}</span> matching jobs
              </span>
              <div className="flex items-center gap-2">
                <span className="text-[10px] text-gray-500 uppercase font-semibold">Sort By</span>
                <select
                  value={sortBy}
                  onChange={(e) => setSortBy(e.target.value)}
                  className="bg-[#0b0f19] border border-[#232e48] rounded px-2.5 py-1 text-xs text-gray-300 focus:outline-none"
                >
                  <option value="match">Highest Match</option>
                  <option value="newest">Newest</option>
                  <option value="salary">Highest Salary</option>
                </select>
              </div>
            </div>
          )}

          {/* Results Listings */}
          {loading ? (
            <div className="flex flex-col items-center justify-center py-24 bg-[#151d30]/30 border border-[#232e48] rounded-xl space-y-2">
              <Loader2 className="w-10 h-10 text-indigo-500 animate-spin mb-3" />
              <span className="text-xs text-gray-200 font-semibold">{loadingStageText}</span>
            </div>
          ) : filteredResults.length > 0 ? (
            <div className="space-y-4">
              {filteredResults.slice(0, visibleCount).map((job, idx) => {
                const isExpanded = expandedJobIndex === idx;
                
                return (
                  <div 
                    key={idx} 
                    className="bg-[#151d30] border border-[#232e48] rounded-xl overflow-hidden hover:border-indigo-500/30 transition shadow-lg"
                  >
                    {/* Primary Info Row */}
                    <div className="p-5 flex flex-col md:flex-row justify-between gap-4 items-start">
                      
                      {/* Left: Company Details & Title */}
                      <div className="flex gap-4 items-start flex-1">
                        
                        {/* Company Logo with fallback */}
                        <div className="w-12 h-12 rounded-lg bg-[#0b0f19] border border-[#232e48] flex items-center justify-center overflow-hidden shrink-0">
                          {job.logo ? (
                            <img 
                              src={job.logo} 
                              alt={`${job.company} logo`} 
                              className="w-8 h-8 object-contain"
                              onError={(e) => { e.target.src = ''; e.target.parentNode.innerHTML = `<span class="text-sm font-bold text-indigo-400">${job.company[0]}</span>`; }}
                            />
                          ) : (
                            <span className="text-sm font-bold text-indigo-400">{job.company[0]}</span>
                          )}
                        </div>

                        {/* Title details */}
                        <div className="space-y-1">
                          <div className="flex items-center gap-2 flex-wrap">
                            <h3 className="text-sm font-semibold text-gray-200">{job.role_title}</h3>
                            {job.verified && (
                              <span className="flex items-center gap-0.5 text-[9px] bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 px-1.5 py-0.2 rounded font-bold uppercase shrink-0">
                                <Award className="w-2.5 h-2.5" />
                                Verified
                              </span>
                            )}
                            <span className="text-[9px] px-2 py-0.5 rounded bg-indigo-500/10 text-indigo-400 border border-indigo-500/20 font-bold uppercase shrink-0">
                              {job.source}
                            </span>
                          </div>
                          
                          <div className="text-[11px] text-gray-400 flex flex-wrap gap-x-4 gap-y-1">
                            <span className="font-semibold text-gray-300">🏢 {job.company}</span>
                            <span>📍 {job.location}</span>
                            <span>🎓 {job.experience_level}</span>
                            <span>💼 {job.employment_type} ({job.work_type})</span>
                            <span>💰 {job.salary}</span>
                            <span className="text-gray-500">📅 {getRelativeTime(job.posted_date)}</span>
                            {job.job_id && <span className="text-gray-500">🆔 {job.job_id}</span>}
                          </div>
                        </div>
                      </div>

                      {/* Right: Scores & Actions */}
                      <div className="flex flex-row md:flex-col items-center justify-between md:justify-center gap-3 w-full md:w-auto border-t md:border-t-0 border-[#232e48] pt-3 md:pt-0 shrink-0">
                        <div className="text-center md:mb-1">
                          <div className="text-2xl font-bold text-gray-100">{job.match_percentage}%</div>
                          <div className="text-[8px] text-gray-500 uppercase font-bold tracking-wider">Match Score</div>
                        </div>

                        <div className="flex items-center gap-2">
                          <button
                            onClick={() => setExpandedJobIndex(isExpanded ? null : idx)}
                            className="bg-[#0b0f19] hover:bg-[#111728] border border-[#232e48] text-gray-300 py-1.5 px-3 rounded-lg text-xs font-semibold flex items-center gap-1"
                          >
                            {isExpanded ? <ChevronUp className="w-3.5 h-3.5" /> : <ChevronDown className="w-3.5 h-3.5" />}
                            View JD
                          </button>

                          {savedJobKeys[idx] ? (
                            <button className="bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 py-1.5 px-3 rounded-lg text-xs font-semibold flex items-center gap-1">
                              <Check className="w-3.5 h-3.5" />
                              Saved
                            </button>
                          ) : (
                            <button
                              onClick={() => handleSaveJob(job, idx)}
                              className="bg-indigo-600 hover:bg-indigo-500 text-white py-1.5 px-3 rounded-lg text-xs font-semibold flex items-center gap-1"
                            >
                              <Plus className="w-3.5 h-3.5" />
                              Save Job
                            </button>
                          )}
                        </div>
                      </div>
                    </div>

                    {/* Expandable Section */}
                    {isExpanded && (
                      <div className="bg-[#0b0f19]/70 border-t border-[#232e48] p-5 space-y-4 text-xs text-gray-300">
                        {/* Skills Analysis */}
                        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                          {/* Matched Skills */}
                          <div className="space-y-1.5">
                            <div className="text-[10px] text-gray-500 font-bold uppercase tracking-wider">Matched Skills</div>
                            <div className="flex flex-wrap gap-1.5">
                              {job.matched_skills && job.matched_skills.length > 0 ? (
                                job.matched_skills.map((skill, sIdx) => (
                                  <span key={sIdx} className="bg-emerald-500/15 border border-emerald-500/25 text-emerald-400 text-[10px] font-bold px-2 py-0.5 rounded-full capitalize">
                                    ✓ {skill}
                                  </span>
                                ))
                              ) : (
                                <span className="text-gray-500 italic text-[11px]">No matching tech keywords detected.</span>
                              )}
                            </div>
                          </div>

                          {/* Missing Skills */}
                          <div className="space-y-1.5">
                            <div className="text-[10px] text-gray-500 font-bold uppercase tracking-wider">Missing Skills</div>
                            <div className="flex flex-wrap gap-1.5">
                              {job.missing_skills && job.missing_skills.length > 0 ? (
                                job.missing_skills.map((skill, sIdx) => (
                                  <span key={sIdx} className="bg-red-500/15 border border-red-500/25 text-red-400 text-[10px] font-bold px-2 py-0.5 rounded-full capitalize">
                                    ✗ {skill}
                                  </span>
                                ))
                              ) : (
                                <span className="text-emerald-400 italic text-[11px]">0 missing skills! Perfect tech alignment.</span>
                              )}
                            </div>
                          </div>
                        </div>

                        {/* Explanation block */}
                        <div className="bg-[#0b0f19] border border-[#232e48] p-3 rounded-lg text-indigo-400 leading-relaxed">
                          <span className="font-semibold text-indigo-300">AI Match Details:</span> {job.explanation}
                        </div>

                        {/* Job Description Text */}
                        <div className="space-y-1.5">
                          <div className="text-[10px] text-gray-500 font-bold uppercase tracking-wider">Full Job Description</div>
                          <p className="leading-relaxed whitespace-pre-line text-gray-400 text-[11px]">{job.job_description}</p>
                        </div>

                        {/* Actions row */}
                        <div className="flex justify-end pt-2">
                          <a 
                            href={job.apply_url} 
                            target="_blank" 
                            rel="noopener noreferrer"
                            className="bg-indigo-600 hover:bg-indigo-500 text-white font-semibold py-2 px-4 rounded-lg text-xs flex items-center gap-1.5 transition"
                          >
                            Apply Now
                            <ExternalLink className="w-3.5 h-3.5" />
                          </a>
                        </div>
                      </div>
                    )}
                  </div>
                );
              })}
            </div>
          ) : (
            <div className="bg-[#151d30] border border-[#232e48] rounded-xl p-16 text-center text-gray-400 text-xs flex flex-col items-center">
              <span className="font-semibold text-gray-200 text-sm">No matching jobs found.</span>
              <div className="text-left space-y-1.5 mt-4 text-gray-400 max-w-sm">
                <p className="font-bold text-gray-500 text-[10px] uppercase tracking-wider mb-2">Suggestions:</p>
                <p>• Try another keyword</p>
                <p>• Search a broader location</p>
                <p>• Reduce filters</p>
                <p>• Search jobs from the last week</p>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
