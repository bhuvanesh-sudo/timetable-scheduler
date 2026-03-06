/**
 * NotificationBell Component
 * 
 * Displays a bell icon with unread notification count badge.
 * On click, shows a dropdown panel with recent notifications.
 * Polls for unread count every 30 seconds.
 */

import { useState, useEffect, useRef } from 'react';
import { notificationAPI } from '../services/api';

function NotificationBell() {
    const [notifications, setNotifications] = useState([]);
    const [unreadCount, setUnreadCount] = useState(0);
    const [isOpen, setIsOpen] = useState(false);
    const [loading, setLoading] = useState(false);
    const panelRef = useRef(null);

    // Fetch unread count on mount and poll every 30s
    useEffect(() => {
        fetchUnreadCount();
        const interval = setInterval(fetchUnreadCount, 30000);
        return () => clearInterval(interval);
    }, []);

    // Close panel when clicking outside
    useEffect(() => {
        const handleClickOutside = (e) => {
            if (panelRef.current && !panelRef.current.contains(e.target)) {
                setIsOpen(false);
            }
        };
        document.addEventListener('mousedown', handleClickOutside);
        return () => document.removeEventListener('mousedown', handleClickOutside);
    }, []);

    const fetchUnreadCount = async () => {
        try {
            const res = await notificationAPI.getUnreadCount();
            setUnreadCount(res.data.count);
        } catch (err) {
            console.error('Failed to fetch unread count:', err);
        }
    };

    const fetchNotifications = async () => {
        setLoading(true);
        try {
            const res = await notificationAPI.getAll();
            const data = res.data.results || res.data || [];
            setNotifications(data);
        } catch (err) {
            console.error('Failed to fetch notifications:', err);
        } finally {
            setLoading(false);
        }
    };

    const togglePanel = () => {
        if (!isOpen) {
            fetchNotifications();
        }
        setIsOpen(!isOpen);
    };

    const handleMarkRead = async (id) => {
        try {
            await notificationAPI.markRead(id);
            setNotifications(prev =>
                prev.map(n => n.id === id ? { ...n, is_read: true } : n)
            );
            setUnreadCount(prev => Math.max(0, prev - 1));
        } catch (err) {
            console.error('Failed to mark as read:', err);
        }
    };

    const handleMarkAllRead = async () => {
        try {
            await notificationAPI.markAllRead();
            setNotifications(prev => prev.map(n => ({ ...n, is_read: true })));
            setUnreadCount(0);
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

    return (
        <div ref={panelRef} style={{ position: 'relative', display: 'inline-block' }}>
            {/* Bell Button */}
            <button
                onClick={togglePanel}
                id="notification-bell-btn"
                style={{
                    background: 'none',
                    border: 'none',
                    cursor: 'pointer',
                    fontSize: '1.4rem',
                    position: 'relative',
                    padding: '6px 8px',
                    borderRadius: 'var(--radius-md)',
                    transition: 'background 0.2s',
                    color: 'var(--text-primary)',
                }}
                onMouseEnter={(e) => e.target.style.background = 'var(--bg-tertiary)'}
                onMouseLeave={(e) => e.target.style.background = 'none'}
                title="Notifications"
            >
                🔔
                {unreadCount > 0 && (
                    <span style={{
                        position: 'absolute',
                        top: '2px',
                        right: '2px',
                        background: 'var(--danger, #e53e3e)',
                        color: '#fff',
                        fontSize: '0.65rem',
                        fontWeight: '700',
                        borderRadius: '50%',
                        minWidth: '18px',
                        height: '18px',
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'center',
                        lineHeight: '1',
                        boxShadow: '0 1px 3px rgba(0,0,0,0.3)',
                    }}>
                        {unreadCount > 99 ? '99+' : unreadCount}
                    </span>
                )}
            </button>

            {/* Dropdown Panel */}
            {isOpen && (
                <div
                    id="notification-panel"
                    style={{
                        position: 'absolute',
                        top: '100%',
                        right: '0',
                        width: '380px',
                        maxHeight: '480px',
                        overflowY: 'auto',
                        background: 'var(--bg-primary, #fff)',
                        border: '1px solid var(--border-color, #e2e8f0)',
                        borderRadius: 'var(--radius-lg, 12px)',
                        boxShadow: '0 10px 40px rgba(0,0,0,0.15)',
                        zIndex: 1000,
                        marginTop: '8px',
                    }}
                >
                    {/* Header */}
                    <div style={{
                        display: 'flex',
                        justifyContent: 'space-between',
                        alignItems: 'center',
                        padding: '14px 16px',
                        borderBottom: '1px solid var(--border-color, #e2e8f0)',
                    }}>
                        <h3 style={{ margin: 0, fontSize: '1rem', fontWeight: '700' }}>
                            Notifications
                        </h3>
                        {unreadCount > 0 && (
                            <button
                                onClick={handleMarkAllRead}
                                style={{
                                    background: 'none',
                                    border: 'none',
                                    color: 'var(--primary)',
                                    cursor: 'pointer',
                                    fontSize: '0.8rem',
                                    fontWeight: '600',
                                    padding: '4px 8px',
                                    borderRadius: 'var(--radius-sm)',
                                    transition: 'background 0.2s',
                                }}
                                onMouseEnter={(e) => e.target.style.background = 'var(--bg-tertiary)'}
                                onMouseLeave={(e) => e.target.style.background = 'none'}
                            >
                                Mark all as read
                            </button>
                        )}
                    </div>

                    {/* Content */}
                    {loading ? (
                        <div style={{ padding: '2rem', textAlign: 'center', color: 'var(--text-secondary)' }}>
                            Loading...
                        </div>
                    ) : notifications.length === 0 ? (
                        <div style={{ padding: '2rem', textAlign: 'center', color: 'var(--text-secondary)' }}>
                            <div style={{ fontSize: '2rem', marginBottom: '0.5rem' }}>🔕</div>
                            No notifications yet
                        </div>
                    ) : (
                        <div>
                            {notifications.map(n => (
                                <div
                                    key={n.id}
                                    onClick={() => !n.is_read && handleMarkRead(n.id)}
                                    style={{
                                        padding: '12px 16px',
                                        borderBottom: '1px solid var(--border-color, #e2e8f0)',
                                        cursor: n.is_read ? 'default' : 'pointer',
                                        background: n.is_read ? 'transparent' : 'var(--bg-secondary, #f7fafc)',
                                        transition: 'background 0.2s',
                                        display: 'flex',
                                        gap: '10px',
                                        alignItems: 'flex-start',
                                    }}
                                    onMouseEnter={(e) => {
                                        if (!n.is_read) e.currentTarget.style.background = 'var(--bg-tertiary)';
                                    }}
                                    onMouseLeave={(e) => {
                                        e.currentTarget.style.background = n.is_read ? 'transparent' : 'var(--bg-secondary, #f7fafc)';
                                    }}
                                >
                                    {/* Unread dot */}
                                    <div style={{
                                        width: '8px',
                                        height: '8px',
                                        borderRadius: '50%',
                                        background: n.is_read ? 'transparent' : 'var(--primary, #4f46e5)',
                                        flexShrink: 0,
                                        marginTop: '6px',
                                    }} />
                                    <div style={{ flex: 1, minWidth: 0 }}>
                                        <div style={{
                                            fontWeight: n.is_read ? '400' : '600',
                                            fontSize: '0.85rem',
                                            marginBottom: '4px',
                                            color: 'var(--text-primary)',
                                        }}>
                                            {n.title}
                                        </div>
                                        <div style={{
                                            fontSize: '0.78rem',
                                            color: 'var(--text-secondary)',
                                            whiteSpace: 'pre-line',
                                            lineHeight: '1.4',
                                            maxHeight: '80px',
                                            overflow: 'hidden',
                                        }}>
                                            {n.message}
                                        </div>
                                        <div style={{
                                            fontSize: '0.7rem',
                                            color: 'var(--text-muted, #a0aec0)',
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
            )}
        </div>
    );
}

export default NotificationBell;
