/**
 * Admin Dashboard
 * 
 * Overview for System Administrators
 */

import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { scheduleAPI, teacherAPI, courseAPI, roomAPI, sectionAPI, systemAPI } from '../../services/api';

function AdminDashboard() {
    const [stats, setStats] = useState({
        teachers: 0,
        courses: 0,
        rooms: 0,
        sections: 0,
        schedules: 0,
    });
    const [loading, setLoading] = useState(true);
    const [showResetModal, setShowResetModal] = useState(false);
    const [confirmText, setConfirmText] = useState('');
    const [resetting, setResetting] = useState(false);

    useEffect(() => {
        loadStats();
    }, []);

    const loadStats = async () => {
        try {
            const [teachers, courses, rooms, sections, schedules] = await Promise.all([
                teacherAPI.getAll(),
                courseAPI.getAll(),
                roomAPI.getAll(),
                sectionAPI.getAll(),
                scheduleAPI.getAll(),
            ]);

            setStats({
                teachers: teachers.data.results?.length || teachers.data.length || 0,
                courses: courses.data.results?.length || courses.data.length || 0,
                rooms: rooms.data.results?.length || rooms.data.length || 0,
                sections: sections.data.results?.length || sections.data.length || 0,
                schedules: schedules.data.results?.length || schedules.data.length || 0,
            });
        } catch (error) {
            console.error('Error loading stats:', error);
        } finally {
            setLoading(false);
        }
    };

    if (loading) return <div className="loading-spinner">Loading dashboard...</div>;


    const handleResetSemester = async () => {
        if (confirmText !== 'CONFIRM') return;

        setResetting(true);
        try {
            await systemAPI.resetSemester({ confirmation: 'CONFIRM' });
            alert('Semester reset successful! All schedules and mappings have been cleared.');
            setShowResetModal(false);
            setConfirmText('');
            loadStats(); // Refresh stats
        } catch (error) {
            console.error('Reset failed:', error);
            alert('Failed to reset semester: ' + (error.response?.data?.error || error.message));
        } finally {
            setResetting(false);
        }
    };

    return (
        <div className="admin-dashboard fade-in">
            <div className="page-header fade-in">
                <h1 className="page-title">System Admin Dashboard</h1>
                <p className="page-description">Manage system health, data, and schedules.</p>
            </div>

            <div className="stats-grid fade-in">
                <div className="stat-card">
                    <div className="stat-label">Total Teachers</div>
                    <div className="stat-value">{stats.teachers}</div>
                </div>
                <div className="stat-card">
                    <div className="stat-label">Total Courses</div>
                    <div className="stat-value">{stats.courses}</div>
                </div>
                <div className="stat-card">
                    <div className="stat-label">Total Rooms</div>
                    <div className="stat-value">{stats.rooms}</div>
                </div>
                <div className="stat-card">
                    <div className="stat-label">Total Sections</div>
                    <div className="stat-value">{stats.sections}</div>
                </div>
                <div className="stat-card">
                    <div className="stat-label">Generated Schedules</div>
                    <div className="stat-value">{stats.schedules}</div>
                </div>
            </div>

            <div className="actions-section" style={{ marginTop: '2rem' }}>
                <h2 style={{ fontSize: '1.25rem', marginBottom: '1rem', color: 'var(--text-primary)' }}>Quick Actions</h2>
                <div className="actions-grid" style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '1rem' }}>
                    <Link to="/data" className="action-card">
                        <h3 style={{ margin: '0 0 0.5rem 0', color: 'var(--primary)' }}>Data Management</h3>
                        <p style={{ margin: 0, fontSize: '0.9rem', color: 'var(--text-secondary)' }}>Manage teachers, courses, rooms, and sections.</p>
                    </Link>
                    <Link to="/generate" className="action-card">
                        <h3 style={{ margin: '0 0 0.5rem 0', color: 'var(--primary)' }}>Generate Schedule</h3>
                        <p style={{ margin: 0, fontSize: '0.9rem', color: 'var(--text-secondary)' }}>Run the scheduling algorithm.</p>
                    </Link>
                    <Link to="/users" className="action-card">
                        <h3 style={{ margin: '0 0 0.5rem 0', color: 'var(--primary)' }}>User Management</h3>
                        <p style={{ margin: 0, fontSize: '0.9rem', color: 'var(--text-secondary)' }}>Manage system access and roles.</p>
                    </Link>
                    <Link to="/audit-logs" className="action-card">
                        <h3 style={{ margin: '0 0 0.5rem 0', color: 'var(--primary)' }}>Audit Logs</h3>
                        <p style={{ margin: 0, fontSize: '0.9rem', color: 'var(--text-secondary)' }}>View system activity and history.</p>
                    </Link>
                    <Link to="/analytics" className="action-card">
                        <h3 style={{ margin: '0 0 0.5rem 0', color: 'var(--primary)' }}>Analytics</h3>
                        <p style={{ margin: 0, fontSize: '0.9rem', color: 'var(--text-secondary)' }}>View workload and utilization stats.</p>
                    </Link>
                    <Link to="/change-requests" className="action-card">
                        <h3 style={{ margin: '0 0 0.5rem 0', color: 'var(--primary)' }}>Change Requests</h3>
                        <p style={{ margin: 0, fontSize: '0.9rem', color: 'var(--text-secondary)' }}>Review requests from HODs.</p>
                    </Link>
                </div>
            </div>

            <div className="danger-zone" style={{ marginTop: '3rem', padding: '1.5rem', border: '1px solid #fee2e2', borderRadius: '8px', backgroundColor: '#fef2f2' }}>
                <h2 style={{ color: '#dc2626', fontSize: '1.25rem', marginTop: 0 }}>System Administration</h2>
                <p style={{ color: '#7f1d1d', marginBottom: '1rem' }}>Critical actions for system maintenance.</p>
                <button
                    onClick={() => setShowResetModal(true)}
                    style={{
                        backgroundColor: '#dc2626',
                        color: 'white',
                        padding: '0.75rem 1.5rem',
                        border: 'none',
                        borderRadius: '4px',
                        cursor: 'pointer',
                        fontWeight: '600'
                    }}
                >
                    End Semester & Reset
                </button>
            </div>

            {/* Reset Modal */}
            {showResetModal && (
                <div style={{
                    position: 'fixed',
                    top: 0,
                    left: 0,
                    right: 0,
                    bottom: 0,
                    backgroundColor: 'rgba(0,0,0,0.5)',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    zIndex: 1000
                }}>
                    <div style={{
                        backgroundColor: 'white',
                        padding: '2rem',
                        borderRadius: '8px',
                        maxWidth: '500px',
                        width: '90%'
                    }}>
                        <h3 style={{ color: '#dc2626', marginTop: 0 }}>⚠️ End Semester Rollover</h3>
                        <p>This action will <strong>PERMANENTLY DELETE</strong>:</p>
                        <ul style={{ color: '#4b5563' }}>
                            <li>All Generated Schedules</li>
                            <li>All Teacher-Course Assignments</li>
                            <li>Conflict Logs</li>
                        </ul>
                        <p style={{ fontSize: '0.9rem', color: '#6b7280' }}>
                            Teachers, Courses, Rooms, Sections, and User accounts will be <strong>preserved</strong>.<br />
                            A backup will be created automatically before deletion.
                        </p>

                        <div style={{ marginTop: '1.5rem' }}>
                            <label style={{ display: 'block', marginBottom: '0.5rem', fontWeight: '500' }}>
                                Type "CONFIRM" to proceed:
                            </label>
                            <input
                                type="text"
                                value={confirmText}
                                onChange={(e) => setConfirmText(e.target.value)}
                                placeholder="CONFIRM"
                                style={{
                                    width: '100%',
                                    padding: '0.5rem',
                                    border: '1px solid #d1d5db',
                                    borderRadius: '4px',
                                    marginBottom: '1rem'
                                }}
                            />
                        </div>

                        <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '0.5rem' }}>
                            <button
                                onClick={() => { setShowResetModal(false); setConfirmText(''); }}
                                style={{
                                    padding: '0.5rem 1rem',
                                    backgroundColor: '#f3f4f6',
                                    border: 'none',
                                    borderRadius: '4px',
                                    cursor: 'pointer'
                                }}
                                disabled={resetting}
                            >
                                Cancel
                            </button>
                            <button
                                onClick={handleResetSemester}
                                disabled={confirmText !== 'CONFIRM' || resetting}
                                style={{
                                    padding: '0.5rem 1rem',
                                    backgroundColor: confirmText === 'CONFIRM' ? '#dc2626' : '#9ca3af',
                                    color: 'white',
                                    border: 'none',
                                    borderRadius: '4px',
                                    cursor: confirmText === 'CONFIRM' ? 'pointer' : 'not-allowed'
                                }}
                            >
                                {resetting ? 'Resetting...' : 'Confirm Reset'}
                            </button>
                        </div>
                    </div>
                </div>
            )}
        </div>
    );

}

export default AdminDashboard;
