import axios from 'axios';

const DJANGO_URL = 'http://localhost:8001/api/v1';
const FASTAPI_URL = 'http://localhost:8000/api/v1';

// Axios Instance for Django (Authenticated Requests)
export const djangoApi = axios.create({
  baseURL: DJANGO_URL,
});

djangoApi.interceptors.request.use((config) => {
  const token = localStorage.getItem('access_token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// Axios Instance for FastAPI (AI Operations)
export const fastapiApi = axios.create({
  baseURL: FASTAPI_URL,
});

export const apiService = {
  // --- Auth Services (Django) ---
  register: (email, password, firstName, lastName) => 
    djangoApi.post('/users/register/', { email, password, first_name: firstName, last_name: lastName }),
  
  login: (email, password) => 
    djangoApi.post('/users/token/', { email, password }),
  
  getUserProfile: () => 
    djangoApi.get('/users/me/'),

  // --- Resume & Database Tracking (Django) ---
  getResumes: () => 
    djangoApi.get('/resumes/'),
  
  createResume: (title) => 
    djangoApi.post('/resumes/', { title }),
  
  getResumeVersions: (resumeId) => 
    djangoApi.get(`/resumes/${resumeId}/`),
  
  setActiveVersion: (resumeId, versionId) => 
    djangoApi.post(`/resumes/${resumeId}/versions/${versionId}/set-active/`),
  
  compareVersions: (resumeId, v1Id, v2Id) => 
    djangoApi.get(`/resumes/${resumeId}/compare/?v1=${v1Id}&v2=${v2Id}`),

  // --- Job Tracking & Dashboard Stats (Django) ---
  getJobApplications: () => 
    djangoApi.get('/jobs/applications/'),
  
  addJobApplication: (company, roleTitle, description, status) => 
    djangoApi.post('/jobs/applications/', { company, role_title: roleTitle, job_description: description, status }),
  
  getDashboardStats: () => 
    djangoApi.get('/jobs/applications/stats/'),
  
  getInterviewSessions: () => 
    djangoApi.get('/jobs/interviews/'),

  // --- AI Operations (FastAPI) ---
  parseResumeFile: (file) => {
    const formData = new FormData();
    formData.append('file', file);
    return fastapiApi.post('/parse/', formData, {
      headers: { 'Content-Type': 'multipart/form-data' }
    });
  },

  // --- Resume Library CRUD (FastAPI) ---
  getLibraryResumes: () => 
    fastapiApi.get('/parse/library'),

  uploadResumeToLibrary: (file) => {
    const formData = new FormData();
    formData.append('file', file);
    return fastapiApi.post('/parse/upload', formData, {
      headers: { 'Content-Type': 'multipart/form-data' }
    });
  },

  parseExistingLibraryResume: (resumeId) => 
    fastapiApi.post(`/parse/library/${resumeId}/parse`),

  getLibraryResumeData: (resumeId) => 
    fastapiApi.get(`/parse/library/${resumeId}/data`),

  saveLibraryResumeData: (resumeId, data) => 
    fastapiApi.post(`/parse/library/${resumeId}/save`, data),

  renameLibraryResume: (resumeId, newName) => 
    fastapiApi.post(`/parse/library/${resumeId}/rename`, { new_name: newName }),

  deleteLibraryResume: (resumeId) => 
    fastapiApi.delete(`/parse/library/${resumeId}`),

  getLibraryResumeDownloadUrl: (resumeId) => 
    `${FASTAPI_URL}/parse/library/${resumeId}/download`,

  evaluateATS: (resume, jobDescription) => 
    fastapiApi.post('/ats/evaluate', { resume, job_description: jobDescription }),
  
  optimizeResume: (resume, jobDescription) => 
    fastapiApi.post('/ats/optimize', { resume, job_description: jobDescription }),
  
  searchJobsOnline: (query, location, resume) => 
    fastapiApi.post('/jobs/search', { query, location, resume }),

  exportPDF: (resume) => 
    fastapiApi.post('/exports/pdf', resume, { responseType: 'blob' }),

  exportDOCX: (resume) => 
    fastapiApi.post('/exports/docx', resume, { responseType: 'blob' }),

  // --- Streaming Chat Helper (FastAPI) ---
  getChatStreamUrl: () => `${FASTAPI_URL}/chat/`
};
