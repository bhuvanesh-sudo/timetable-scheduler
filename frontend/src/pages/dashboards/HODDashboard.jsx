/**
 * HOD Dashboard
 * 
 * Overview for Heads of Department
 */

import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { useAuth } from '../../context/AuthContext';
import { teacherAPI, courseAPI, sectionAPI, scheduleAPI } from '../../services/api';

function HODDashboard() {
    const { user } = useAuth();
    const [stats, setStats] = useState({
        deptTeachers: 0,
        deptCourses: 0,
        deptSections: 0,
        pendingApprovals: 0,
    });
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        loadDeptStats();
    }, [user]);

    const loadDeptStats = async () => {
        if (!user?.department) return;

        try {
<<<<<<< HEAD
            // simulating dept filtering on client side for MVP or using specific endpoints if available
            const [teachers, sections] = await Promise.all([
                teacherAPI.byDepartment(user.department),
                sectionAPI.getAll(), // Filter locally
            ]);

            const deptSections = (sections.data.results || []).filter(s => s.department === user.department);
=======
            const [teachers, sections] = await Promise.all([
                teacherAPI.byDepartment(user.department),
                sectionAPI.getAll(),
            ]);

            const sectionData = sections.data.results || sections.data || [];
            const deptSections = sectionData.filter(s => s.department === user.department);
>>>>>>> sprint1

            setStats({
                deptTeachers: teachers.data.results?.length || teachers.data.length || 0,
                deptCourses: 0, // Placeholder, would need course-dept link
                deptSections: deptSections.length,
                pendingApprovals: 2, // Mock data for "Pending Schedule Approvals"
            });
        } catch (error) {
            console.error('Error loading HOD stats:', error);
        } finally {
            setLoading(false);
        }
    };

    if (loading) return <div className="loading-spinner">Loading department dashboard...</div>;

    return (
<<<<<<< HEAD
        <div className="hod-dashboard">
=======
        <div className="fade-in">
>>>>>>> sprint1
            <div className="page-header">
                <h1 className="page-title">Head of Department: {user.department}</h1>
                <p className="page-description">Oversee departmental academic planning and schedules.</p>
            </div>

            <div className="stats-grid">
                <div className="stat-card">
                    <div className="stat-label">Faculty Members</div>
                    <div className="stat-value">{stats.deptTeachers}</div>
                </div>
                <div className="stat-card">
                    <div className="stat-label">Active Sections</div>
                    <div className="stat-value">{stats.deptSections}</div>
                </div>
                <div className="stat-card">
                    <div className="stat-label">Pending Approvals</div>
                    <div className="stat-value" style={{ color: '#e67e22' }}>{stats.pendingApprovals}</div>
                </div>
            </div>

            <div className="actions-section" style={{ marginTop: '2rem' }}>
                <h2 style={{ fontSize: '1.25rem', marginBottom: '1rem', color: 'var(--text-primary)' }}>Department Actions</h2>
                <div className="actions-grid" style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '1rem' }}>
<<<<<<< HEAD
                    <Link to="/teacher-requests" className="action-card" style={{ padding: '1.5rem', background: 'white', borderRadius: '8px', border: '1px solid #eee', textDecoration: 'none', color: 'inherit', boxShadow: '0 2px 4px rgba(0,0,0,0.05)', transition: 'transform 0.2s' }}>
                        <h3 style={{ margin: '0 0 0.5rem 0', color: 'var(--primary-color)' }}>Teacher Requests</h3>
                        <p style={{ margin: 0, fontSize: '0.9rem', color: 'var(--text-secondary)' }}>Request changes to faculty details.</p>
                    </Link>
                    <Link to="/timetable" className="action-card" style={{ padding: '1.5rem', background: 'white', borderRadius: '8px', border: '1px solid #eee', textDecoration: 'none', color: 'inherit', boxShadow: '0 2px 4px rgba(0,0,0,0.05)', transition: 'transform 0.2s' }}>
                        <h3 style={{ margin: '0 0 0.5rem 0', color: 'var(--primary-color)' }}>Dept Timetable</h3>
                        <p style={{ margin: 0, fontSize: '0.9rem', color: 'var(--text-secondary)' }}>View generated schedules for {user.department}.</p>
                    </Link>
                    <Link to="/analytics" className="action-card" style={{ padding: '1.5rem', background: 'white', borderRadius: '8px', border: '1px solid #eee', textDecoration: 'none', color: 'inherit', boxShadow: '0 2px 4px rgba(0,0,0,0.05)', transition: 'transform 0.2s' }}>
                        <h3 style={{ margin: '0 0 0.5rem 0', color: 'var(--primary-color)' }}>Workload Reports</h3>
=======
                    <Link to="/data" className="action-card">
                        <h3 style={{ margin: '0 0 0.5rem 0', color: 'var(--primary)' }}>Manage Faculty</h3>
                        <p style={{ margin: 0, fontSize: '0.9rem', color: 'var(--text-secondary)' }}>View and edit faculty details.</p>
                    </Link>
                    <Link to="/timetable" className="action-card">
                        <h3 style={{ margin: '0 0 0.5rem 0', color: 'var(--primary)' }}>Dept Timetable</h3>
                        <p style={{ margin: 0, fontSize: '0.9rem', color: 'var(--text-secondary)' }}>View generated schedules for {user.department}.</p>
                    </Link>
                    <Link to="/analytics" className="action-card">
                        <h3 style={{ margin: '0 0 0.5rem 0', color: 'var(--primary)' }}>Workload Reports</h3>
>>>>>>> sprint1
                        <p style={{ margin: 0, fontSize: '0.9rem', color: 'var(--text-secondary)' }}>Check faculty workload distribution.</p>
                    </Link>
                </div>
            </div>

            <div className="card" style={{ marginTop: '2rem' }}>
                <h3>Department Notices via Scheduler</h3>
                <ul>
                    <li>Please review constraints for the upcoming semester.</li>
                    <li>Ensure all elective courses are assigned to sections.</li>
                </ul>
            </div>
        </div>
    );
}

export default HODDashboard;
