/**
 * Audit Logs Page
 * 
 * View system activity logs.
 * Accessible only to Admin and HOD.
 */

import { useState, useEffect } from 'react';
import { auditLogAPI } from '../services/api';

function AuditLogs() {
    const [logs, setLogs] = useState([]);
    const [loading, setLoading] = useState(true);
    const [filter, setFilter] = useState('');

    useEffect(() => {
        loadLogs();
    }, []);

    const loadLogs = async () => {
        try {
            const response = await auditLogAPI.getAll();
            setLogs(response.data.results || response.data);
        } catch (error) {
            console.error('Error loading audit logs:', error);
        } finally {
            setLoading(false);
        }
    };

    const filteredLogs = logs.filter(log =>
        log.user_name?.toLowerCase().includes(filter.toLowerCase()) ||
        log.action?.toLowerCase().includes(filter.toLowerCase()) ||
        log.model_name?.toLowerCase().includes(filter.toLowerCase()) ||
        log.object_id?.toLowerCase().includes(filter.toLowerCase())
    );

    return (
        <div className="audit-logs-page">
            <div className="page-header">
                <h1 className="page-title">System Audit Logs</h1>
                <p className="page-description">Track all critical system activities and changes.</p>
            </div>

            <div className="card">
                <div className="filters">
                    <input
                        type="text"
                        placeholder="Search logs..."
                        className="filter-input"
                        value={filter}
                        onChange={(e) => setFilter(e.target.value)}
                        style={{ padding: '0.5rem', width: '100%', maxWidth: '300px', border: '1px solid #ddd', borderRadius: '4px' }}
                    />
                    <button onClick={loadLogs} className="btn btn-secondary" style={{ marginLeft: '1rem' }}>
                        Refresh
                    </button>
                </div>

                {loading ? (
                    <div className="loading-spinner">Loading logs...</div>
                ) : (
                    <div className="table-container" style={{ marginTop: '1rem', overflowX: 'auto' }}>
                        <table className="data-table" style={{ width: '100%', borderCollapse: 'collapse' }}>
                            <thead>
                                <tr style={{ background: '#f8f9fa', textAlign: 'left' }}>
                                    <th style={{ padding: '12px', borderBottom: '2px solid #ddd' }}>Timestamp</th>
                                    <th style={{ padding: '12px', borderBottom: '2px solid #ddd' }}>User</th>
                                    <th style={{ padding: '12px', borderBottom: '2px solid #ddd' }}>Action</th>
                                    <th style={{ padding: '12px', borderBottom: '2px solid #ddd' }}>Entity</th>
                                    <th style={{ padding: '12px', borderBottom: '2px solid #ddd' }}>Object ID</th>
                                    <th style={{ padding: '12px', borderBottom: '2px solid #ddd' }}>Details</th>
                                </tr>
                            </thead>
                            <tbody>
                                {filteredLogs.length > 0 ? (
                                    filteredLogs.map((log) => (
                                        <tr key={log.id} style={{ borderBottom: '1px solid #eee' }}>
                                            <td style={{ padding: '12px' }}>{new Date(log.timestamp).toLocaleString()}</td>
                                            <td style={{ padding: '12px' }}>
                                                <span className="badge" style={{ background: '#e9ecef', color: '#495057', padding: '0.25rem 0.5rem', borderRadius: '4px', fontSize: '0.875rem' }}>
                                                    {log.user_name || 'System'}
                                                </span>
                                            </td>
                                            <td style={{ padding: '12px' }}>
                                                <span className={`badge ${getActionColor(log.action)}`} style={{ padding: '0.25rem 0.5rem', borderRadius: '4px', fontSize: '0.875rem', color: 'white' }}>
                                                    {log.action}
                                                </span>
                                            </td>
                                            <td style={{ padding: '12px' }}>{log.model_name}</td>
                                            <td style={{ padding: '12px' }}><code style={{ background: '#f8f9fa', padding: '2px 4px', borderRadius: '3px' }}>{log.object_id}</code></td>
                                            <td style={{ padding: '12px' }}>
                                                <details>
                                                    <summary style={{ cursor: 'pointer', color: '#007bff' }}>View Details</summary>
                                                    <pre style={{ fontSize: '0.75rem', background: '#f1f1f1', padding: '0.5rem', borderRadius: '4px', marginTop: '0.5rem', maxWidth: '300px', overflowX: 'auto' }}>
                                                        {JSON.stringify(log.details, null, 2)}
                                                    </pre>
                                                </details>
                                            </td>
                                        </tr>
                                    ))
                                ) : (
                                    <tr>
                                        <td colSpan="6" style={{ padding: '2rem', textAlign: 'center', color: '#666' }}>
                                            No logs found matching your criteria.
                                        </td>
                                    </tr>
                                )}
                            </tbody>
                        </table>
                    </div>
                )}
            </div>
        </div>
    );
}

function getActionColor(action) {
    switch (action) {
        case 'CREATE': return 'bg-success'; // Green (need to define class or use style)
        case 'UPDATE': return 'bg-warning'; // Orange
        case 'DELETE': return 'bg-danger';  // Red
        case 'LOGIN': return 'bg-info';     // Blue
        default: return 'bg-secondary';
    }
}

// Inline styles helper for badges if classes don't exist
const styles = `
.bg-success { background-color: #28a745; }
.bg-warning { background-color: #ffc107; color: #212529 !important; }
.bg-danger { background-color: #dc3545; }
.bg-info { background-color: #17a2b8; }
.bg-secondary { background-color: #6c757d; }
`;

// Inject styles (hacky but quick, or move to CSS file)
const styleSheet = document.createElement("style");
styleSheet.innerText = styles;
document.head.appendChild(styleSheet);

export default AuditLogs;
