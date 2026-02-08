import React, { useState, useEffect } from 'react';
import { useAuth } from '../context/AuthContext';
import axios from 'axios';
import WorkloadChart from './WorkloadChart';

/**
 * HODDashboard Component
 * Provides a comprehensive interface for Department Heads to:
 * - Monitor faculty workload distribution
 * - Audit course assignments
 * - Manage elective buckets
 * - Review department-specific statistics
 */
const HODDashboard = () => {
    // Component State
    const { user } = useAuth(); // Current logged-in user details
    const [activeTab, setActiveTab] = useState('overview'); // Current selected navigation tab
    const [stats, setStats] = useState(null); // Department-wide statistics (faculty counts, sections, etc.)
    const [availabilities, setAvailabilities] = useState([]); // Faculty constraint submission status
    const [buckets, setBuckets] = useState([]); // Elective course groups
    const [loading, setLoading] = useState(true); // Loading state for data fetching
    const [searchTerm, setSearchTerm] = useState(''); // Faculty search query
    const [expandedFaculty, setExpandedFaculty] = useState(null); // ID of the faculty member currently being "reviewed" (expanded)

    // Fetch all dashboard-related data on component mount
    useEffect(() => {
        const fetchAllData = async () => {
            try {
                const token = localStorage.getItem('access_token');
                if (!token) return;

                const headers = { Authorization: `Bearer ${token}` };

                const [statsRes, availRes, bucketsRes] = await Promise.all([
                    axios.get('http://127.0.0.1:8000/api/dashboard-stats/', { headers }),
                    axios.get('http://127.0.0.1:8000/api/faculty-availabilities/', { headers }),
                    axios.get('http://127.0.0.1:8000/api/elective-buckets/', { headers })
                ]);

                setStats(statsRes.data);
                setAvailabilities(availRes.data.results || availRes.data);
                setBuckets(bucketsRes.data.results || bucketsRes.data);
            } catch (error) {
                console.error("Error fetching dashboard data:", error);
            } finally {
                setLoading(false);
            }
        };

        fetchAllData();
    }, []);

    if (loading) return <div className="loading">Loading {user.department} Dashboard...</div>;

    if (!stats || !stats.department_stats) {
        return (
            <div className="dashboard-container">
                <h1 className="page-title">Welcome, {user.first_name}</h1>
                <p className="page-description">No department data found. Please contact the administrator.</p>
            </div>
        );
    }

    const { department_stats } = stats;

    /**
     * Toggles the detailed breakdown view for a faculty member
     * @param {string} id - The teacher ID to expand/collapse
     */
    const toggleFaculty = (id) => {
        setExpandedFaculty(prev => prev === id ? null : id);
    };

    // Filter faculty list based on search term (searching by name or ID)
    const filteredFaculty = department_stats.faculty_workload.filter(f =>
        f.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
        f.id.toLowerCase().includes(searchTerm.toLowerCase())
    );

    /**
     * Helper to render the content based on activeTab
     */
    const renderTabContent = () => {
        switch (activeTab) {
            case 'overview':
                return (
                    <div className="tab-pane">
                        <div className="stats-grid">
                            <div className="stat-card hod-stat-card">
                                <div className="stat-icon-wrapper">
                                    <svg fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 4.354a4 4 0 110 5.292M15 21H3v-1a6 6 0 0112 0v1zm0 0h6v-1a6 6 0 00-9-5.197M13 7a4 4 0 11-8 0 4 4 0 018 0z" /></svg>
                                </div>
                                <div>
                                    <div className="stat-label">Department Faculty</div>
                                    <div className="stat-value">{department_stats.total_faculty}</div>
                                </div>
                            </div>
                            <div className="stat-card hod-stat-card">
                                <div className="stat-icon-wrapper">
                                    <svg fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16m14 0h2m-2 0h-5m-9 0H3m2 0h5M9 7h1m-1 4h1m4-4h1m-1 4h1m-5 10v-5a1 1 0 011-1h2a1 1 0 011 1v5m-4 0h4" /></svg>
                                </div>
                                <div>
                                    <div className="stat-label">Total Sections</div>
                                    <div className="stat-value">{department_stats.total_sections}</div>
                                </div>
                            </div>
                            <div className="stat-card hod-stat-card">
                                <div className="stat-icon-wrapper" style={{ color: department_stats.pending_constraints > 0 ? 'var(--warning)' : 'var(--success)' }}>
                                    <svg fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" /></svg>
                                </div>
                                <div>
                                    <div className="stat-label">Pending Constraints</div>
                                    <div className="stat-value" style={{ color: department_stats.pending_constraints > 0 ? 'var(--warning)' : 'var(--success)' }}>
                                        {department_stats.pending_constraints}
                                    </div>
                                </div>
                            </div>
                        </div>

                        <div className="card mt-4">
                            <div className="card-header">
                                <h2 className="card-title">Quick Actions</h2>
                            </div>
                            <div className="actions-grid" style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '1rem', padding: '1rem' }}>
                                <button onClick={() => setActiveTab('workload')} className="btn btn-secondary">📋 Review Workload</button>
                                <button onClick={() => setActiveTab('electives')} className="btn btn-secondary">🗂️ Manage Electives</button>
                                <button className="btn btn-primary" style={{ opacity: 0.6, cursor: 'not-allowed' }} title="HOD cannot run scheduler">⚡ Request Schedule Run</button>
                            </div>
                        </div>
                    </div>
                );
            case 'workload':
                return (
                    <div className="tab-pane">
                        <div className="search-bar-container">
                            <input
                                type="text"
                                className="search-input"
                                placeholder="Search faculty by name or ID..."
                                value={searchTerm}
                                onChange={(e) => setSearchTerm(e.target.value)}
                            />
                        </div>
                        <div className="card">
                            <div className="card-header">
                                <h2 className="card-title">Workload Distribution</h2>
                            </div>
                            <WorkloadChart facultyData={filteredFaculty} />
                        </div>

                        <div className="card mt-4">
                            <div className="card-header">
                                <h2 className="card-title">Detailed Workload Review</h2>
                            </div>
                            <div className="table-container">
                                <table className="data-table">
                                    <thead>
                                        <tr>
                                            <th>Faculty Name</th>
                                            <th>Load Status</th>
                                            <th>Hours</th>
                                            <th>Action</th>
                                        </tr>
                                    </thead>
                                    <tbody>
                                        {filteredFaculty.map((faculty) => {
                                            const hasPending = availabilities.some(a => a.teacher === faculty.id && a.status === 'PENDING');
                                            const isExpanded = expandedFaculty === faculty.id;
                                            const isOverloaded = faculty.assigned_hours > faculty.max_hours;

                                            return (
                                                <React.Fragment key={faculty.id}>
                                                    <tr onClick={() => toggleFaculty(faculty.id)} style={{ cursor: 'pointer' }}>
                                                        <td>
                                                            <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                                                                <span style={{ transition: 'transform 0.2s', transform: isExpanded ? 'rotate(90deg)' : 'rotate(0)' }}>▶</span>
                                                                <strong>{faculty.name}</strong>
                                                            </div>
                                                        </td>
                                                        <td>
                                                            <span className={`badge ${isOverloaded ? 'badge-pending' : 'badge-approved'}`} style={{ background: isOverloaded ? '#fee2e2' : '', color: isOverloaded ? '#991b1b' : '' }}>
                                                                {isOverloaded ? 'Overloaded' : 'Normal'}
                                                            </span>
                                                        </td>
                                                        <td>{faculty.assigned_hours} / {faculty.max_hours}</td>
                                                        <td>
                                                            <button className="btn btn-secondary" style={{ padding: '0.2rem 0.5rem', fontSize: '0.75rem' }}>
                                                                {isExpanded ? 'Hide' : 'Review'}
                                                            </button>
                                                        </td>
                                                    </tr>
                                                    {isExpanded && (
                                                        <tr style={{ background: 'var(--bg-secondary)' }}>
                                                            <td colSpan="4" style={{ padding: '1rem' }}>
                                                                <div className="breakdown-container">
                                                                    <h4 style={{ fontSize: '0.85rem', marginBottom: '0.5rem', color: 'var(--text-secondary)' }}>Assignment Breakdown:</h4>
                                                                    {faculty.assignments && faculty.assignments.length > 0 ? (
                                                                        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(200px, 1fr))', gap: '0.75rem' }}>
                                                                            {faculty.assignments.map((asm, idx) => (
                                                                                <div key={idx} className="card" style={{ padding: '0.75rem', marginBottom: 0, border: '1px solid var(--border)' }}>
                                                                                    <div style={{ fontSize: '0.85rem', fontWeight: 'bold' }}>{asm.course_name}</div>
                                                                                    <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>Section: {asm.section}</div>
                                                                                    <div style={{ fontSize: '0.75rem', marginTop: '0.25rem' }}>
                                                                                        <span className="badge badge-approved" style={{ fontSize: '0.7rem' }}>{asm.hours} Hours</span>
                                                                                    </div>
                                                                                </div>
                                                                            ))}
                                                                        </div>
                                                                    ) : (
                                                                        <p style={{ fontSize: '0.85rem', fontStyle: 'italic', color: 'var(--text-muted)' }}>No assignments found for published schedules.</p>
                                                                    )}
                                                                </div>
                                                            </td>
                                                        </tr>
                                                    )}
                                                </React.Fragment>
                                            );
                                        })}
                                    </tbody>
                                </table>
                            </div>
                        </div>
                    </div>
                );
            case 'electives':
                return (
                    <div className="tab-pane">
                        <div className="card">
                            <div className="card-header">
                                <h2 className="card-title">Elective Buckets</h2>
                                <button className="btn btn-primary btn-sm">+ Create Bucket</button>
                            </div>
                            <div style={{ padding: '1rem' }}>
                                {buckets.length === 0 ? (
                                    <div className="loading">No elective buckets defined for this department.</div>
                                ) : (
                                    <div className="buckets-grid">
                                        {buckets.map(bucket => (
                                            <div key={bucket.id} className="bucket-card">
                                                <h3 style={{ fontSize: '1.1rem', marginBottom: '1rem', color: 'var(--primary)' }}>{bucket.name}</h3>
                                                <div className="course-tags">
                                                    {bucket.course_details?.map(c => (
                                                        <span key={c.course_id} className="course-tag">
                                                            <strong>{c.course_id}</strong>: {c.course_name}
                                                        </span>
                                                    ))}
                                                </div>
                                            </div>
                                        ))}
                                    </div>
                                )}
                            </div>
                        </div>
                    </div>
                );
            case 'schedule':
                return (
                    <div className="tab-pane">
                        <div className="card">
                            <div className="card-header">
                                <h2 className="card-title">Department Timetable Audit</h2>
                            </div>
                            <div style={{ padding: '2rem', textAlign: 'center' }}>
                                <p>Select a schedule snapshot to review.</p>
                                <select className="filter-select" style={{ maxWidth: '300px', margin: '1rem auto' }}>
                                    <option>Spring 2026 - Main v1.0 [LATEST]</option>
                                    <option>Spring 2026 - Draft v0.9</option>
                                </select>
                                <div style={{ background: 'var(--bg-secondary)', padding: '2.5rem', border: '2px dashed var(--border)', borderRadius: '12px', marginTop: '1rem' }}>
                                    <p style={{ color: 'var(--secondary)', marginBottom: '1rem' }}>Interactive Master Grid View</p>
                                    <div style={{ fontSize: '0.85rem', color: 'var(--text-muted)' }}>
                                        Filtered by Department: <strong>{department_stats.department}</strong>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>
                );
            default:
                return null;
        }
    };

    return (
        <div className="dashboard-container">
            <div className="page-header">
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', flexWrap: 'wrap', gap: '1rem' }}>
                    <div>
                        <h1 className="page-title">{department_stats.department} HOD Dashboard</h1>
                        <p className="page-description">Academic Oversight & Workload Auditor</p>
                    </div>
                    <div className="tab-nav" style={{ display: 'flex', gap: '0.25rem', background: 'var(--bg-tertiary)', padding: '0.25rem', borderRadius: 'var(--radius-md)' }}>
                        <button onClick={() => setActiveTab('overview')} className={`nav-link ${activeTab === 'overview' ? 'active' : ''}`} style={tabOverride(activeTab === 'overview')}>Overview</button>
                        <button onClick={() => setActiveTab('workload')} className={`nav-link ${activeTab === 'workload' ? 'active' : ''}`} style={tabOverride(activeTab === 'workload')}>Faculty Load</button>
                        <button onClick={() => setActiveTab('electives')} className={`nav-link ${activeTab === 'electives' ? 'active' : ''}`} style={tabOverride(activeTab === 'electives')}>Electives</button>
                        <button onClick={() => setActiveTab('schedule')} className={`nav-link ${activeTab === 'schedule' ? 'active' : ''}`} style={tabOverride(activeTab === 'schedule')}>Schedule Review</button>
                    </div>
                </div>
            </div>

            <main style={{ marginTop: '1rem' }}>
                {renderTabContent()}
            </main>
        </div>
    );
};

const tabOverride = (isActive) => ({
    padding: '0.5rem 1rem',
    fontSize: '0.85rem',
    border: 'none',
    boxShadow: isActive ? 'var(--shadow-sm)' : 'none'
});

export default HODDashboard;
