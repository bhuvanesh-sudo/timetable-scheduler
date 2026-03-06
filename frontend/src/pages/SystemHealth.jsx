/**
 * System Health & Backup Management Page
 * 
 * Admin-only page for database backup management.
 * Story 6.2 - Automated Backups
 */

import { useState, useEffect } from 'react';
import { systemAPI } from '../services/api';

function SystemHealth() {
    const [systemInfo, setSystemInfo] = useState(null);
    const [backups, setBackups] = useState([]);
    const [loading, setLoading] = useState(true);
    const [actionLoading, setActionLoading] = useState(false);
    const [error, setError] = useState(null);
    const [successMsg, setSuccessMsg] = useState(null);
    const [restoreConfirm, setRestoreConfirm] = useState(null);
    const [deleteConfirm, setDeleteConfirm] = useState(null);
    const [backupLabel, setBackupLabel] = useState('');

    useEffect(() => {
        loadData();
    }, []);

    // Auto-dismiss success messages
    useEffect(() => {
        if (successMsg) {
            const timer = setTimeout(() => setSuccessMsg(null), 4000);
            return () => clearTimeout(timer);
        }
    }, [successMsg]);

    const loadData = async () => {
        setLoading(true);
        setError(null);
        try {
            const [infoRes, backupsRes] = await Promise.all([
                systemAPI.getInfo(),
                systemAPI.listBackups(),
            ]);
            setSystemInfo(infoRes.data);
            setBackups(backupsRes.data.backups || []);
        } catch (err) {
            console.error('Error loading system info:', err);
            setError('Failed to load system information.');
        } finally {
            setLoading(false);
        }
    };

    const handleCreateBackup = async () => {
        setActionLoading(true);
        setError(null);
        try {
            const res = await systemAPI.createBackup(backupLabel);
            setSuccessMsg(res.data.message || 'Backup created successfully!');
            setBackupLabel('');
            await loadData();
        } catch (err) {
            console.error('Backup creation failed:', err);
            setError(err.response?.data?.error || 'Failed to create backup.');
        } finally {
            setActionLoading(false);
        }
    };

    const handleRestore = async (filename) => {
        setActionLoading(true);
        setError(null);
        setRestoreConfirm(null);
        try {
            const res = await systemAPI.restoreBackup(filename);
            setSuccessMsg(
                `Database restored from ${filename}. Safety backup: ${res.data.safety_backup}`
            );
            await loadData();
        } catch (err) {
            console.error('Restore failed:', err);
            setError(err.response?.data?.error || 'Failed to restore backup.');
        } finally {
            setActionLoading(false);
        }
    };

    const handleDelete = async (filename) => {
        setActionLoading(true);
        setError(null);
        setDeleteConfirm(null);
        try {
            await systemAPI.deleteBackup(filename);
            setSuccessMsg(`Deleted: ${filename}`);
            await loadData();
        } catch (err) {
            console.error('Delete failed:', err);
            setError(err.response?.data?.error || 'Failed to delete backup.');
        } finally {
            setActionLoading(false);
        }
    };

    const formatDate = (isoString) => {
        if (!isoString) return 'Unknown';
        return new Date(isoString).toLocaleString();
    };

    return (
        <div className="system-health-page">
            <div className="page-header">
                <h1 className="page-title">System Health & Backups</h1>
                <p className="page-description">
                    Manage database backups and monitor system health.
                </p>
            </div>

            {/* Alerts */}
            {successMsg && (
                <div style={{
                    padding: '1rem 1.25rem',
                    marginBottom: '1.5rem',
                    borderRadius: '8px',
                    background: 'linear-gradient(135deg, rgba(34, 197, 94, 0.15), rgba(34, 197, 94, 0.05))',
                    border: '1px solid rgba(34, 197, 94, 0.3)',
                    color: '#16a34a',
                    fontWeight: 500,
                    display: 'flex',
                    alignItems: 'center',
                    gap: '0.5rem',
                }}>
                    ✓ {successMsg}
                </div>
            )}

            {error && (
                <div style={{
                    padding: '1rem 1.25rem',
                    marginBottom: '1.5rem',
                    borderRadius: '8px',
                    background: 'linear-gradient(135deg, rgba(239, 68, 68, 0.15), rgba(239, 68, 68, 0.05))',
                    border: '1px solid rgba(239, 68, 68, 0.3)',
                    color: '#dc2626',
                    fontWeight: 500,
                    display: 'flex',
                    alignItems: 'center',
                    gap: '0.5rem',
                }}>
                    ✕ {error}
                </div>
            )}

            {loading ? (
                <div className="loading-spinner">Loading system info...</div>
            ) : (
                <>
                    {/* System Overview Cards */}
                    <div style={{
                        display: 'grid',
                        gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))',
                        gap: '1.25rem',
                        marginBottom: '2rem',
                    }}>
                        {/* Database Card */}
                        <div className="card" style={{
                            padding: '1.5rem',
                            background: 'var(--card-bg)',
                            borderRadius: '12px',
                            border: '1px solid var(--border-color)',
                        }}>
                            <div style={{ fontSize: '0.8rem', textTransform: 'uppercase', letterSpacing: '0.05em', color: 'var(--text-muted)', marginBottom: '0.5rem' }}>
                                Database
                            </div>
                            <div style={{ fontSize: '1.75rem', fontWeight: 700, color: 'var(--text-primary)', lineHeight: 1.2 }}>
                                {systemInfo?.database?.size_display || '—'}
                            </div>
                            <div style={{ fontSize: '0.85rem', color: 'var(--text-secondary)', marginTop: '0.25rem' }}>
                                {systemInfo?.database?.engine} • {systemInfo?.database?.path}
                            </div>
                        </div>

                        {/* Backups Count Card */}
                        <div className="card" style={{
                            padding: '1.5rem',
                            background: 'var(--card-bg)',
                            borderRadius: '12px',
                            border: '1px solid var(--border-color)',
                        }}>
                            <div style={{ fontSize: '0.8rem', textTransform: 'uppercase', letterSpacing: '0.05em', color: 'var(--text-muted)', marginBottom: '0.5rem' }}>
                                Total Backups
                            </div>
                            <div style={{ fontSize: '1.75rem', fontWeight: 700, color: 'var(--text-primary)', lineHeight: 1.2 }}>
                                {systemInfo?.backups?.count ?? 0}
                            </div>
                            <div style={{ fontSize: '0.85rem', color: 'var(--text-secondary)', marginTop: '0.25rem' }}>
                                {systemInfo?.backups?.total_size_display || '0 B'} total
                            </div>
                        </div>

                        {/* Status Card */}
                        <div className="card" style={{
                            padding: '1.5rem',
                            background: 'var(--card-bg)',
                            borderRadius: '12px',
                            border: '1px solid var(--border-color)',
                        }}>
                            <div style={{ fontSize: '0.8rem', textTransform: 'uppercase', letterSpacing: '0.05em', color: 'var(--text-muted)', marginBottom: '0.5rem' }}>
                                System Status
                            </div>
                            <div style={{ fontSize: '1.75rem', fontWeight: 700, color: '#16a34a', lineHeight: 1.2 }}>
                                Online
                            </div>
                            <div style={{ fontSize: '0.85rem', color: 'var(--text-secondary)', marginTop: '0.25rem' }}>
                                All services running
                            </div>
                        </div>
                    </div>

                    {/* Backup Management */}
                    <div className="card" style={{ padding: '1.5rem', borderRadius: '12px' }}>
                        <div style={{
                            display: 'flex',
                            justifyContent: 'space-between',
                            alignItems: 'center',
                            marginBottom: '1.25rem',
                        }}>
                            <h2 style={{ margin: 0, fontSize: '1.15rem', fontWeight: 600, color: 'var(--text-primary)' }}>
                                Backup History
                            </h2>
                            <div style={{ display: 'flex', gap: '0.5rem', alignItems: 'center' }}>
                                <input
                                    type="text"
                                    placeholder="Backup label (optional)"
                                    value={backupLabel}
                                    onChange={(e) => setBackupLabel(e.target.value)}
                                    onKeyDown={(e) => e.key === 'Enter' && !actionLoading && handleCreateBackup()}
                                    style={{
                                        padding: '0.5rem 0.75rem',
                                        fontSize: '0.85rem',
                                        border: '1px solid var(--border-color, #ddd)',
                                        borderRadius: '6px',
                                        width: '200px',
                                        background: 'var(--card-bg, #fff)',
                                        color: 'var(--text-primary)',
                                    }}
                                />
                                <button
                                    onClick={loadData}
                                    className="btn btn-secondary"
                                    disabled={actionLoading}
                                    style={{ padding: '0.5rem 1rem', fontSize: '0.85rem' }}
                                >
                                    Refresh
                                </button>
                                <button
                                    onClick={handleCreateBackup}
                                    className="btn btn-primary"
                                    disabled={actionLoading}
                                    style={{
                                        padding: '0.5rem 1.25rem',
                                        fontSize: '0.85rem',
                                        background: 'linear-gradient(135deg, #3b82f6, #2563eb)',
                                        color: '#fff',
                                        border: 'none',
                                        borderRadius: '6px',
                                        cursor: actionLoading ? 'wait' : 'pointer',
                                        fontWeight: 600,
                                    }}
                                >
                                    {actionLoading ? 'Working...' : '+ Backup Now'}
                                </button>
                            </div>
                        </div>

                        {backups.length === 0 ? (
                            <div style={{
                                textAlign: 'center',
                                padding: '3rem 1rem',
                                color: 'var(--text-muted)',
                            }}>
                                <div style={{ fontSize: '2.5rem', marginBottom: '0.75rem' }}>📦</div>
                                <p style={{ margin: 0, fontSize: '1rem', fontWeight: 500 }}>No backups yet</p>
                                <p style={{ margin: '0.25rem 0 0', fontSize: '0.85rem' }}>
                                    Click "Backup Now" to create your first backup.
                                </p>
                            </div>
                        ) : (
                            <div style={{ overflowX: 'auto' }}>
                                <table className="data-table" style={{ width: '100%', borderCollapse: 'collapse' }}>
                                    <thead>
                                        <tr style={{ textAlign: 'left' }}>
                                            <th style={{ padding: '10px 12px', borderBottom: '2px solid var(--border-color)', fontSize: '0.8rem', textTransform: 'uppercase', letterSpacing: '0.04em', color: 'var(--text-muted)' }}>Backup</th>
                                            <th style={{ padding: '10px 12px', borderBottom: '2px solid var(--border-color)', fontSize: '0.8rem', textTransform: 'uppercase', letterSpacing: '0.04em', color: 'var(--text-muted)' }}>Created</th>
                                            <th style={{ padding: '10px 12px', borderBottom: '2px solid var(--border-color)', fontSize: '0.8rem', textTransform: 'uppercase', letterSpacing: '0.04em', color: 'var(--text-muted)' }}>Size</th>
                                            <th style={{ padding: '10px 12px', borderBottom: '2px solid var(--border-color)', fontSize: '0.8rem', textTransform: 'uppercase', letterSpacing: '0.04em', color: 'var(--text-muted)', textAlign: 'right' }}>Actions</th>
                                        </tr>
                                    </thead>
                                    <tbody>
                                        {backups.map((backup, idx) => (
                                            <tr key={backup.filename} style={{
                                                borderBottom: '1px solid var(--border-color)',
                                                background: idx === 0 ? 'rgba(59, 130, 246, 0.04)' : 'transparent',
                                            }}>
                                                <td style={{ padding: '12px' }}>
                                                    <div>
                                                        {backup.label && (
                                                            <div style={{
                                                                fontWeight: 600,
                                                                fontSize: '0.9rem',
                                                                color: 'var(--text-primary)',
                                                                marginBottom: '2px',
                                                            }}>
                                                                {backup.label}
                                                            </div>
                                                        )}
                                                        <code style={{
                                                            background: 'var(--bg-secondary, #f1f5f9)',
                                                            padding: '3px 8px',
                                                            borderRadius: '4px',
                                                            fontSize: '0.78rem',
                                                            fontFamily: 'monospace',
                                                            color: 'var(--text-muted)',
                                                        }}>
                                                            {backup.filename}
                                                        </code>
                                                        {idx === 0 && (
                                                            <span style={{
                                                                marginLeft: '0.5rem',
                                                                fontSize: '0.7rem',
                                                                padding: '2px 6px',
                                                                borderRadius: '9999px',
                                                                background: 'rgba(59, 130, 246, 0.15)',
                                                                color: '#2563eb',
                                                                fontWeight: 600,
                                                            }}>
                                                                LATEST
                                                            </span>
                                                        )}
                                                    </div>
                                                </td>
                                                <td style={{ padding: '12px', fontSize: '0.9rem', color: 'var(--text-secondary)' }}>
                                                    {formatDate(backup.created_at)}
                                                </td>
                                                <td style={{ padding: '12px', fontSize: '0.9rem', color: 'var(--text-secondary)' }}>
                                                    {backup.size_display}
                                                </td>
                                                <td style={{ padding: '12px', textAlign: 'right' }}>
                                                    <div style={{ display: 'flex', gap: '0.5rem', justifyContent: 'flex-end' }}>
                                                        <button
                                                            onClick={() => setRestoreConfirm(backup.filename)}
                                                            disabled={actionLoading}
                                                            style={{
                                                                padding: '0.35rem 0.75rem',
                                                                fontSize: '0.8rem',
                                                                background: 'rgba(245, 158, 11, 0.1)',
                                                                color: '#d97706',
                                                                border: '1px solid rgba(245, 158, 11, 0.3)',
                                                                borderRadius: '5px',
                                                                cursor: 'pointer',
                                                                fontWeight: 500,
                                                            }}
                                                        >
                                                            Restore
                                                        </button>
                                                        <button
                                                            onClick={() => setDeleteConfirm(backup.filename)}
                                                            disabled={actionLoading}
                                                            style={{
                                                                padding: '0.35rem 0.75rem',
                                                                fontSize: '0.8rem',
                                                                background: 'rgba(239, 68, 68, 0.1)',
                                                                color: '#dc2626',
                                                                border: '1px solid rgba(239, 68, 68, 0.3)',
                                                                borderRadius: '5px',
                                                                cursor: 'pointer',
                                                                fontWeight: 500,
                                                            }}
                                                        >
                                                            Delete
                                                        </button>
                                                    </div>
                                                </td>
                                            </tr>
                                        ))}
                                    </tbody>
                                </table>
                            </div>
                        )}
                    </div>
                </>
            )}

            {/* Restore Confirmation Modal */}
            {restoreConfirm && (
                <div style={{
                    position: 'fixed',
                    inset: 0,
                    background: 'rgba(0,0,0,0.5)',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    zIndex: 1000,
                    backdropFilter: 'blur(4px)',
                }}>
                    <div style={{
                        background: 'var(--card-bg, #fff)',
                        padding: '2rem',
                        borderRadius: '16px',
                        maxWidth: '460px',
                        width: '90%',
                        boxShadow: '0 20px 60px rgba(0,0,0,0.3)',
                    }}>
                        <div style={{ textAlign: 'center', marginBottom: '1.25rem' }}>
                            <div style={{ fontSize: '2.5rem' }}>⚠️</div>
                            <h3 style={{ margin: '0.5rem 0 0', fontSize: '1.15rem', color: 'var(--text-primary)' }}>
                                Confirm Database Restore
                            </h3>
                        </div>
                        <p style={{ color: 'var(--text-secondary)', fontSize: '0.9rem', textAlign: 'center', lineHeight: 1.6 }}>
                            This will <strong style={{ color: '#dc2626' }}>replace the current database</strong> with the backup:
                        </p>
                        <div style={{
                            background: 'var(--bg-secondary, #f1f5f9)',
                            padding: '0.75rem 1rem',
                            borderRadius: '8px',
                            textAlign: 'center',
                            fontFamily: 'monospace',
                            fontSize: '0.85rem',
                            margin: '0.75rem 0 1rem',
                            color: 'var(--text-primary)',
                        }}>
                            {restoreConfirm}
                        </div>
                        <p style={{ color: 'var(--text-muted)', fontSize: '0.8rem', textAlign: 'center', margin: '0 0 1.25rem' }}>
                            A safety backup of the current state will be created automatically.
                        </p>
                        <div style={{ display: 'flex', gap: '0.75rem', justifyContent: 'center' }}>
                            <button
                                onClick={() => setRestoreConfirm(null)}
                                style={{
                                    padding: '0.6rem 1.5rem',
                                    background: 'var(--bg-secondary, #e2e8f0)',
                                    border: '1px solid var(--border-color)',
                                    borderRadius: '8px',
                                    cursor: 'pointer',
                                    fontWeight: 500,
                                    color: 'var(--text-primary)',
                                }}
                            >
                                Cancel
                            </button>
                            <button
                                onClick={() => handleRestore(restoreConfirm)}
                                style={{
                                    padding: '0.6rem 1.5rem',
                                    background: 'linear-gradient(135deg, #f59e0b, #d97706)',
                                    color: '#fff',
                                    border: 'none',
                                    borderRadius: '8px',
                                    cursor: 'pointer',
                                    fontWeight: 600,
                                }}
                            >
                                Yes, Restore
                            </button>
                        </div>
                    </div>
                </div>
            )}

            {/* Delete Confirmation Modal */}
            {deleteConfirm && (
                <div style={{
                    position: 'fixed',
                    inset: 0,
                    background: 'rgba(0,0,0,0.5)',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    zIndex: 1000,
                    backdropFilter: 'blur(4px)',
                }}>
                    <div style={{
                        background: 'var(--card-bg, #fff)',
                        padding: '2rem',
                        borderRadius: '16px',
                        maxWidth: '420px',
                        width: '90%',
                        boxShadow: '0 20px 60px rgba(0,0,0,0.3)',
                    }}>
                        <div style={{ textAlign: 'center', marginBottom: '1rem' }}>
                            <div style={{ fontSize: '2rem' }}>🗑️</div>
                            <h3 style={{ margin: '0.5rem 0 0', fontSize: '1.1rem', color: 'var(--text-primary)' }}>
                                Delete Backup?
                            </h3>
                        </div>
                        <p style={{ color: 'var(--text-secondary)', fontSize: '0.9rem', textAlign: 'center' }}>
                            This cannot be undone.
                        </p>
                        <div style={{
                            background: 'var(--bg-secondary, #f1f5f9)',
                            padding: '0.6rem 1rem',
                            borderRadius: '8px',
                            textAlign: 'center',
                            fontFamily: 'monospace',
                            fontSize: '0.85rem',
                            margin: '0.75rem 0 1.25rem',
                            color: 'var(--text-primary)',
                        }}>
                            {deleteConfirm}
                        </div>
                        <div style={{ display: 'flex', gap: '0.75rem', justifyContent: 'center' }}>
                            <button
                                onClick={() => setDeleteConfirm(null)}
                                style={{
                                    padding: '0.6rem 1.5rem',
                                    background: 'var(--bg-secondary, #e2e8f0)',
                                    border: '1px solid var(--border-color)',
                                    borderRadius: '8px',
                                    cursor: 'pointer',
                                    fontWeight: 500,
                                    color: 'var(--text-primary)',
                                }}
                            >
                                Cancel
                            </button>
                            <button
                                onClick={() => handleDelete(deleteConfirm)}
                                style={{
                                    padding: '0.6rem 1.5rem',
                                    background: 'linear-gradient(135deg, #ef4444, #dc2626)',
                                    color: '#fff',
                                    border: 'none',
                                    borderRadius: '8px',
                                    cursor: 'pointer',
                                    fontWeight: 600,
                                }}
                            >
                                Yes, Delete
                            </button>
                        </div>
                    </div>
                </div>
            )}
        </div>
    );
}

export default SystemHealth;
