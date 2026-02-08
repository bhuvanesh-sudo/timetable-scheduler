/**
 * Dashboard Page - Overview of the system
 * 
 * Author: Frontend Team (Bhuvanesh, Akshitha)
 */

import { useState, useEffect } from 'react';
import { scheduleAPI, teacherAPI, courseAPI, roomAPI, sectionAPI } from '../services/api';
import { useAuth } from '../context/AuthContext';
import HODDashboard from '../components/HODDashboard';

function Dashboard() {
    const [stats, setStats] = useState({
        teachers: 0,
        courses: 0,
        rooms: 0,
        sections: 0,
        schedules: 0,
    });
    const [loading, setLoading] = useState(true);
    const { user } = useAuth();

    useEffect(() => {
        if (user?.role === 'HOD') {
            setLoading(false); // HOD Dashboard handles its own loading
            return;
        }
        loadStats();
    }, [user]);

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
                teachers: teachers.data.results?.length || teachers.data.count || 0,
                courses: courses.data.results?.length || courses.data.count || 0,
                rooms: rooms.data.results?.length || rooms.data.count || 0,
                sections: sections.data.results?.length || sections.data.count || 0,
                schedules: schedules.data.results?.length || schedules.data.count || 0,
            });
        } catch (error) {
            console.error('Error loading stats:', error);
        } finally {
            setLoading(false);
        }
    };

    if (loading) {
        return (
            <div className="loading">
                <div className="spinner"></div>
                <p>Loading dashboard...</p>
            </div>
        );
    }

    if (user?.role === 'HOD') {
        return <HODDashboard />;
    }

    return (
        <div>
            <div className="page-header">
                <h1 className="page-title">Dashboard</h1>
                <p className="page-description">Overview of the M3 Timetable Scheduling System</p>
            </div>

            <div className="stats-grid">
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

            <div className="card">
                <div className="card-header">
                    <h2 className="card-title">Welcome to M3 Timetable System</h2>
                </div>
                <p style={{ marginBottom: '1rem' }}>
                    This system helps you automatically generate conflict-free timetables for your institution.
                </p>
                <h3 style={{ marginBottom: '0.5rem', fontSize: '1.1rem' }}>Quick Start:</h3>
                <ol style={{ marginLeft: '1.5rem', lineHeight: '1.8' }}>
                    <li>Review your data in <strong>Data Management</strong></li>
                    <li>Generate a new schedule in <strong>Generate Schedule</strong></li>
                    <li>View the timetable in <strong>View Timetable</strong></li>
                    <li>Analyze workload in <strong>Analytics</strong></li>
                </ol>
            </div>
        </div>
    );
}

export default Dashboard;
