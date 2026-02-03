import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuthStore } from '../store/authStore';
import { ArrowRight, Lock, User, Hexagon } from 'lucide-react';

const Login = () => {
  const navigate = useNavigate();
  const login = useAuthStore((state) => state.login);
  
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [role, setRole] = useState<'ADMIN' | 'HOD' | 'FACULTY'>('FACULTY');
  const [isLoading, setIsLoading] = useState(false);

  const handleLogin = (e: React.FormEvent) => {
    e.preventDefault();
    setIsLoading(true);
    // Simulation
    setTimeout(() => {
        login('mock-token', { username, role });
        navigate('/dashboard');
    }, 600);
  };

  return (
    <div className="min-h-screen w-full flex bg-[#F9FAFB]">
      
      {/* Left Column: The Form */}
      <div className="w-full lg:w-1/2 flex flex-col justify-center items-center p-8 lg:p-24 border-r border-gray-100 bg-white">
        <div className="w-full max-w-sm space-y-8">
          
          {/* Logo / Brand */}
          <div className="flex items-center space-x-2 mb-10">
            <div className="w-8 h-8 bg-slate-900 rounded flex items-center justify-center text-white">
              <Hexagon size={20} strokeWidth={5} />
            </div>
            <span className="text-lg font-bold text-slate-900 tracking-tight">Timetable.AI</span>
          </div>

          {/* Header */}
          <div className="space-y-2">
            <h1 className="text-3xl font-semibold text-slate-900 tracking-tight">Welcome</h1>
            <p className="text-slate-500 text-sm">Please enter your details to sign in.</p>
          </div>

          {/* Form */}
          <form onSubmit={handleLogin} className="space-y-6">
            <div className="space-y-4">
              
              {/* Username */}
              <div className="space-y-1">
                <label className="text-xs font-medium text-slate-700 uppercase tracking-wide">Username</label>
                <div className="relative">
                  <User className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" size={18} />
                  <input
                    type="text"
                    value={username}
                    onChange={(e) => setUsername(e.target.value)}
                    className="w-full pl-10 pr-4 py-3 bg-white border border-slate-200 rounded-lg text-slate-900 placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-slate-900 focus:border-transparent transition-all shadow-sm"
                    placeholder="Enter your ID"
                  />
                </div>
              </div>

              {/* Password */}
              <div className="space-y-1">
                <label className="text-xs font-medium text-slate-700 uppercase tracking-wide">Password</label>
                <div className="relative">
                  <Lock className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" size={18} />
                  <input
                    type="password"
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    className="w-full pl-10 pr-4 py-3 bg-white border border-slate-200 rounded-lg text-slate-900 placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-slate-900 focus:border-transparent transition-all shadow-sm"
                    placeholder="••••••••"
                  />
                </div>
              </div>

              {/* Role Switcher (Minimal) */}
              <div className="pt-2">
                <label className="text-[10px] font-semibold text-slate-400 uppercase tracking-wider mb-2 block">
                  Select Context
                </label>
                <div className="flex bg-slate-50 p-1 rounded-lg border border-slate-100">
                  {['ADMIN', 'HOD', 'FACULTY'].map((r) => (
                    <button
                      key={r}
                      type="button"
                      onClick={() => setRole(r as any)}
                      className={`flex-1 py-1.5 text-xs font-medium rounded-md transition-all ${
                        role === r 
                        ? 'bg-white text-slate-900 shadow-sm border border-slate-200' 
                        : 'text-slate-500 hover:text-slate-700'
                      }`}
                    >
                      {r}
                    </button>
                  ))}
                </div>
              </div>
            </div>

            <button
              type="submit"
              disabled={isLoading}
              className="w-full flex items-center justify-center py-3 bg-slate-900 text-white font-medium rounded-lg hover:bg-slate-800 transition-colors disabled:opacity-70"
            >
              {isLoading ? 'Signing in...' : 'Sign In'}
              {!isLoading && <ArrowRight size={18} className="ml-2" />}
            </button>
          </form>

          <p className="text-center text-xs text-slate-400 mt-8">
            © 2026 University Scheduler System
          </p>
        </div>
      </div>

      {/* Right Column: Visual / Context */}
      <div className="hidden lg:flex w-1/2 bg-slate-50 relative overflow-hidden items-center justify-center border-l border-slate-200">
        <div className="absolute inset-0 bg-[radial-gradient(#e2e8f0_1px,transparent_1px)] [bg-size:16px_16px] opacity-50"></div>
        
        <div className="relative z-10 max-w-md text-center p-12">
           <div className="mb-8 flex justify-center">
             <div className="p-4 bg-white rounded-2xl shadow-sm border border-slate-100 rotate-3">
                <div className="w-32 h-20 bg-slate-100 rounded-lg flex flex-col gap-2 p-2">
                   <div className="h-2 w-2/3 bg-slate-300 rounded"></div>
                   <div className="h-2 w-full bg-slate-200 rounded"></div>
                   <div className="h-2 w-full bg-slate-200 rounded"></div>
                </div>
             </div>
             <div className="p-4 bg-white rounded-2xl shadow-lg border border-slate-200 -ml-8 -mt-8 z-20">
                <div className="w-32 h-20 bg-slate-50 rounded-lg flex flex-col gap-2 p-2 border border-slate-100">
                   <div className="flex justify-between">
                     <div className="h-2 w-10 bg-blue-500 rounded"></div>
                     <div className="h-2 w-4 bg-slate-200 rounded"></div>
                   </div>
                   <div className="h-10 w-full bg-blue-50/50 rounded border border-blue-100 mt-1"></div>
                </div>
             </div>
           </div>
           
           <h2 className="text-2xl font-bold text-slate-900 mb-3">Constraint-Aware Scheduling</h2>
           <p className="text-slate-500 leading-relaxed">
             An intelligent platform designed to autonomize conflict-free institutional timetables ensuring workload fairness and policy compliance.
           </p>
        </div>
      </div>

    </div>
  );
};

export default Login;