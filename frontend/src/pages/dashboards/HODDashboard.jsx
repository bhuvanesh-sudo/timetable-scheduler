/**
 * HOD Dashboard
 * 
 * Overview for Heads of Department
 */

import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { useAuth } from '../../context/AuthContext';
import { teacherAPI, sectionAPI } from '../../services/api';

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
            const [teachers, sections] = await Promise.all([
                teacherAPI.byDepartment(user.department),
                sectionAPI.getAll(),
            ]);

            const sectionData = sections.data.results || sections.data || [];
            const deptSections = sectionData.filter(s => s.department === user.department);

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
        <div className="fade-in">
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

            <div className="actions-section">
                <h2 className="actions-header">Department Actions</h2>
                <div className="actions-grid">
                    <Link to="/data" className="action-card">
                        <h3>Manage Faculty</h3>
                        <p>View and edit faculty details.</p>
                    </Link>
                    <Link to="/timetable" className="action-card">
                        <h3>Dept Timetable</h3>
                        <p>View generated schedules for {user.department}.</p>
                    </Link>
                    <Link to="/analytics" className="action-card">
                        <h3>Workload Reports</h3>
                        <p>Check faculty workload distribution.</p>
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
