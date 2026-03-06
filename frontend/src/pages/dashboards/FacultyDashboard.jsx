/**
 * Faculty Dashboard
 * 
 * Personal overview for Faculty Members
 */

import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { useAuth } from '../../context/AuthContext';
import { teacherAPI, notificationAPI } from '../../services/api';

function FacultyDashboard() {
    const { user } = useAuth();
    const [myCourses, setMyCourses] = useState([]);
    const [nextClass, setNextClass] = useState(null);
    const [loading, setLoading] = useState(true);
    const [notifications, setNotifications] = useState([]);
    const [notifLoading, setNotifLoading] = useState(true);

    useEffect(() => {
        loadFacultyData();
        loadNotifications();
    }, [user]);

    const loadFacultyData = async () => {
        try {
            const teachers = await teacherAPI.getAll();
            const teacherData = teachers.data.results || teachers.data || [];
            const me = teacherData.find(t => t.teacher_name?.toLowerCase() === user.username.toLowerCase() || t.email === user.email);

            if (me) {
                setMyCourses([]);
            }

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

    const loadNotifications = async () => {
        setNotifLoading(true);
        try {
            const res = await notificationAPI.getAll();
            const data = res.data.results || res.data || [];
            setNotifications(data);
        } catch (error) {
            console.error('Error loading notifications:', error);
        } finally {
            setNotifLoading(false);
        }
    };

    const handleMarkRead = async (id) => {
        try {
            await notificationAPI.markRead(id);
            setNotifications(prev =>
                prev.map(n => n.id === id ? { ...n, is_read: true } : n)
            );
        } catch (err) {
            console.error('Failed to mark as read:', err);
        }
    };

    const handleMarkAllRead = async () => {
        try {
            await notificationAPI.markAllRead();
            setNotifications(prev => prev.map(n => ({ ...n, is_read: true })));
        } catch (err) {
            console.error('Failed to mark all as read:', err);
        }
    };

    const timeAgo = (dateStr) => {
        const now = new Date();
        const date = new Date(dateStr);
        const diff = Math.floor((now - date) / 1000);
        if (diff < 60) return 'just now';
        if (diff < 3600) return `${Math.floor(diff / 60)}m ago`;
        if (diff < 86400) return `${Math.floor(diff / 3600)}h ago`;
        return `${Math.floor(diff / 86400)}d ago`;
    };

    if (loading) return <div className="loading-spinner">Loading faculty dashboard...</div>;

    const unreadNotifs = notifications.filter(n => !n.is_read);

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
                                <span style={{ marginRight: '1rem', fontSize: '1.5rem' }}>📅</span>
                                <div>
                                    <div style={{ fontWeight: '500' }}>My Timetable</div>
                                    <div style={{ fontSize: '0.8rem', color: '#666' }}>View your weekly schedule</div>
                                </div>
                            </Link>
                        </li>
                        <li style={{ marginBottom: '1rem' }}>
                            <div style={{ display: 'flex', alignItems: 'center', textDecoration: 'none', color: 'inherit', padding: '0.875rem', background: 'var(--bg-tertiary)', borderRadius: 'var(--radius-md)', opacity: 0.6, cursor: 'not-allowed' }}>
                                <span style={{ marginRight: '1rem', fontSize: '1.5rem' }}>⏳</span>
                                <div>
                                    <div style={{ fontWeight: '500' }}>Update Availability</div>
                                    <div style={{ fontSize: '0.8rem', color: '#666' }}>Coming in Epic 2</div>
                                </div>
                            </div>
                        </li>
                    </ul>
                </div>
            </div>

            {/* Notifications Card */}
            <div className="card" style={{ marginTop: '2rem' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem' }}>
                    <h2 className="card-title" style={{ margin: 0 }}>
                        🔔 Recent Notifications
                        {unreadNotifs.length > 0 && (
                            <span style={{
                                marginLeft: '8px',
                                background: 'var(--danger, #e53e3e)',
                                color: '#fff',
                                fontSize: '0.7rem',
                                fontWeight: '700',
                                borderRadius: '12px',
                                padding: '2px 8px',
                                verticalAlign: 'middle',
                            }}>
                                {unreadNotifs.length} new
                            </span>
                        )}
                    </h2>
                    {unreadNotifs.length > 0 && (
                        <button
                            onClick={handleMarkAllRead}
                            style={{
                                background: 'none',
                                border: 'none',
                                color: 'var(--primary)',
                                cursor: 'pointer',
                                fontSize: '0.85rem',
                                fontWeight: '600',
                            }}
                        >
                            Mark all as read
                        </button>
                    )}
                </div>

                {notifLoading ? (
                    <p style={{ color: 'var(--text-secondary)' }}>Loading notifications...</p>
                ) : notifications.length === 0 ? (
                    <p style={{ color: 'var(--text-secondary)' }}>No notifications yet. You'll be notified when a new timetable is published.</p>
                ) : (
                    <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
                        {notifications.slice(0, 10).map(n => (
                            <div
                                key={n.id}
                                onClick={() => !n.is_read && handleMarkRead(n.id)}
                                style={{
                                    display: 'flex',
                                    alignItems: 'flex-start',
                                    gap: '12px',
                                    padding: '12px 14px',
                                    borderRadius: 'var(--radius-md)',
                                    background: n.is_read ? 'transparent' : 'var(--bg-secondary, #f7fafc)',
                                    border: `1px solid ${n.is_read ? 'var(--border-color, #e2e8f0)' : 'var(--primary)'}`,
                                    cursor: n.is_read ? 'default' : 'pointer',
                                    transition: 'all 0.2s ease',
                                }}
                            >
                                <div style={{
                                    width: '10px',
                                    height: '10px',
                                    borderRadius: '50%',
                                    background: n.is_read ? 'var(--text-muted)' : 'var(--primary, #4f46e5)',
                                    flexShrink: 0,
                                    marginTop: '5px',
                                }} />
                                <div style={{ flex: 1 }}>
                                    <div style={{
                                        fontWeight: n.is_read ? '400' : '600',
                                        fontSize: '0.9rem',
                                        marginBottom: '4px',
                                    }}>
                                        {n.title}
                                    </div>
                                    <div style={{
                                        fontSize: '0.8rem',
                                        color: 'var(--text-secondary)',
                                        whiteSpace: 'pre-line',
                                        lineHeight: '1.5',
                                    }}>
                                        {n.message}
                                    </div>
                                    <div style={{
                                        fontSize: '0.72rem',
                                        color: 'var(--text-muted)',
                                        marginTop: '4px',
                                    }}>
                                        {timeAgo(n.created_at)}
                                    </div>
                                </div>
                            </div>
                        ))}
                    </div>
                )}
            </div>
        </div>
    );
}

export default FacultyDashboard;

