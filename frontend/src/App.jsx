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
import ChangeRequests from './pages/ChangeRequests';
import TeacherRequests from './pages/TeacherRequests';
import SystemHealth from './pages/SystemHealth';
import Login from './pages/Login';
import { AuthProvider, useAuth } from './context/AuthContext';
import { ThemeProvider, useTheme } from './context/ThemeContext';
import ProtectedRoute from './components/ProtectedRoute';

// Layout component for authenticated pages
const MainLayout = ({ children }) => {
  const { user, logout } = useAuth();
  const { theme, toggleTheme } = useTheme();

  return (
    <div className="app-container">
      {/* Sidebar Navigation */}
      <aside className="sidebar">
        <div className="sidebar-header">
          <h1 className="sidebar-title">M3</h1>
          <p className="sidebar-subtitle">Timetable System</p>
        </div>

        <nav>
          <ul className="nav-menu">
            <li className="nav-item">
              <Link to="/dashboard" className="nav-link">
                Dashboard
              </Link>
            </li>

            {/* Admin: Full Access */}
            {user?.role === 'ADMIN' && (
              <>
                <li className="nav-item">
                  <Link to="/data" className="nav-link">
                    Data Management
                  </Link>
                </li>
                <li className="nav-item">
                  <Link to="/generate" className="nav-link">
                    Generate Schedule
                  </Link>
                </li>
                <li className="nav-item">
                  <Link to="/timetable" className="nav-link">
                    View Timetable
                  </Link>
                </li>
                <li className="nav-item">
                  <Link to="/analytics" className="nav-link">
                    Analytics
                  </Link>
                </li>
                <li className="nav-item">
                  <Link to="/users" className="nav-link">
                    Users
                  </Link>
                </li>
                <li className="nav-item">
                  <Link to="/change-requests" className="nav-link">
                    Change Requests
                  </Link>
                </li>
                <li className="nav-item">
                  <Link to="/audit-logs" className="nav-link">
                    Audit Logs
                  </Link>
                </li>
                <li className="nav-item">
                  <Link to="/system-health" className="nav-link">
                    System Health
                  </Link>
                </li>
              </>
            )}

            {/* HOD: Limited Access */}
            {user?.role === 'HOD' && (
              <>
                <li className="nav-item">
                  <Link to="/teacher-requests" className="nav-link">
                    Teacher Requests
                  </Link>
                </li>
                <li className="nav-item">
                  <Link to="/timetable" className="nav-link">
                    View Timetable
                  </Link>
                </li>
                <li className="nav-item">
                  <Link to="/analytics" className="nav-link">
                    Analytics
                  </Link>
                </li>
              </>
            )}

            {/* Faculty: View Only */}
            {user?.role === 'FACULTY' && (
              <li className="nav-item">
                <Link to="/timetable" className="nav-link">
                  View Timetable
                </Link>
              </li>
            )}

            <li className="nav-item" style={{ marginTop: 'auto' }}>
              <button
                onClick={logout}
                className="nav-link"
                style={{
                  width: '100%',
                  textAlign: 'left',
                  background: 'none',
                  border: 'none',
                  cursor: 'pointer',
                  color: 'var(--danger)',
                  marginTop: '2rem'
                }}
              >
                Logout
              </button>
            </li>
          </ul>
        </nav>
      </aside>

      {/* Main Content Area */}
      <main className="main-content">
        <header className="top-bar">
          <div style={{ textAlign: 'right' }}>
            <div className="user-welcome">
              Welcome, {user?.username} ({user?.role})
            </div>
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'flex-end', gap: '8px', marginTop: '4px' }}>
              <span style={{ fontSize: '0.8rem', fontWeight: 600, color: 'var(--text-muted)' }}>
                {theme === 'light' ? 'Light' : 'Dark'}
              </span>
              <label className="theme-switch">
                <input
                  type="checkbox"
                  checked={theme === 'dark'}
                  onChange={toggleTheme}
                />
                <span className="slider">
                  <span className="icon">☀️</span>
                  <span className="icon">🌙</span>
                </span>
              </label>
            </div>
          </div>
        </header>

        <div className="fade-in">
          {children}
        </div>
      </main>
    </div>
  );
};

function App() {
  return (
    <Router>
      <ThemeProvider>
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
              <ProtectedRoute roles={['ADMIN']}>
                <MainLayout><DataManagement /></MainLayout>
              </ProtectedRoute>
            } />

            <Route path="/generate" element={
              <ProtectedRoute roles={['ADMIN']}>
                <MainLayout><GenerateSchedule /></MainLayout>
              </ProtectedRoute>
            } />

            <Route path="/timetable" element={
              <ProtectedRoute>
                <MainLayout><ViewTimetable /></MainLayout>
              </ProtectedRoute>
            } />

            <Route path="/analytics" element={
              <ProtectedRoute roles={['ADMIN', 'HOD']}>
                <MainLayout><Analytics /></MainLayout>
              </ProtectedRoute>
            } />

            <Route path="/users" element={
              <ProtectedRoute roles={['ADMIN']}>
                <MainLayout><UserManagement /></MainLayout>
              </ProtectedRoute>
            } />

            <Route path="/change-requests" element={
              <ProtectedRoute roles={['ADMIN']}>
                <MainLayout><ChangeRequests /></MainLayout>
              </ProtectedRoute>
            } />

            <Route path="/teacher-requests" element={
              <ProtectedRoute roles={['HOD']}>
                <MainLayout><TeacherRequests /></MainLayout>
              </ProtectedRoute>
            } />

            <Route path="/audit-logs" element={
              <ProtectedRoute roles={['ADMIN']}>
                <MainLayout><AuditLogs /></MainLayout>
              </ProtectedRoute>
            } />

            <Route path="/system-health" element={
              <ProtectedRoute roles={['ADMIN']}>
                <MainLayout><SystemHealth /></MainLayout>
              </ProtectedRoute>
            } />

            {/* Catch all - redirect to dashboard if logged in, else login */}
            <Route path="*" element={<Navigate to="/dashboard" replace />} />
          </Routes>
        </AuthProvider>
      </ThemeProvider>
    </Router>
  );
}

export default App;
