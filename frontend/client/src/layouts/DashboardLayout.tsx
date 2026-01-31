import React from 'react';
import { Outlet, Link, useNavigate } from 'react-router-dom';
import { useAuthStore } from '../store/authStore';
import { LayoutDashboard, Upload, Calendar, LogOut } from 'lucide-react';

const DashboardLayout: React.FC = () => {
    const { logout, user } = useAuthStore();
    const navigate = useNavigate();

    const handleLogout = () => {
        logout();
        navigate('/');
    };

    return (
        <div className="flex h-screen bg-gray-50">
            {/* Sidebar */}
            <div className="w-64 bg-white shadow-md">
                <div className="p-6 border-b">
                    <h1 className="text-xl font-bold text-blue-600">Timetable AI</h1>
                    <p className="text-xs text-gray-500">Welcome, {user?.username}</p>
                </div>
                <nav className="mt-6 px-4 space-y-2">
                    <Link to="/dashboard" className="flex items-center px-4 py-3 text-gray-700 hover:bg-blue-50 hover:text-blue-600 rounded-lg transition-colors">
                        <LayoutDashboard size={20} className="mr-3" />
                        Dashboard
                    </Link>
                    <Link to="/dashboard/upload" className="flex items-center px-4 py-3 text-gray-700 hover:bg-blue-50 hover:text-blue-600 rounded-lg transition-colors">
                        <Upload size={20} className="mr-3" />
                        Data Upload
                    </Link>
                    <Link to="/dashboard/schedule" className="flex items-center px-4 py-3 text-gray-700 hover:bg-blue-50 hover:text-blue-600 rounded-lg transition-colors">
                        <Calendar size={20} className="mr-3" />
                        Schedule
                    </Link>
                </nav>
                <div className="absolute bottom-0 w-64 p-4 border-t">
                    <button onClick={handleLogout} className="flex items-center w-full px-4 py-3 text-red-600 hover:bg-red-50 rounded-lg transition-colors">
                        <LogOut size={20} className="mr-3" />
                        Logout
                    </button>
                </div>
            </div>

            {/* Main Content */}
            <div className="flex-1 overflow-auto">
                <main className="p-8">
                    <Outlet />
                </main>
            </div>
        </div>
    );
};

export default DashboardLayout;
