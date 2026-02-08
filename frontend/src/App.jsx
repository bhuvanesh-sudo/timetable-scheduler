/**
 * Main App Component
 * 
 * Author: Frontend Team (Bhuvanesh, Akshitha)
 * Sprint: 1
 */

import { BrowserRouter as Router, Routes, Route, Link, Navigate, useLocation } from 'react-router-dom';
import './index.css';
import Dashboard from './pages/Dashboard';
import DataManagement from './pages/DataManagement';
import GenerateSchedule from './pages/GenerateSchedule';
import ViewTimetable from './pages/ViewTimetable';
import Analytics from './pages/Analytics';
import AuditLogs from './pages/AuditLogs';
import UserManagement from './pages/UserManagement';
import Login from './pages/Login';
import { AuthProvider, useAuth } from './context/AuthContext';
import ProtectedRoute from './components/ProtectedRoute';

// Layout component for authenticated pages
const MainLayout = ({ children }) => {
  const { user, logout } = useAuth();

  return (
    <div className="app-container">
      {/* Sidebar Navigation */}
      <aside className="sidebar">
        <div className="sidebar-header">
          <h1 className="sidebar-title">M3 Timetable</h1>
          <p className="sidebar-subtitle">Automated Scheduling System</p>
        </div>

        <div className="user-info" style={{ padding: '0 1.5rem', marginBottom: '1rem', color: 'var(--text-secondary)', fontSize: '0.875rem' }}>
          Welcome, {user?.username} ({user?.role})
        </div>

        <nav>
          <ul className="nav-menu">
            <li className="nav-item">
              <Link to="/dashboard" className="nav-link">
                📊 Dashboard
              </Link>
            </li>
            {(user?.role === 'ADMIN' || user?.role === 'HOD') && (
              <li className="nav-item">
                <Link to="/data" className="nav-link">
                  📁 Data Management
                </Link>
              </li>
            )}
            {(user?.role === 'ADMIN' || user?.role === 'HOD') && (
              <li className="nav-item">
                <Link to="/generate" className="nav-link">
                  ⚙️ Generate Schedule
                </Link>
              </li>
            )}
            <li className="nav-item">
              <Link to="/timetable" className="nav-link">
                📅 View Timetable
              </Link>
            </li>
            <li className="nav-item">
              <Link to="/analytics" className="nav-link">
                📈 Analytics
              </Link>
            </li>
            {user?.role === 'ADMIN' && (
              <li className="nav-item">
                <Link to="/users" className="nav-link">
                  👥 Users
                </Link>
              </li>
            )}
            {(user?.role === 'ADMIN' || user?.role === 'HOD') && (
              <li className="nav-item">
                <Link to="/audit-logs" className="nav-link">
                  📋 Audit Logs
                </Link>
              </li>
            )}
            <li className="nav-item" style={{ marginTop: '2rem' }}>
              <button onClick={logout} className="nav-link" style={{ width: '100%', textAlign: 'left', background: 'none', border: 'none', cursor: 'pointer', color: 'var(--danger)' }}>
                🚪 Logout
              </button>
            </li>
          </ul>
        </nav>
      </aside>

      {/* Main Content Area */}
      <main className="main-content">
        {children}
      </main>
    </div>
  );
};

function App() {
  return (
    <Router>
      <AuthProvider>
        <Routes>
          <Route path="/login" element={<Login />} />

          {/* Protected Routes */}
          <Route path="/" element={
            <ProtectedRoute>
              <Navigate to="/dashboard" replace />
            </ProtectedRoute>
          } />

          <Route path="/dashboard" element={
            <ProtectedRoute>
              <MainLayout><Dashboard /></MainLayout>
            </ProtectedRoute>
          } />

          <Route path="/data" element={
            <ProtectedRoute roles={['ADMIN', 'HOD']}>
              <MainLayout><DataManagement /></MainLayout>
            </ProtectedRoute>
          } />

          <Route path="/generate" element={
            <ProtectedRoute roles={['ADMIN', 'HOD']}>
              <MainLayout><GenerateSchedule /></MainLayout>
            </ProtectedRoute>
          } />

          <Route path="/timetable" element={
            <ProtectedRoute>
              <MainLayout><ViewTimetable /></MainLayout>
            </ProtectedRoute>
          } />

          <Route path="/analytics" element={
            <ProtectedRoute>
              <MainLayout><Analytics /></MainLayout>
            </ProtectedRoute>
          } />

          <Route path="/users" element={
            <ProtectedRoute roles={['ADMIN']}>
              <MainLayout><UserManagement /></MainLayout>
            </ProtectedRoute>
          } />

          <Route path="/audit-logs" element={
            <ProtectedRoute roles={['ADMIN', 'HOD']}>
              <MainLayout><AuditLogs /></MainLayout>
            </ProtectedRoute>
          } />

          {/* Catch all - redirect to dashboard if logged in, else login */}
          <Route path="*" element={<Navigate to="/dashboard" replace />} />
        </Routes>
      </AuthProvider>
    </Router>
  );
}

export default App;
