import React, { useState, useEffect, useRef } from 'react';
import {
  Sparkles, FileText, Briefcase, ShieldAlert, ArrowRight,
  CheckCircle2, Zap, Brain, Target, Star, ChevronRight,
  BarChart3, Search, MessageSquare, Award, TrendingUp, Users
} from 'lucide-react';

/* ─── tiny hook: detect if element is on screen ─── */
function useInView(threshold = 0.15) {
  const ref = useRef(null);
  const [inView, setInView] = useState(false);
  useEffect(() => {
    const obs = new IntersectionObserver(([e]) => {
      if (e.isIntersecting) { setInView(true); obs.disconnect(); }
    }, { threshold });
    if (ref.current) obs.observe(ref.current);
    return () => obs.disconnect();
  }, [threshold]);
  return [ref, inView];
}

/* ─── Animated counter ─── */
function Counter({ end, suffix = '', duration = 2000 }) {
  const [count, setCount] = useState(0);
  const [ref, inView] = useInView();
  useEffect(() => {
    if (!inView) return;
    let start = 0;
    const step = Math.ceil(end / (duration / 16));
    const timer = setInterval(() => {
      start = Math.min(start + step, end);
      setCount(start);
      if (start >= end) clearInterval(timer);
    }, 16);
    return () => clearInterval(timer);
  }, [inView, end, duration]);
  return <span ref={ref}>{count.toLocaleString()}{suffix}</span>;
}

/* ─── Feature card ─── */
function FeatureCard({ icon: Icon, title, description, delay }) {
  const [ref, inView] = useInView();
  return (
    <div
      ref={ref}
      style={{ transitionDelay: `${delay}ms` }}
      className={`group relative p-6 rounded-2xl border border-white/5 bg-[#151d30]/60 backdrop-blur-sm
        hover:border-indigo-500/30 hover:bg-[#1a2540]/80 transition-all duration-500 cursor-default
        ${inView ? 'opacity-100 translate-y-0' : 'opacity-0 translate-y-8'}`}
    >
      <div className="absolute inset-0 rounded-2xl opacity-0 group-hover:opacity-100 transition-opacity duration-500 bg-gradient-to-br from-indigo-500/5 to-violet-500/5 blur-xl -z-10" />
      <div className="inline-flex p-2.5 rounded-xl mb-4" style={{ background: 'rgba(99,102,241,0.12)', border: '1px solid rgba(99,102,241,0.2)' }}>
        <Icon className="w-5 h-5 text-indigo-400" />
      </div>
      <h3 className="text-sm font-bold text-gray-100 mb-2">{title}</h3>
      <p className="text-xs text-gray-400 leading-relaxed">{description}</p>
    </div>
  );
}

/* ─── Testimonial card ─── */
function TestimonialCard({ name, role, company, quote, avatar, delay }) {
  const [ref, inView] = useInView();
  return (
    <div
      ref={ref}
      style={{ transitionDelay: `${delay}ms` }}
      className={`p-6 rounded-2xl border border-white/5 bg-[#151d30]/60 backdrop-blur-sm
        transition-all duration-700
        ${inView ? 'opacity-100 translate-y-0' : 'opacity-0 translate-y-8'}`}
    >
      <div className="flex gap-1 mb-4">
        {[...Array(5)].map((_, i) => <Star key={i} className="w-3.5 h-3.5 fill-amber-400 text-amber-400" />)}
      </div>
      <p className="text-sm text-gray-300 leading-relaxed italic mb-5">"{quote}"</p>
      <div className="flex items-center gap-3">
        <div className="w-9 h-9 rounded-full bg-gradient-to-br from-indigo-500 to-violet-600 flex items-center justify-center text-white font-bold text-xs">
          {avatar}
        </div>
        <div>
          <div className="text-xs font-bold text-gray-100">{name}</div>
          <div className="text-[10px] text-gray-500">{role} · {company}</div>
        </div>
      </div>
    </div>
  );
}

