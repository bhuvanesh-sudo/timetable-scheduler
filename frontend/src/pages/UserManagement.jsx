/**
 * User Management Page
 * 
 * Manage system users (Admin only).
 * Lists users and allows deletion of non-protected accounts.
 */

import { useState, useEffect } from 'react';
import { userAPI } from '../services/api';

function UserManagement() {
    const [users, setUsers] = useState([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);
    const [searchTerm, setSearchTerm] = useState('');

    useEffect(() => {
        loadUsers();
    }, []);

    const loadUsers = async () => {
        try {
            const response = await userAPI.getAll();
            setUsers(response.data.results || response.data);
            setError(null);
        } catch (err) {
            console.error('Error loading users:', err);
            setError('Failed to load users.');
        } finally {
            setLoading(false);
        }
    };

    const handleDelete = async (userId, username) => {
        if (!window.confirm(`Are you sure you want to delete user "${username}"? This action cannot be undone.`)) {
            return;
        }

        try {
            await userAPI.delete(userId);
            setUsers(users.filter(u => u.id !== userId));
            alert(`User "${username}" deleted successfully.`);
        } catch (err) {
            console.error('Error deleting user:', err);
            const msg = err.response?.data?.error || 'Failed to delete user. The account might be protected.';
            alert(msg);
        }
    };

    const filteredUsers = users.filter(user =>
        user.username.toLowerCase().includes(searchTerm.toLowerCase()) ||
        user.email.toLowerCase().includes(searchTerm.toLowerCase()) ||
        (user.department && user.department.toLowerCase().includes(searchTerm.toLowerCase()))
    );

    return (
        <div className="user-management-page">
            <div className="page-header">
                <h1 className="page-title">User Management</h1>
                <p className="page-description">Manage system access and roles.</p>
            </div>

            <div className="card">
                <div className="filters">
                    <input
                        type="text"
                        placeholder="Search users..."
                        className="filter-input"
                        value={searchTerm}
                        onChange={(e) => setSearchTerm(e.target.value)}
                        style={{ padding: '0.5rem', width: '100%', maxWidth: '300px', border: '1px solid #ddd', borderRadius: '4px' }}
                    />
                    <button onClick={loadUsers} className="btn btn-secondary" style={{ marginLeft: '1rem' }}>
                        Refresh
                    </button>
                    {/* Placeholder for Add User button - logical next step */}
                    <button className="btn btn-primary" style={{ marginLeft: 'auto' }} disabled title="Not implemented yet">
                        + Add User
                    </button>
                </div>

                {error && <div className="alert alert-danger">{error}</div>}

                {loading ? (
                    <div className="loading-spinner">Loading users...</div>
                ) : (
                    <div className="table-container" style={{ marginTop: '1rem', overflowX: 'auto' }}>
                        <table className="data-table" style={{ width: '100%', borderCollapse: 'collapse' }}>
                            <thead>
                                <tr style={{ background: '#f8f9fa', textAlign: 'left' }}>
                                    <th style={{ padding: '12px', borderBottom: '2px solid #ddd' }}>Username</th>
                                    <th style={{ padding: '12px', borderBottom: '2px solid #ddd' }}>Role</th>
                                    <th style={{ padding: '12px', borderBottom: '2px solid #ddd' }}>Department</th>
                                    <th style={{ padding: '12px', borderBottom: '2px solid #ddd' }}>Email</th>
                                    <th style={{ padding: '12px', borderBottom: '2px solid #ddd' }}>Status</th>
                                    <th style={{ padding: '12px', borderBottom: '2px solid #ddd' }}>Actions</th>
                                </tr>
                            </thead>
                            <tbody>
                                {filteredUsers.map((user) => (
                                    <tr key={user.id} style={{ borderBottom: '1px solid #eee' }}>
                                        <td style={{ padding: '12px', fontWeight: '500' }}>{user.username}</td>
                                        <td style={{ padding: '12px' }}>
                                            <span className={`badge ${getRoleBadgeClass(user.role)}`} style={{ padding: '0.25rem 0.5rem', borderRadius: '4px', fontSize: '0.875rem', color: 'white' }}>
                                                {user.role}
                                            </span>
                                        </td>
                                        <td style={{ padding: '12px' }}>{user.department || '-'}</td>
                                        <td style={{ padding: '12px' }}>{user.email}</td>
                                        <td style={{ padding: '12px' }}>
                                            {user.is_protected && <span title="Protected Account">🛡️ Protected</span>}
                                        </td>
                                        <td style={{ padding: '12px' }}>
                                            {!user.is_protected && (
                                                <button
                                                    onClick={() => handleDelete(user.id, user.username)}
                                                    className="btn btn-danger btn-sm"
                                                    style={{ padding: '0.25rem 0.5rem', background: '#dc3545', color: 'white', border: 'none', borderRadius: '3px', cursor: 'pointer' }}
                                                >
                                                    Delete
                                                </button>
                                            )}
                                        </td>
                                    </tr>
                                ))}
                            </tbody>
                        </table>
                    </div>
                )}
            </div>
        </div>
    );
}

function getRoleBadgeClass(role) {
    switch (role) {
        case 'ADMIN': return 'bg-danger';
        case 'HOD': return 'bg-warning';
        case 'FACULTY': return 'bg-info';
        default: return 'bg-secondary';
    }
}

export default UserManagement;
