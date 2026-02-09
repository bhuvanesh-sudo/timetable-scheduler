/**
 * Faculty Dashboard
 * 
 * Personal overview for Faculty Members
 */

import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { useAuth } from '../../context/AuthContext';
import { teacherAPI, scheduleAPI } from '../../services/api';

function FacultyDashboard() {
    const { user } = useAuth();
    const [myCourses, setMyCourses] = useState([]);
    const [nextClass, setNextClass] = useState(null);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        loadFacultyData();
    }, [user]);

    const loadFacultyData = async () => {
        try {
            // Note: In MVP, we might not have a direct link between User and Teacher models yet.
            // We'll try to find a teacher with the same name/email, or just show general info.
            const teacherData = teachers.data.results || teachers.data || [];
            const me = teacherData.find(t => t.teacher_name?.toLowerCase() === user.username.toLowerCase() || t.email === user.email);

            if (me) {
                // If we found the teacher profile, load their courses
                // This assumes an endpoint or filtering potential.
                // For now, we'll just show a placeholder or "No assigned courses found" if not implemented.
                setMyCourses([]);
            }

            // Mocking "Next Class" for UI demonstration
            setNextClass({
                course: "CS101",
                time: "10:00 AM",
                room: "C-101"
            });

        } catch (error) {
            console.error('Error loading faculty data:', error);
        } finally {
            setLoading(false);
        }
    };

    if (loading) return <div className="loading-spinner">Loading faculty dashboard...</div>;

    return (
        <div className="fade-in">
            <div className="page-header">
                <h1 className="page-title">Personal Dashboard</h1>
                <p className="page-description">View your upcoming classes and manage your schedule.</p>
            </div>

            <div className="dashboard-grid" style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(300px, 1fr))', gap: '2rem' }}>

                {/* Upcoming Class Card */}
                <div className="card" style={{ borderLeft: '5px solid var(--primary)' }}>
                    <h2 className="card-title">Next Class</h2>
                    {nextClass ? (
                        <div className="class-details">
                            <div style={{ fontSize: '2.5rem', fontWeight: '800', color: 'var(--primary)' }}>{nextClass.time}</div>
                            <div style={{ fontSize: '1.2rem', marginTop: '0.5rem' }}>{nextClass.course}</div>
                            <div style={{ color: 'var(--text-secondary)' }}>Room: {nextClass.room}</div>
                        </div>
                    ) : (
                        <p>No classes scheduled for today.</p>
                    )}
                    <Link to="/timetable" className="btn btn-primary" style={{ marginTop: '1rem', display: 'inline-block' }}>
                        View Full Timetable
                    </Link>
                </div>

                {/* Quick Actions */}
                <div className="card">
                    <h2 className="card-title">My Actions</h2>
                    <ul className="action-list" style={{ listStyle: 'none', padding: 0 }}>
                        <li style={{ marginBottom: '1rem' }}>
                            <Link to="/timetable" style={{ display: 'flex', alignItems: 'center', textDecoration: 'none', color: 'inherit', padding: '0.875rem', background: 'var(--bg-tertiary)', borderRadius: 'var(--radius-md)' }}>
                                <span style={{ marginRight: '1rem', fontSize: '1.5rem' }}></span>
                                <div>
                                    <div style={{ fontWeight: '500' }}>My Timetable</div>
                                    <div style={{ fontSize: '0.8rem', color: '#666' }}>View your weekly schedule</div>
                                </div>
                            </Link>
                        </li>
                        <li style={{ marginBottom: '1rem' }}>
                            <div style={{ display: 'flex', alignItems: 'center', textDecoration: 'none', color: 'inherit', padding: '0.875rem', background: 'var(--bg-tertiary)', borderRadius: 'var(--radius-md)', opacity: 0.6, cursor: 'not-allowed' }}>
                                <span style={{ marginRight: '1rem', fontSize: '1.5rem' }}></span>
                                <div>
                                    <div style={{ fontWeight: '500' }}>Update Availability</div>
                                    <div style={{ fontSize: '0.8rem', color: '#666' }}>Coming in Epic 2</div>
                                </div>
                            </div>
                        </li>
                    </ul>
                </div>
            </div>

            <div className="card" style={{ marginTop: '2rem' }}>
                <h2 className="card-title">Department Announcements</h2>
                <p>No new announcements from {user.department || 'your department'}.</p>
            </div>
        </div>
    );
}

export default FacultyDashboard;