/* ─── Step card ─── */
function StepCard({ icon: Icon, title, desc, index }) {
  const [ref, inView] = useInView();
  return (
    <div
      ref={ref}
      style={{ transitionDelay: `${index * 120}ms` }}
      className={`flex flex-col items-center text-center transition-all duration-700 ${inView ? 'opacity-100 translate-y-0' : 'opacity-0 translate-y-8'}`}
    >
      <div className="relative mb-5">
        <div className="w-20 h-20 rounded-2xl bg-gradient-to-br from-indigo-500/20 to-violet-500/20 border border-indigo-500/20 flex items-center justify-center">
          <Icon className="w-8 h-8 text-indigo-400" />
        </div>
        <div className="absolute -top-2 -right-2 w-6 h-6 rounded-full bg-indigo-600 border-2 border-[#0b0f19] flex items-center justify-center text-[10px] font-extrabold text-white">
          {index + 1}
        </div>
      </div>
      <h3 className="text-sm font-bold text-gray-100 mb-2">{title}</h3>
      <p className="text-xs text-gray-400 leading-relaxed">{desc}</p>
    </div>
  );
}

/* ════════════════════════════════════════════════ */
export default function LandingPage({ onEnterApp }) {
  const [scrolled, setScrolled] = useState(false);
  const [heroRef, heroInView] = useInView(0.05);

  useEffect(() => {
    const handler = () => setScrolled(window.scrollY > 20);
    window.addEventListener('scroll', handler);
    return () => window.removeEventListener('scroll', handler);
  }, []);

  const features = [
    { icon: Brain, title: 'AI-Powered Resume Analysis', description: 'Upload your resume and get instant AI feedback, ATS score, and actionable improvement suggestions in seconds.' },
    { icon: Target, title: 'Smart Job Matching', description: 'Paste a job description and see exactly how well your profile matches — with a detailed skill gap breakdown.' },
    { icon: MessageSquare, title: 'AI Interview Coach', description: 'Practice with role-specific interview questions tailored to your resume and the job you are targeting.' },
    { icon: FileText, title: 'Resume Library', description: 'Store and manage multiple resume versions. Switch between them instantly for different job applications.' },
    { icon: BarChart3, title: 'ATS Optimisation', description: 'Ensure your resume passes Applicant Tracking Systems with keyword analysis and formatting guidance.' },
    { icon: Zap, title: 'Instant AI Chat', description: 'Ask anything career-related — from salary negotiation tips to how to write the perfect cover letter.' },
  ];

  const testimonials = [
    { name: 'Priya Sharma', role: 'Software Engineer', company: 'Microsoft', quote: 'CareerOS helped me identify the exact skill gaps that were costing me interviews. Landed my dream role in 6 weeks.', avatar: 'PS' },
    { name: 'James Liu', role: 'Product Manager', company: 'Stripe', quote: 'The AI interview coach is unreal. I practised 50+ questions tailored to my exact target role. Got the offer!', avatar: 'JL' },
    { name: 'Ananya Nair', role: 'Data Scientist', company: 'Google', quote: 'My ATS score went from 42% to 91% in one session. The resume feedback is incredibly detailed and actionable.', avatar: 'AN' },
  ];

  const steps = [
    { icon: FileText, title: 'Upload your resume', desc: 'PDF or DOCX — our AI parses it in seconds.' },
    { icon: Search, title: 'Match to jobs', desc: 'Paste any job description for instant fit analysis.' },
    { icon: Award, title: 'Ace the interview', desc: 'Practice with AI until you feel completely ready.' },
    { icon: TrendingUp, title: 'Land your dream role', desc: 'Join thousands of professionals who already did.' },
  ];

  return (
    <div className="min-h-screen bg-[#0b0f19] text-gray-200 overflow-x-hidden">

      {/* Ambient background orbs */}
      <div className="fixed inset-0 pointer-events-none overflow-hidden -z-10">
        <div className="absolute top-[-15%] left-[-10%] w-[55vw] h-[55vw] rounded-full bg-indigo-600/8 blur-[140px] animate-pulse" style={{ animationDuration: '8s' }} />
        <div className="absolute bottom-[-10%] right-[-10%] w-[50vw] h-[50vw] rounded-full bg-violet-600/8 blur-[140px] animate-pulse" style={{ animationDuration: '10s', animationDelay: '2s' }} />
        <div className="absolute top-[40%] left-[45%] w-[30vw] h-[30vw] rounded-full bg-cyan-600/5 blur-[120px] animate-pulse" style={{ animationDuration: '12s', animationDelay: '4s' }} />
      </div>

      {/* ══ NAVBAR ══ */}
      <nav className={`fixed top-0 inset-x-0 z-50 transition-all duration-300 ${scrolled ? 'bg-[#0b0f19]/90 backdrop-blur-xl border-b border-white/5 shadow-2xl' : ''}`}>
        <div className="max-w-6xl mx-auto px-6 py-4 flex items-center justify-between">
          <div className="flex items-center gap-2.5">
            <div className="p-1.5 bg-indigo-500/15 rounded-lg border border-indigo-500/25">
              <Sparkles className="w-5 h-5 text-indigo-400" />
            </div>
            <span className="font-bold text-sm text-white tracking-tight">CareerOS</span>
            <span className="hidden sm:inline-block text-[10px] font-semibold text-indigo-400 bg-indigo-500/10 border border-indigo-500/20 px-2 py-0.5 rounded-full">AI Powered</span>
          </div>
          <div className="hidden md:flex items-center gap-8 text-xs text-gray-400 font-medium">
            <a href="#features" className="hover:text-white transition">Features</a>
            <a href="#how-it-works" className="hover:text-white transition">How it works</a>
            <a href="#testimonials" className="hover:text-white transition">Testimonials</a>
          </div>
          <div className="flex items-center gap-3">
            <button id="nav-signin-btn" onClick={() => onEnterApp('login')} className="text-xs text-gray-300 hover:text-white font-medium transition hidden sm:block">
              Sign In
            </button>
            <button id="nav-getstarted-btn" onClick={() => onEnterApp('register')} className="flex items-center gap-1.5 bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-semibold px-4 py-2 rounded-lg transition duration-150 shadow-lg shadow-indigo-500/20">
              Get Started <ArrowRight className="w-3.5 h-3.5" />
            </button>
          </div>
        </div>
      </nav>

      {/* ══ HERO ══ */}
      <section className="pt-32 pb-20 px-6 relative">
        <div ref={heroRef} className={`max-w-6xl mx-auto transition-all duration-1000 ${heroInView ? 'opacity-100 translate-y-0' : 'opacity-0 translate-y-12'}`}>
          <div className="flex justify-center mb-6">
            <div className="flex items-center gap-2 bg-indigo-500/10 border border-indigo-500/20 text-indigo-300 text-xs font-semibold px-4 py-1.5 rounded-full">
              <Zap className="w-3 h-3" /> AI-powered career acceleration platform
            </div>
          </div>
          <h1 className="text-center text-4xl sm:text-5xl md:text-6xl font-extrabold leading-[1.1] tracking-tight mb-6">
            Land your dream job{' '}
            <span className="bg-gradient-to-r from-indigo-400 via-violet-400 to-cyan-400 bg-clip-text text-transparent">10× faster</span>
            <br className="hidden sm:block" />
            {' '}with AI that works for you
          </h1>
          <p className="text-center text-gray-400 text-sm sm:text-base max-w-2xl mx-auto mb-10 leading-relaxed">
            CareerOS analyses your resume, matches you to jobs, coaches you for interviews,
            and gives you the unfair advantage you need — all in one intelligent workspace.
          </p>
          <div className="flex flex-col sm:flex-row items-center justify-center gap-4 mb-14">
            <button id="hero-getstarted-btn" onClick={() => onEnterApp('register')}
              className="group flex items-center gap-2 bg-gradient-to-r from-indigo-600 to-violet-600 hover:from-indigo-500 hover:to-violet-500 text-white font-bold px-7 py-3.5 rounded-xl text-sm transition-all duration-200 shadow-xl shadow-indigo-500/25 hover:shadow-indigo-500/40 hover:-translate-y-0.5">
              Start for free <ArrowRight className="w-4 h-4 group-hover:translate-x-0.5 transition-transform" />
            </button>
            <button id="hero-signin-btn" onClick={() => onEnterApp('login')}
              className="flex items-center gap-2 border border-white/10 hover:border-indigo-500/40 bg-white/5 hover:bg-indigo-500/5 text-gray-200 font-semibold px-7 py-3.5 rounded-xl text-sm transition-all duration-200 hover:-translate-y-0.5">
              Sign in to dashboard <ChevronRight className="w-4 h-4" />
            </button>
          </div>
          <div className="flex flex-wrap items-center justify-center gap-6 text-xs text-gray-500 mb-14">
            {['No credit card required', 'Free to get started', 'Trusted by 10,000+ job seekers'].map(t => (
              <div key={t} className="flex items-center gap-1.5">
                <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400" /> {t}
              </div>
            ))}
          </div>
          {/* Hero image */}
          <div className="relative rounded-2xl overflow-hidden border border-white/5 shadow-2xl shadow-indigo-500/10 group">
            <div className="absolute inset-0 bg-gradient-to-t from-[#0b0f19] via-transparent to-transparent z-10 pointer-events-none" />
            <img src="/hero-visual.jpg" alt="CareerOS AI dashboard" className="w-full h-auto object-cover group-hover:scale-[1.02] transition-transform duration-700" />
            <div className="absolute bottom-6 left-6 z-20 flex items-center gap-3 bg-[#0b0f19]/80 backdrop-blur-md border border-white/10 rounded-xl px-4 py-3 shadow-xl">
              <div className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse" />
              <span className="text-xs font-semibold text-gray-200">AI is ready — resume analysis live</span>
            </div>
            <div className="absolute bottom-6 right-6 z-20 bg-indigo-600/90 backdrop-blur-md rounded-xl px-4 py-3 shadow-xl">
              <div className="text-[10px] text-indigo-200 font-medium">ATS Score</div>
              <div className="text-lg font-extrabold text-white">94%</div>
            </div>
          </div>
        </div>
      </section>

      {/* ══ STATS ══ */}
      <section className="py-14 border-y border-white/5 bg-[#151d30]/30">
        <div className="max-w-5xl mx-auto px-6 grid grid-cols-2 md:grid-cols-4 gap-8 text-center">
          {[
            { value: 10000, suffix: '+', label: 'Job seekers helped' },
            { value: 94, suffix: '%', label: 'ATS pass rate' },
            { value: 3, suffix: '×', label: 'More interview calls' },
            { value: 6, suffix: ' wks', label: 'Avg. time to offer' },
          ].map(({ value, suffix, label }) => (
            <div key={label}>
              <div className="text-3xl font-extrabold bg-gradient-to-r from-indigo-400 to-violet-400 bg-clip-text text-transparent">
                <Counter end={value} suffix={suffix} />
              </div>
              <div className="text-xs text-gray-500 mt-1 font-medium">{label}</div>
            </div>
          ))}
        </div>
      </section>

      {/* ══ FEATURES ══ */}
      <section id="features" className="py-24 px-6">
        <div className="max-w-6xl mx-auto">
          <div className="text-center mb-14">
            <div className="inline-flex items-center gap-2 text-indigo-400 text-xs font-bold uppercase tracking-widest mb-4">
              <Sparkles className="w-3.5 h-3.5" /> Everything you need
            </div>
            <h2 className="text-3xl md:text-4xl font-extrabold tracking-tight mb-4">
              Your AI career team,{' '}
              <span className="bg-gradient-to-r from-indigo-400 to-violet-400 bg-clip-text text-transparent">on demand</span>
            </h2>
            <p className="text-sm text-gray-400 max-w-xl mx-auto">
              Every tool a modern job seeker needs, powered by state-of-the-art AI. No fluff — just results.
            </p>
          </div>
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-5">
            {features.map((f, i) => <FeatureCard key={f.title} {...f} delay={i * 80} />)}
          </div>
        </div>
      </section>

      {/* ══ HOW IT WORKS ══ */}
      <section id="how-it-works" className="py-24 px-6 bg-[#151d30]/20">
        <div className="max-w-5xl mx-auto">
          <div className="text-center mb-14">
            <div className="inline-flex items-center gap-2 text-violet-400 text-xs font-bold uppercase tracking-widest mb-4">
              <Target className="w-3.5 h-3.5" /> Simple process
            </div>
            <h2 className="text-3xl md:text-4xl font-extrabold tracking-tight mb-4">
              From upload to offer in{' '}
              <span className="bg-gradient-to-r from-violet-400 to-cyan-400 bg-clip-text text-transparent">4 steps</span>
            </h2>
          </div>
          <div className="relative grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6">
            <div className="hidden lg:block absolute top-10 left-[12.5%] right-[12.5%] h-px bg-gradient-to-r from-indigo-500/0 via-indigo-500/40 to-indigo-500/0" />
            {steps.map((s, i) => <StepCard key={s.title} {...s} index={i} />)}
          </div>
        </div>
      </section>

      {/* ══ TESTIMONIALS ══ */}
      <section id="testimonials" className="py-24 px-6">
        <div className="max-w-5xl mx-auto">
          <div className="text-center mb-14">
            <div className="inline-flex items-center gap-2 text-cyan-400 text-xs font-bold uppercase tracking-widest mb-4">
              <Users className="w-3.5 h-3.5" /> Success stories
            </div>
            <h2 className="text-3xl md:text-4xl font-extrabold tracking-tight">
              Real people.{' '}
              <span className="bg-gradient-to-r from-cyan-400 to-indigo-400 bg-clip-text text-transparent">Real results.</span>
            </h2>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-5">
            {testimonials.map((t, i) => <TestimonialCard key={t.name} {...t} delay={i * 100} />)}
          </div>
        </div>
      </section>

      {/* ══ CTA BANNER ══ */}
      <section className="py-24 px-6">
        <div className="max-w-4xl mx-auto">
          <div className="relative rounded-3xl overflow-hidden border border-indigo-500/20 bg-gradient-to-br from-indigo-600/10 via-violet-600/10 to-transparent p-12 text-center">
            <div className="absolute inset-0 bg-gradient-to-br from-indigo-600/5 to-violet-600/5 pointer-events-none" />
            <div className="absolute top-[-30%] left-[-10%] w-[50%] h-[120%] rounded-full bg-indigo-500/10 blur-[100px] pointer-events-none" />
            <div className="absolute top-[-30%] right-[-10%] w-[50%] h-[120%] rounded-full bg-violet-500/10 blur-[100px] pointer-events-none" />
            <div className="relative z-10">
              <div className="inline-flex p-3 bg-indigo-500/15 rounded-2xl border border-indigo-500/25 mb-6">
                <Sparkles className="w-7 h-7 text-indigo-400" />
              </div>
              <h2 className="text-3xl md:text-4xl font-extrabold tracking-tight mb-4">
                Ready to transform{' '}
                <span className="bg-gradient-to-r from-indigo-400 via-violet-400 to-cyan-400 bg-clip-text text-transparent">your career?</span>
              </h2>
              <p className="text-sm text-gray-400 mb-8 max-w-lg mx-auto">
                Join thousands of professionals who use CareerOS to get more interviews, ace their rounds, and land the roles they deserve.
              </p>
              <div className="flex flex-col sm:flex-row items-center justify-center gap-4">
                <button id="cta-getstarted-btn" onClick={() => onEnterApp('register')}
                  className="group flex items-center gap-2 bg-gradient-to-r from-indigo-600 to-violet-600 hover:from-indigo-500 hover:to-violet-500 text-white font-bold px-8 py-3.5 rounded-xl text-sm transition-all duration-200 shadow-xl shadow-indigo-500/25 hover:shadow-indigo-500/40 hover:-translate-y-0.5">
                  Create free account <ArrowRight className="w-4 h-4 group-hover:translate-x-0.5 transition-transform" />
                </button>
                <button id="cta-signin-btn" onClick={() => onEnterApp('login')}
                  className="text-sm text-indigo-400 hover:text-indigo-300 font-semibold transition flex items-center gap-1.5">
                  Already have an account? Sign in <ChevronRight className="w-4 h-4" />
                </button>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* ══ FOOTER ══ */}
      <footer className="border-t border-white/5 py-10 px-6">
        <div className="max-w-6xl mx-auto flex flex-col md:flex-row items-center justify-between gap-4">
          <div className="flex items-center gap-2">
            <div className="p-1.5 bg-indigo-500/15 rounded-lg border border-indigo-500/25">
              <Sparkles className="w-4 h-4 text-indigo-400" />
            </div>
            <span className="font-bold text-sm text-white">CareerOS</span>
          </div>
          <p className="text-xs text-gray-600 text-center">© {new Date().getFullYear()} CareerOS · AI Career Intelligence Platform · Built with ❤️</p>
          <div className="flex items-center gap-5 text-xs text-gray-500">
            <a href="#features" className="hover:text-gray-300 transition">Features</a>
            <a href="#how-it-works" className="hover:text-gray-300 transition">How it works</a>
            <button onClick={() => onEnterApp('login')} className="hover:text-gray-300 transition">Sign In</button>
          </div>
        </div>
      </footer>
    </div>
  );
}
