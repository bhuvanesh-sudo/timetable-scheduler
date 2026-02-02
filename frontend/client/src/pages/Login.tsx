import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuthStore } from '../store/authStore';
import { 
  User, 
  Lock, 
  ArrowRight, 
  ShieldCheck, 
  GraduationCap, 
  Users 
} from 'lucide-react';

const Login = () => {
  const navigate = useNavigate();
  const login = useAuthStore((state) => state.login);
  
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [role, setRole] = useState<'ADMIN' | 'HOD' | 'FACULTY'>('FACULTY');
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState('');

  const handleLogin = (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setIsLoading(true);

    // MOCK AUTHENTICATION LOGIC
    // In a real app, this would be an API call to your Django backend.
    setTimeout(() => {
      if (username && password) {
        // Success! Save user to store
        login('mock-jwt-token-123', { 
            username: username, 
            role: role 
        });
        navigate('/dashboard');
      } else {
        setError('Please enter both username and password.');
        setIsLoading(false);
      }
    }, 800); // Simulate network delay
  };

  // Helper to get role color/icon
  const getRoleBadge = (r: string) => {
    switch(r) {
      case 'ADMIN': return { color: 'bg-rose-100 text-rose-700', icon: <ShieldCheck size={18} /> };
      case 'HOD': return { color: 'bg-purple-100 text-purple-700', icon: <Users size={18} /> };
      default: return { color: 'bg-blue-100 text-blue-700', icon: <GraduationCap size={18} /> };
    }
  };

  return (
    <div className="min-h-screen w-full flex items-center justify-center bg-gradient-to-br from-blue-600 via-indigo-700 to-purple-800 p-4 relative overflow-hidden">
      
      {/* Decorative Background Blobs */}
      <div className="absolute top-0 left-0 w-96 h-96 bg-blue-500 rounded-full mix-blend-multiply filter blur-3xl opacity-30 animate-blob"></div>
      <div className="absolute top-0 right-0 w-96 h-96 bg-purple-500 rounded-full mix-blend-multiply filter blur-3xl opacity-30 animate-blob animation-delay-2000"></div>
      <div className="absolute -bottom-32 left-20 w-96 h-96 bg-pink-500 rounded-full mix-blend-multiply filter blur-3xl opacity-30 animate-blob animation-delay-4000"></div>

      {/* Glassmorphism Card */}
      <div className="w-full max-w-md bg-white/10 backdrop-blur-xl border border-white/20 rounded-2xl shadow-2xl overflow-hidden z-10">
        
        {/* Header */}
        <div className="p-8 text-center border-b border-white/10">
          <div className="w-16 h-16 bg-gradient-to-tr from-blue-400 to-purple-500 rounded-xl mx-auto flex items-center justify-center shadow-lg mb-4">
            <GraduationCap className="text-white w-8 h-8" />
          </div>
          <h2 className="text-3xl font-bold text-white mb-2">Welcome Back</h2>
          <p className="text-blue-100/80">Sign in to manage the academic schedule</p>
        </div>

        {/* Form */}
        <form onSubmit={handleLogin} className="p-8 space-y-6">
          
          {/* Username Input */}
          <div className="space-y-2">
            <label className="text-sm font-medium text-blue-100 ml-1">Username / ID</label>
            <div className="relative group">
              <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                <User className="h-5 w-5 text-blue-200 group-focus-within:text-white transition-colors" />
              </div>
              <input
                type="text"
                value={username}
                onChange={(e) => setUsername(e.target.value)}
                className="w-full pl-10 pr-4 py-3 bg-white/5 border border-white/10 rounded-xl text-white placeholder-blue-200/50 focus:outline-none focus:ring-2 focus:ring-blue-400/50 focus:bg-white/10 transition-all"
                placeholder="e.g. admin_01"
              />
            </div>
          </div>

          {/* Password Input */}
          <div className="space-y-2">
            <label className="text-sm font-medium text-blue-100 ml-1">Password</label>
            <div className="relative group">
              <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                <Lock className="h-5 w-5 text-blue-200 group-focus-within:text-white transition-colors" />
              </div>
              <input
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                className="w-full pl-10 pr-4 py-3 bg-white/5 border border-white/10 rounded-xl text-white placeholder-blue-200/50 focus:outline-none focus:ring-2 focus:ring-blue-400/50 focus:bg-white/10 transition-all"
                placeholder="••••••••"
              />
            </div>
          </div>

          {/* DEV ONLY: Role Selector */}
          <div className="p-4 bg-white/5 rounded-xl border border-white/10">
            <label className="text-xs font-semibold text-blue-200 uppercase tracking-wider mb-3 block">
              Select Role (Dev Mode)
            </label>
            <div className="grid grid-cols-3 gap-2">
              {(['ADMIN', 'HOD', 'FACULTY'] as const).map((r) => {
                 const badge = getRoleBadge(r);
                 const isSelected = role === r;
                 return (
                  <button
                    key={r}
                    type="button"
                    onClick={() => setRole(r)}
                    className={`flex flex-col items-center justify-center p-2 rounded-lg transition-all border ${
                      isSelected 
                      ? 'bg-white text-blue-900 border-white shadow-md scale-105' 
                      : 'bg-transparent text-blue-200 border-transparent hover:bg-white/5'
                    }`}
                  >
                    <div className={`p-1.5 rounded-full mb-1 ${isSelected ? 'bg-blue-100 text-blue-700' : 'bg-white/10'}`}>
                      {badge.icon}
                    </div>
                    <span className="text-[10px] font-bold">{r}</span>
                  </button>
                 );
              })}
            </div>
          </div>

          {/* Error Message */}
          {error && (
            <div className="p-3 rounded-lg bg-red-500/20 border border-red-500/30 text-red-200 text-sm text-center">
              {error}
            </div>
          )}

          {/* Submit Button */}
          <button
            type="submit"
            disabled={isLoading}
            className="w-full flex items-center justify-center py-3.5 px-4 bg-gradient-to-r from-blue-500 to-indigo-500 hover:from-blue-400 hover:to-indigo-400 text-white font-semibold rounded-xl shadow-lg shadow-blue-500/30 hover:shadow-blue-500/40 transform hover:-translate-y-0.5 transition-all disabled:opacity-70 disabled:cursor-not-allowed"
          >
            {isLoading ? (
               <span className="w-5 h-5 border-2 border-white/30 border-t-white rounded-full animate-spin"></span>
            ) : (
               <>
                 Sign In <ArrowRight className="ml-2 w-5 h-5" />
               </>
            )}
          </button>
        </form>

        {/* Footer */}
        <div className="p-4 text-center bg-black/20 border-t border-white/5">
          <p className="text-xs text-blue-200/60">
            University Timetable Scheduler v1.0
          </p>
        </div>
      </div>
    </div>
  );
};

export default Login;