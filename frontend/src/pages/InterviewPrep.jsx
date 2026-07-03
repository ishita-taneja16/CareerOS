import React, { useState, useEffect } from 'react';
import { apiService } from '../services/api';
import { MessageSquare, Play, Send, CheckCircle, HelpCircle, Loader2 } from 'lucide-react';

export default function InterviewPrep({ resume }) {
  const [jobDescription, setJobDescription] = useState('Senior React Developer building agentic software dashboards.');
  const [inProgress, setInProgress] = useState(false);
  const [chatHistory, setChatHistory] = useState([]);
  const [userAnswer, setUserAnswer] = useState('');
  const [sessions, setSessions] = useState([]);
  
  const [loading, setLoading] = useState(false);
  const [streaming, setStreaming] = useState(false);
  const [message, setMessage] = useState('');

  useEffect(() => {
    loadSessions();
  }, []);

  async function loadSessions() {
    try {
      const res = await apiService.getInterviewSessions();
      setSessions(res.data);
    } catch (e) {
      console.error(e);
    }
  }

  const startInterview = () => {
    if (!resume) {
      setMessage('Please upload a resume in the Resume Editor tab first to conduct mock interviews.');
      return;
    }
    setChatHistory([]);
    setInProgress(true);
    // Welcome message from recruiter
    setChatHistory([
      { role: 'assistant', content: "Hello! Welcome to your mock interview session. I am your AI Recruiter today. I have reviewed your profile and the Job Description. Let's get started. Could you start by introducing yourself and outlining a recent complex project you spearheaded?" }
    ]);
  };

  const handleSend = async (e) => {
    e.preventDefault();
    if (!userAnswer.strip || userAnswer.trim() === '' || streaming) return;

    const userMsg = { role: 'user', content: userAnswer };
    const updatedHistory = [...chatHistory, userMsg];
    setChatHistory(updatedHistory);
    setUserAnswer('');
    setStreaming(true);

    try {
      // Connect to the streaming chat SSE backend
      const response = await fetch(apiService.getChatStreamUrl(), {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          user_id: 'local_dev_user',
          messages: updatedHistory,
          job_description: jobDescription,
          structured_resume_data: resume
        })
      });

      if (!response.body) {
        setStreaming(false);
        return;
      }

      const reader = response.body.getReader();
      const decoder = new TextDecoder();
      
      let assistantReply = '';
      setChatHistory(prev => [...prev, { role: 'assistant', content: '' }]);

      while (true) {
        const { value, done } = await reader.read();
        if (done) break;
        
        const chunk = decoder.decode(value, { stream: true });
        // Process SSE lines
        const lines = chunk.split('\n');
        for (const line of lines) {
          if (line.startsWith('event: message')) {
            // Find next line with data
            const dataLine = lines[lines.indexOf(line) + 1];
            if (dataLine && dataLine.startsWith('data:')) {
              try {
                const parsed = JSON.parse(dataLine.replace('data:', '').strip());
                assistantReply += parsed.text;
                setChatHistory(prev => {
                  const copy = [...prev];
                  copy[copy.length - 1].content = assistantReply;
                  return copy;
                });
              } catch (err) {
                console.error(err);
              }
            }
          }
        }
      }
    } catch (err) {
      console.error(err);
    } finally {
      setStreaming(false);
    }
  };

  return (
    <div className="grid grid-cols-1 xl:grid-cols-4 gap-6">
      {/* Sidebar - Sessions history */}
      <div className="bg-[#151d30] border border-[#232e48] rounded-xl p-5 space-y-6">
        <div>
          <h2 className="text-sm font-semibold text-gray-300 uppercase tracking-wider mb-4">Past Feedback Reports</h2>
          {sessions.length === 0 ? (
            <div className="text-xs text-gray-500 text-center py-4">No completed mock sessions yet.</div>
          ) : (
            <div className="space-y-2">
              {sessions.map(s => (
                <div key={s.id} className="p-3 bg-[#0b0f19]/40 border border-[#232e48]/50 rounded-lg text-xs space-y-2">
                  <div className="flex justify-between font-bold text-gray-300">
                    <span>{s.job_details?.role_title || 'Software Role'}</span>
                    <span className="text-indigo-400">{s.overall_score || 0}/5</span>
                  </div>
                  <p className="text-[10px] text-gray-500 line-clamp-2">{s.feedback?.summary || 'Good interview session'}</p>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>

      {/* Main console screen */}
      <div className="bg-[#151d30] border border-[#232e48] rounded-xl p-6 xl:col-span-3 space-y-6">
        {message && (
          <div className="p-3 bg-indigo-500/10 border border-indigo-500/20 text-indigo-400 text-xs rounded-lg text-center flex justify-between items-center">
            <span>{message}</span>
            <button onClick={() => setMessage('')} className="text-gray-400 hover:text-gray-200">×</button>
          </div>
        )}

        {!inProgress ? (
          <div className="space-y-6">
            <div>
              <h2 className="text-lg font-semibold text-gray-200">Setup Simulated Mock Interview</h2>
              <p className="text-xs text-gray-500 mt-1">Practice behavior, system design, and algorithms against an interactive recruiter bot.</p>
            </div>

            <div className="space-y-2">
              <label className="text-[10px] text-gray-400 uppercase tracking-wider font-semibold">Target Job Description</label>
              <textarea
                value={jobDescription}
                onChange={(e) => setJobDescription(e.target.value)}
                className="w-full h-32 bg-[#0b0f19] border border-[#232e48] rounded-lg p-3 text-xs text-gray-200 focus:outline-none focus:border-indigo-500"
              />
            </div>

            <button
              onClick={startInterview}
              className="bg-indigo-600 hover:bg-indigo-500 text-white font-semibold py-2.5 px-6 rounded-lg text-xs transition duration-150 flex items-center gap-2"
            >
              <Play className="w-4 h-4 fill-white" />
              Begin Interview Simulation
            </button>
          </div>
        ) : (
          <div className="flex flex-col h-[550px] bg-[#0b0f19] border border-[#232e48] rounded-xl overflow-hidden relative">
            {/* Header */}
            <div className="bg-[#151d30] border-b border-[#232e48] px-4 py-3 flex justify-between items-center">
              <div className="flex items-center gap-2">
                <span className="w-2.5 h-2.5 rounded-full bg-red-500 animate-pulse" />
                <span className="text-xs font-semibold text-gray-300">Interview in progress</span>
              </div>
              <button
                onClick={() => setInProgress(false)}
                className="text-xs text-gray-500 hover:text-gray-300 transition"
              >
                Quit Session
              </button>
            </div>

            {/* Chat Messages */}
            <div className="flex-1 p-4 overflow-y-auto space-y-4">
              {chatHistory.map((msg, i) => (
                <div key={i} className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}>
                  <div className={`max-w-[75%] rounded-xl p-3 text-xs leading-relaxed ${
                    msg.role === 'user'
                      ? 'bg-indigo-600 text-white rounded-tr-none'
                      : 'bg-[#151d30] border border-[#232e48] text-gray-200 rounded-tl-none'
                  }`}>
                    {msg.content}
                  </div>
                </div>
              ))}
              {streaming && chatHistory[chatHistory.length - 1]?.role === 'user' && (
                <div className="flex justify-start">
                  <div className="bg-[#151d30] border border-[#232e48] rounded-xl rounded-tl-none p-3 flex items-center gap-2">
                    <Loader2 className="w-4 h-4 animate-spin text-indigo-500" />
                    <span className="text-[10px] text-gray-500">Recruiter typing...</span>
                  </div>
                </div>
              )}
            </div>

            {/* Input Form */}
            <form onSubmit={handleSend} className="bg-[#151d30] border-t border-[#232e48] p-3 flex gap-2">
              <input
                type="text"
                value={userAnswer}
                onChange={(e) => setUserAnswer(e.target.value)}
                placeholder="Type your interview answer..."
                className="flex-1 bg-[#0b0f19] border border-[#232e48] rounded-lg px-4 text-xs text-gray-200 focus:outline-none focus:border-indigo-500"
              />
              <button
                type="submit"
                disabled={streaming}
                className="bg-indigo-600 hover:bg-indigo-500 disabled:bg-indigo-800 text-white p-2 rounded-lg transition"
              >
                <Send className="w-4 h-4" />
              </button>
            </form>
          </div>
        )}
      </div>
    </div>
  );
}
