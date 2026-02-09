/**
 * Admin Dashboard
 * 
 * Overview for System Administrators
 */

import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { scheduleAPI, teacherAPI, courseAPI, roomAPI, sectionAPI } from '../../services/api';

function AdminDashboard() {
    const [stats, setStats] = useState({
        teachers: 0,
        courses: 0,
        rooms: 0,
        sections: 0,
        schedules: 0,
    });
    const [loading, setLoading] = useState(true);

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
        </div>
    );
}

export default AdminDashboard;
