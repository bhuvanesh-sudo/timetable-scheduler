import { Outlet, Link, useLocation } from 'react-router-dom';
import { useAuthStore } from '../store/authStore';
import { NAV_ITEMS } from '../config/navigation';
import { LogOut, Menu, UserCircle } from 'lucide-react';
import { useState } from 'react';

const DashboardLayout = () => {
  const { user, logout } = useAuthStore();
  const location = useLocation();
  const [isSidebarOpen, setSidebarOpen] = useState(true);

  // Fallback for safety, though user should always exist in protected routes
  const userRole = user?.role || 'FACULTY';
  const username = user?.username || 'Guest';

  return (
    <div className="flex h-screen bg-gray-50 overflow-hidden">
      {/* Sidebar */}
      <aside 
        className={`${isSidebarOpen ? 'w-64' : 'w-20'} bg-white border-r border-gray-200 flex flex-col transition-all duration-300 ease-in-out shadow-sm z-10`}
      >
        <div className="h-16 flex items-center justify-center border-b border-gray-100">
          <h1 className={`font-bold text-blue-600 transition-all ${isSidebarOpen ? 'text-xl' : 'text-xs'}`}>
            {isSidebarOpen ? 'Scheduler AI' : 'AI'}
          </h1>
        </div>

        <nav className="flex-1 py-6 space-y-1 px-3">
          {NAV_ITEMS.map((item) => {
             // RBAC Check: Only show items allowed for this role
             if (!item.roles.includes(userRole as any) && userRole !== 'ADMIN') return null;

             const isActive = location.pathname === item.path;
             return (
              <Link
                key={item.path}
                to={item.path}
                className={`flex items-center px-3 py-3 rounded-lg transition-colors group relative ${
                  isActive 
                  ? 'bg-blue-50 text-blue-700' 
                  : 'text-gray-500 hover:bg-gray-100 hover:text-gray-900'
                }`}
              >
                <span className={`${isActive ? 'text-blue-600' : 'text-gray-400 group-hover:text-gray-600'}`}>
                  {item.icon}
                </span>
                
                {isSidebarOpen && (
                  <span className="ml-3 font-medium text-sm">{item.label}</span>
                )}

                {/* Tooltip for collapsed state */}
                {!isSidebarOpen && (
                  <div className="absolute left-full ml-2 px-2 py-1 bg-gray-800 text-white text-xs rounded opacity-0 group-hover:opacity-100 whitespace-nowrap z-50 pointer-events-none">
                    {item.label}
                  </div>
                )}
              </Link>
            );
          })}
        </nav>

        <div className="p-4 border-t border-gray-100">
          <button 
            onClick={logout}
            className={`flex items-center w-full px-3 py-2 text-red-600 hover:bg-red-50 rounded-lg transition-colors ${!isSidebarOpen && 'justify-center'}`}
          >
            <LogOut size={20} />
            {isSidebarOpen && <span className="ml-3 text-sm font-medium">Sign Out</span>}
          </button>
        </div>
      </aside>

      {/* Main Content */}
      <main className="flex-1 flex flex-col min-w-0">
        {/* Top Header */}
        <header className="h-16 bg-white border-b border-gray-200 flex items-center justify-between px-6 shadow-sm">
           <button 
             onClick={() => setSidebarOpen(!isSidebarOpen)}
             className="p-2 text-gray-500 hover:bg-gray-100 rounded-lg"
           >
             <Menu size={20} />
           </button>

           <div className="flex items-center space-x-6">
             {/* System Status Indicator */}
             <div className="hidden md:flex items-center space-x-2 bg-green-50 px-3 py-1 rounded-full border border-green-100">
               <div className="w-2 h-2 bg-green-500 rounded-full animate-pulse"></div>
               <span className="text-xs font-semibold text-green-700">System Online</span>
             </div>

             {/* User Profile - Corrected to use only Username/Role */}
             <div className="flex items-center space-x-3 border-l pl-6 border-gray-200">
               <div className="text-right hidden sm:block">
                 <div className="text-sm font-bold text-gray-800">
                   {username}
                 </div>
                 <div className="text-xs text-blue-600 font-semibold bg-blue-50 px-2 py-0.5 rounded inline-block mt-0.5">
                   {userRole}
                 </div>
               </div>
               
               {/* Avatar Fallback */}
               <div className="w-9 h-9 rounded-lg bg-gray-100 text-gray-600 flex items-center justify-center shadow-sm border border-gray-200">
                 <UserCircle size={20} />
               </div>
             </div>
           </div>
        </header>

        {/* Scrollable Page Content */}
        <section className="flex-1 overflow-y-auto bg-gray-50 p-6">
          <div className="max-w-7xl mx-auto">
            <Outlet />
          </div>
        </section>
      </main>
    </div>
  );
};

export default DashboardLayout;