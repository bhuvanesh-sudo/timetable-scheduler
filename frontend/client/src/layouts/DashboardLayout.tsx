import { Outlet, Link, useLocation } from 'react-router-dom';
import { useAuthStore } from '../store/authStore';
import { NAV_ITEMS } from '../config/navigation';
import { 
  LogOut, 
  Menu, 
  ChevronsLeft,
  Search,
  Bell,
  Hexagon
} from 'lucide-react';
import { useState } from 'react';

const DashboardLayout = () => {
  const { user, logout } = useAuthStore();
  const location = useLocation();
  const [isSidebarOpen, setSidebarOpen] = useState(true);

  const userRole = user?.role || 'FACULTY';
  const username = user?.username || 'Guest';

  return (
    <div className="flex h-screen bg-[#FDFDFD] overflow-hidden selection:bg-slate-900 selection:text-white">
      
      {/* 1. ANIMATED SIDEBAR */}
      <aside 
        className={`
          relative z-20 bg-white border-r border-slate-100 flex flex-col 
          transition-[width] duration-500 cubic-bezier(0.25, 1, 0.5, 1)
          ${isSidebarOpen ? 'w-72' : 'w-20'}
        `}
      >
        {/* Logo Section */}
        <div className="h-16 flex items-center justify-center border-b border-slate-50">
          <div className={`flex items-center gap-3 transition-all duration-300 ${!isSidebarOpen && 'scale-0 opacity-0 absolute'}`}>
            <div className="w-8 h-8 bg-slate-900 text-white rounded-lg flex items-center justify-center">
              <Hexagon size={18} strokeWidth={3} />
            </div>
            <span className="font-bold text-lg tracking-tight text-slate-900">Timetable.AI</span>
          </div>
          {/* Collapsed Logo */}
          {!isSidebarOpen && (
             <div className="w-8 h-8 bg-slate-900 text-white rounded-lg flex items-center justify-center animate-fade-in">
               <Hexagon size={18} strokeWidth={3} />
             </div>
          )}
        </div>

        {/* Navigation Items */}
        <nav className="flex-1 py-6 px-3 space-y-1 overflow-y-auto overflow-x-hidden custom-scrollbar">
          <div className={`px-3 mb-2 text-[10px] font-bold text-slate-400 uppercase tracking-widest transition-opacity duration-300 ${!isSidebarOpen && 'opacity-0 hidden'}`}>
            Main Menu
          </div>
          
          {NAV_ITEMS.map((item) => {
             if (!item.roles.includes(userRole as any) && userRole !== 'ADMIN') return null;
             const isActive = location.pathname === item.path;

             return (
              <Link
                key={item.path}
                to={item.path}
                className={`
                  group relative flex items-center px-3 py-2.5 rounded-lg mb-1
                  transition-all duration-200 ease-out
                  ${isActive 
                    ? 'bg-slate-50 text-slate-900 shadow-sm ring-1 ring-slate-200' 
                    : 'text-slate-500 hover:bg-white hover:text-slate-900 hover:shadow-sm hover:ring-1 hover:ring-slate-100'
                  }
                `}
              >
                {/* Active Indicator Line */}
                {isActive && (
                  <div className="absolute left-0 top-1/2 -translate-y-1/2 w-1 h-8 bg-slate-900 rounded-r-full" />
                )}

                <span className={`transition-transform duration-300 group-hover:scale-110 ${isActive ? 'text-slate-900' : 'text-slate-400 group-hover:text-slate-700'}`}>
                  {item.icon}
                </span>
                
                <span className={`
                  ml-3 font-medium text-sm whitespace-nowrap transition-all duration-300 origin-left
                  ${!isSidebarOpen ? 'opacity-0 translate-x-4 overflow-hidden w-0' : 'opacity-100 translate-x-0 w-auto'}
                `}>
                  {item.label}
                </span>

                {/* Floating Tooltip (Collapsed Mode) */}
                {!isSidebarOpen && (
                  <div className="absolute left-full ml-4 px-2 py-1 bg-slate-900 text-white text-xs rounded opacity-0 -translate-x-2 group-hover:opacity-100 group-hover:translate-x-0 transition-all duration-200 pointer-events-none z-50 shadow-xl">
                    {item.label}
                  </div>
                )}
              </Link>
            );
          })}
        </nav>

        {/* User Profile Footer */}
        <div className="p-4 border-t border-slate-50">
          <button 
            onClick={logout}
            className={`
              flex items-center w-full p-2 rounded-lg 
              text-slate-500 hover:bg-rose-50 hover:text-rose-600 
              transition-all duration-200 group
              ${!isSidebarOpen && 'justify-center'}
            `}
          >
            <LogOut size={20} className="transition-transform group-hover:-translate-x-1" />
            
            <div className={`ml-3 text-left transition-all duration-300 ${!isSidebarOpen && 'w-0 opacity-0 overflow-hidden'}`}>
              <p className="text-xs font-bold text-slate-900">Sign Out</p>
              <p className="text-[10px] text-slate-400">End session</p>
            </div>
          </button>
        </div>
      </aside>

      {/* 2. MAIN CONTENT AREA */}
      <main className="flex-1 flex flex-col min-w-0 bg-[#FDFDFD]">
        
        {/* Sticky Glassmorphism Header */}
        <header className="h-16 sticky top-0 z-10 bg-white/80 backdrop-blur-md border-b border-slate-100 flex items-center justify-between px-6 transition-all duration-300">
           
           {/* Left: Sidebar Toggle & Breadcrumbs */}
           <div className="flex items-center gap-4">
             <button 
               onClick={() => setSidebarOpen(!isSidebarOpen)}
               className="p-2 text-slate-400 hover:text-slate-900 hover:bg-slate-100 rounded-lg transition-all duration-200 active:scale-95"
             >
               {isSidebarOpen ? <ChevronsLeft size={20} /> : <Menu size={20} />}
             </button>
             
             {/* Search Bar (Fake) */}
             <div className="hidden md:flex items-center relative group">
                <Search size={14} className="absolute left-3 text-slate-400 group-focus-within:text-slate-600 transition-colors" />
                <input 
                  type="text" 
                  placeholder="Quick Search..." 
                  className="pl-9 pr-4 py-1.5 bg-slate-50 border-none rounded-full text-sm text-slate-700 placeholder-slate-400 focus:ring-2 focus:ring-slate-100 focus:bg-white transition-all w-64"
                />
             </div>
           </div>

           {/* Right: Actions & Profile */}
           <div className="flex items-center space-x-4">
             {/* Notification Bell */}
             <button className="relative p-2 text-slate-400 hover:text-slate-900 transition-colors">
               <Bell size={20} />
               <span className="absolute top-2 right-2 w-2 h-2 bg-rose-500 rounded-full ring-2 ring-white animate-pulse"></span>
             </button>

             <div className="h-6 w-px bg-slate-200 mx-2"></div>

             {/* Minimal Profile Pill */}
             <div className="flex items-center gap-3 pl-2">
               <div className="text-right hidden sm:block">
                 <div className="text-xs font-bold text-slate-900">{username}</div>
                 <div className="text-[10px] text-slate-400 font-medium tracking-wide uppercase">{userRole}</div>
               </div>
               <div className="w-9 h-9 rounded-full bg-linear-to-tr from-slate-800 to-slate-600 text-white flex items-center justify-center font-bold text-sm shadow-md ring-2 ring-white">
                 {userRole[0]}
               </div>
             </div>
           </div>
        </header>

        {/* 3. SCROLLABLE PAGE CONTENT */}
        <section className="flex-1 overflow-y-auto p-6 md:p-8 scroll-smooth">
          <div className="max-w-7xl mx-auto animate-slide-up">
            <Outlet />
          </div>
        </section>
      </main>
    </div>
  );
};

export default DashboardLayout;