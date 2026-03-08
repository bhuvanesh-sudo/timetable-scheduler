/**
 * Teacher Requests Page (HOD Only)
 * 
 * Submit teacher modification requests for Admin approval
 */

import { useState, useEffect } from 'react';
import { useAuth } from '../context/AuthContext';
import { teacherAPI, changeRequestAPI, courseAPI, sectionAPI, teacherCourseMappingAPI } from '../services/api';

function TeacherRequests() {
    const { user } = useAuth();
    const [teachers, setTeachers] = useState([]);
    const [courses, setCourses] = useState([]);
    const [sections, setSections] = useState([]);
    const [mappings, setMappings] = useState([]);
    const [newMapping, setNewMapping] = useState({ course_id: '', section_id: '' });
    const [myRequests, setMyRequests] = useState([]);
    const [loading, setLoading] = useState(true);
    const [showForm, setShowForm] = useState(false);
    const [formMode, setFormMode] = useState('CREATE'); // CREATE, UPDATE, DELETE
    const [selectedTeacher, setSelectedTeacher] = useState(null);
    const [formData, setFormData] = useState({
        teacher_id: '',
        teacher_name: '',
        email: '',
        department: user?.department || '',
        max_hours_per_week: 20,
    });
    const [requestNotes, setRequestNotes] = useState('');

    useEffect(() => {
        loadData();
    }, [user]);

    const loadData = async () => {
        if (!user || !user.department) return;
        try {
            const [teachersRes, requestsRes, coursesRes, sectionsRes] = await Promise.all([
                teacherAPI.byDepartment(user.department),
                changeRequestAPI.getAll(),
                courseAPI.byDepartment(user.department),
                sectionAPI.byDepartment(user.department),
            ]);
            setTeachers(teachersRes.data.results || teachersRes.data);
            setMyRequests(requestsRes.data.results || requestsRes.data);
            setCourses(coursesRes.data.results || coursesRes.data);
            setSections(sectionsRes.data.results || sectionsRes.data);
        } catch (error) {
            console.error('Error loading data:', error);
        } finally {
            setLoading(false);
        }
    };

    const handleCreateRequest = () => {
        setFormMode('CREATE');
        setFormData({
            teacher_id: '',
            teacher_name: '',
            email: '',
            department: user.department,
            max_hours_per_week: 20,
        });
        setMappings([]);
        setNewMapping({ course_id: '', section_id: '' });
        setRequestNotes('');
        setShowForm(true);
    };

    const handleEditRequest = async (teacher) => {
        setFormMode('UPDATE');
        setSelectedTeacher(teacher);
        setFormData({
            teacher_id: teacher.teacher_id,
            teacher_name: teacher.teacher_name,
            email: teacher.email,
            department: teacher.department,
            max_hours_per_week: teacher.max_hours_per_week,
        });
        setMappings([]);
        setNewMapping({ course_id: '', section_id: '' });
        setRequestNotes('');
        setShowForm(true);

        // Fetch current mappings
        try {
            const res = await teacherCourseMappingAPI.byTeacher(teacher.teacher_id);
            setMappings(res.data.results || res.data);
        } catch (error) {
            console.error('Error fetching mappings:', error);
        }
    };

    const handleDeleteRequest = (teacher) => {
        setFormMode('DELETE');
        setSelectedTeacher(teacher);
        setMappings([]);
        setRequestNotes('');
        setShowForm(true);
    };

    const addMapping = () => {
        if (!newMapping.course_id || !newMapping.section_id) return;

        // Prevent duplicates in local state
        const exists = mappings.find(m => m.course_id === newMapping.course_id && m.section_id === newMapping.section_id);
        if (exists) {
            alert('This course-section assignment already exists.');
            return;
        }

        const course = courses.find(c => c.course_id === newMapping.course_id);
        const section = sections.find(s => s.class_id === newMapping.section_id);

        if (!course || !section) return;

        setMappings([...mappings, {
            course: course.course_id,
            course_name: course.course_name,
            section: section.class_id,
            section_name: section.class_id,
            preference_level: 3
        }]);
        setNewMapping({ course_id: '', section_id: '' });
    };

    const removeMapping = (index) => {
        const newMappings = [...mappings];
        newMappings.splice(index, 1);
        setMappings(newMappings);
    };

    const submitRequest = async () => {
        try {
            const requestData = {
                target_model: 'Teacher',
                target_id: formMode === 'CREATE' ? null : selectedTeacher.teacher_id,
                change_type: formMode,
                proposed_data: {
                    ...formData,
                    mappings: mappings.map(m => ({
                        course_id: m.course || m.course_id,
                        section_id: m.section || m.section_id || m.class_id,
                        preference_level: m.preference_level || 3
                    }))
                },
                current_data: formMode === 'CREATE' ? null : selectedTeacher,
                request_notes: requestNotes,
            };

            await changeRequestAPI.create(requestData);
            alert('Request submitted successfully! Waiting for Admin approval.');
            setShowForm(false);
            loadData();
        } catch (error) {
            console.error('Error submitting request:', error);
            alert('Failed to submit request: ' + (error.response?.data?.error || error.message));
        }
    };

    if (loading) return <div className="loading-spinner">Loading...</div>;

    return (
        <div className="teacher-requests-page">
            <div className="page-header">
                <h1 className="page-title">Faculty Management ({user.department})</h1>
                <p className="page-description">Submit faculty modification requests for Admin approval.</p>
            </div>

            <div style={{ marginBottom: '2rem' }}>
                <button onClick={handleCreateRequest} className="btn btn-primary">
                    + Request New Teacher
                </button>
            </div>

            {/* Current Teachers */}
            <div className="card" style={{ marginBottom: '2rem' }}>
                <h2 className="card-title">Department Teachers</h2>
                <div className="table-container">
                    <table className="data-table" style={{ width: '100%', borderCollapse: 'collapse' }}>
                        <thead>
                            <tr style={{ background: '#f8f9fa', textAlign: 'left' }}>
                                <th style={{ padding: '12px', borderBottom: '2px solid #ddd' }}>ID</th>
                                <th style={{ padding: '12px', borderBottom: '2px solid #ddd' }}>Name</th>
                                <th style={{ padding: '12px', borderBottom: '2px solid #ddd' }}>Email</th>
                                <th style={{ padding: '12px', borderBottom: '2px solid #ddd' }}>Max Hours/Week</th>
                                <th style={{ padding: '12px', borderBottom: '2px solid #ddd' }}>Actions</th>
                            </tr>
                        </thead>
                        <tbody>
                            {teachers.map((teacher) => (
                                <tr key={teacher.teacher_id} style={{ borderBottom: '1px solid #eee' }}>
                                    <td style={{ padding: '12px' }}>{teacher.teacher_id}</td>
                                    <td style={{ padding: '12px', fontWeight: '500' }}>{teacher.teacher_name}</td>
                                    <td style={{ padding: '12px' }}>{teacher.email}</td>
                                    <td style={{ padding: '12px' }}>{teacher.max_hours_per_week}</td>
                                    <td style={{ padding: '12px' }}>
                                        <button
                                            onClick={() => handleEditRequest(teacher)}
                                            className="btn btn-sm btn-secondary"
                                            style={{ padding: '0.25rem 0.5rem', marginRight: '0.5rem' }}
                                        >
                                            Request Edit
                                        </button>
                                        <button
                                            onClick={() => handleDeleteRequest(teacher)}
                                            className="btn btn-sm btn-danger"
                                            style={{ padding: '0.25rem 0.5rem' }}
                                        >
                                            Request Delete
                                        </button>
                                    </td>
                                </tr>
                            ))}
                        </tbody>
                    </table>
                </div>
            </div>

            {/* My Requests */}
            <div className="card">
                <h2 className="card-title">My Pending Requests</h2>
                {myRequests.filter(r => r.status === 'PENDING').length === 0 ? (
                    <p>No pending requests.</p>
                ) : (
                    <div className="table-container">
                        <table className="data-table" style={{ width: '100%', borderCollapse: 'collapse' }}>
                            <thead>
                                <tr style={{ background: '#f8f9fa', textAlign: 'left' }}>
                                    <th style={{ padding: '12px', borderBottom: '2px solid #ddd' }}>Type</th>
                                    <th style={{ padding: '12px', borderBottom: '2px solid #ddd' }}>Target</th>
                                    <th style={{ padding: '12px', borderBottom: '2px solid #ddd' }}>Status</th>
                                    <th style={{ padding: '12px', borderBottom: '2px solid #ddd' }}>Submitted</th>
                                </tr>
                            </thead>
                            <tbody>
                                {myRequests.filter(r => r.status === 'PENDING').map((req) => (
                                    <tr key={req.id} style={{ borderBottom: '1px solid #eee' }}>
                                        <td style={{ padding: '12px' }}>
                                            <span className={`badge ${req.change_type === 'CREATE' ? 'bg-success' : req.change_type === 'UPDATE' ? 'bg-warning' : 'bg-danger'}`}>
                                                {req.change_type}
                                            </span>
                                        </td>
                                        <td style={{ padding: '12px' }}>
                                            {req.target_model} {req.target_id || '(New)'}
                                        </td>
                                        <td style={{ padding: '12px' }}>
                                            <span className="badge bg-warning">{req.status}</span>
                                        </td>
                                        <td style={{ padding: '12px', fontSize: '0.875rem' }}>
                                            {new Date(req.created_at).toLocaleDateString()}
                                        </td>
                                    </tr>
                                ))}
                            </tbody>
                        </table>
                    </div>
                )}
            </div>

            {/* Request Form Modal */}
            {showForm && (
                <div className="modal-overlay" style={{ position: 'fixed', top: 0, left: 0, right: 0, bottom: 0, background: 'rgba(0,0,0,0.5)', display: 'flex', alignItems: 'center', justifyContent: 'center', zIndex: 1000 }}>
                    <div className="modal-content" style={{ background: 'white', padding: '2rem', borderRadius: '8px', maxWidth: '600px', width: '90%' }}>
                        <h2>{formMode} Teacher Request</h2>

                        {formMode !== 'DELETE' ? (
                            <div>
                                <div style={{ marginBottom: '1rem' }}>
                                    <label style={{ display: 'block', marginBottom: '0.5rem', fontWeight: '500' }}>Teacher ID:</label>
                                    <input
                                        type="text"
                                        value={formData.teacher_id}
                                        onChange={(e) => setFormData({ ...formData, teacher_id: e.target.value })}
                                        disabled={formMode === 'UPDATE'}
                                        style={{ width: '100%', padding: '0.5rem', border: '1px solid #ddd', borderRadius: '4px' }}
                                    />
                                </div>
                                <div style={{ marginBottom: '1rem' }}>
                                    <label style={{ display: 'block', marginBottom: '0.5rem', fontWeight: '500' }}>Name:</label>
                                    <input
                                        type="text"
                                        value={formData.teacher_name}
                                        onChange={(e) => setFormData({ ...formData, teacher_name: e.target.value })}
                                        style={{ width: '100%', padding: '0.5rem', border: '1px solid #ddd', borderRadius: '4px' }}
                                    />
                                </div>
                                <div style={{ marginBottom: '1rem' }}>
                                    <label style={{ display: 'block', marginBottom: '0.5rem', fontWeight: '500' }}>Email:</label>
                                    <input
                                        type="email"
                                        value={formData.email}
                                        onChange={(e) => setFormData({ ...formData, email: e.target.value })}
                                        style={{ width: '100%', padding: '0.5rem', border: '1px solid #ddd', borderRadius: '4px' }}
                                    />
                                </div>
                                <div style={{ marginBottom: '1rem' }}>
                                    <label style={{ display: 'block', marginBottom: '0.5rem', fontWeight: '500' }}>Max Hours/Week:</label>
                                    <input
                                        type="number"
                                        value={formData.max_hours_per_week}
                                        onChange={(e) => setFormData({ ...formData, max_hours_per_week: parseInt(e.target.value) })}
                                        min="0"
                                        max="40"
                                        style={{ width: '100%', padding: '0.5rem', border: '1px solid #ddd', borderRadius: '4px' }}
                                    />
                                </div>

                                <div style={{ borderTop: '1px solid #eee', marginTop: '1.5rem', paddingTop: '1.5rem' }}>
                                    <h3 style={{ fontSize: '1.1rem', marginBottom: '1rem' }}>Course Assignments</h3>

                                    <div style={{ background: '#f8f9fa', padding: '1rem', borderRadius: '4px', marginBottom: '1rem' }}>
                                        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr auto', gap: '0.5rem', alignItems: 'end' }}>
                                            <div>
                                                <label style={{ display: 'block', fontSize: '0.8rem', marginBottom: '0.25rem' }}>Course</label>
                                                <select
                                                    value={newMapping.course_id}
                                                    onChange={(e) => setNewMapping({ ...newMapping, course_id: e.target.value })}
                                                    style={{ width: '100%', padding: '0.4rem', border: '1px solid #ddd', borderRadius: '4px' }}
                                                >
                                                    <option value="">Select Course</option>
                                                    {courses.map(c => (
                                                        <option key={c.course_id} value={c.course_id}>{c.course_id} - {c.course_name}</option>
                                                    ))}
                                                </select>
                                            </div>
                                            <div>
                                                <label style={{ display: 'block', fontSize: '0.8rem', marginBottom: '0.25rem' }}>Section</label>
                                                <select
                                                    value={newMapping.section_id}
                                                    onChange={(e) => setNewMapping({ ...newMapping, section_id: e.target.value })}
                                                    style={{ width: '100%', padding: '0.4rem', border: '1px solid #ddd', borderRadius: '4px' }}
                                                >
                                                    <option value="">Select Section</option>
                                                    {sections.map(s => (
                                                        <option key={s.class_id} value={s.class_id}>{s.class_id} (Yr {s.year})</option>
                                                    ))}
                                                </select>
                                            </div>
                                            <button
                                                type="button"
                                                onClick={addMapping}
                                                className="btn btn-sm btn-primary"
                                                style={{ height: '36px' }}
                                            >
                                                Add
                                            </button>
                                        </div>
                                    </div>

                                    <div className="mapping-list">
                                        {mappings.length === 0 ? (
                                            <p style={{ color: '#666', fontStyle: 'italic', fontSize: '0.9rem' }}>No courses assigned yet.</p>
                                        ) : (
                                            <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.9rem' }}>
                                                <thead>
                                                    <tr style={{ textAlign: 'left', borderBottom: '1px solid #ddd' }}>
                                                        <th style={{ padding: '0.5rem' }}>Course</th>
                                                        <th style={{ padding: '0.5rem' }}>Section</th>
                                                        <th style={{ padding: '0.5rem' }}>Action</th>
                                                    </tr>
                                                </thead>
                                                <tbody>
                                                    {mappings.map((m, idx) => (
                                                        <tr key={idx} style={{ borderBottom: '1px solid #eee' }}>
                                                            <td style={{ padding: '0.5rem' }}>{m.course}</td>
                                                            <td style={{ padding: '0.5rem' }}>{m.section_name || m.section}</td>
                                                            <td style={{ padding: '0.5rem' }}>
                                                                <button
                                                                    onClick={() => removeMapping(idx)}
                                                                    style={{ background: 'none', border: 'none', color: '#e74c3c', cursor: 'pointer', padding: 0 }}
                                                                >
                                                                    Remove
                                                                </button>
                                                            </td>
                                                        </tr>
                                                    ))}
                                                </tbody>
                                            </table>
                                        )}
                                    </div>
                                </div>
                            </div>
                        ) : (
                            <div style={{ padding: '1rem', background: '#fff3cd', borderRadius: '4px', marginBottom: '1rem' }}>
                                <strong>Warning:</strong> You are requesting to delete teacher <strong>{selectedTeacher?.teacher_name}</strong> ({selectedTeacher?.teacher_id}).
                            </div>
                        )}

                        <div style={{ marginBottom: '1rem' }}>
                            <label style={{ display: 'block', marginBottom: '0.5rem', fontWeight: '500' }}>Reason for Request:</label>
                            <textarea
                                value={requestNotes}
                                onChange={(e) => setRequestNotes(e.target.value)}
                                placeholder="Explain why this change is needed..."
                                style={{ width: '100%', padding: '0.5rem', border: '1px solid #ddd', borderRadius: '4px', minHeight: '80px' }}
                            />
                        </div>

                        <div style={{ display: 'flex', gap: '1rem', justifyContent: 'flex-end' }}>
                            <button onClick={submitRequest} className="btn btn-primary">
                                Submit Request
                            </button>
                            <button onClick={() => setShowForm(false)} className="btn btn-secondary">
                                Cancel
                            </button>
                        </div>
                    </div>
                </div>
            )}
        </div>
    );
}

export default TeacherRequests;
