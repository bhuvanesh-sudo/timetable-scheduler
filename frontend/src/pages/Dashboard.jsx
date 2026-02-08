/**
 * Dashboard Page - Overview of the system
 * 
 * Routes to specific dashboard views based on user role.
 * 
 * Author: Frontend Team (Bhuvanesh, Akshitha)
 */

import { useAuth } from '../context/AuthContext';
import AdminDashboard from './dashboards/AdminDashboard';
import HODDashboard from './dashboards/HODDashboard';
import FacultyDashboard from './dashboards/FacultyDashboard';

function Dashboard() {
    const { user } = useAuth();

    // Fallback for loading or undefined user
    if (!user) {
        return <div className="loading-spinner">Loading dashboard...</div>;
    }

    // Role-based routing
    switch (user.role) {
        case 'ADMIN':
            return <AdminDashboard />;
        case 'HOD':
            return <HODDashboard />;
        case 'FACULTY':
            return <FacultyDashboard />;
        default:
            // Fallback for unknown roles
            return (
                <div className="card">
                    <h2>Welcome, {user.username}</h2>
                    <p>Your role ({user.role}) does not have a specific dashboard view configured.</p>
                </div>
            );
    }
}

export default Dashboard;
