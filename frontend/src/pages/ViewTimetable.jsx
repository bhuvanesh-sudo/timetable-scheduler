import { useState, useEffect } from 'react';
import { scheduleAPI, schedulerAPI, sectionAPI, teacherAPI, electiveAllocationAPI } from '../services/api';
import { useAuth } from '../context/AuthContext';

function ViewTimetable() {
    const { user } = useAuth();
    const [schedules, setSchedules] = useState([]);
    const [sections, setSections] = useState([]);
    const [teachers, setTeachers] = useState([]);
    const [allocations, setAllocations] = useState([]);

    const [selectedSchedule, setSelectedSchedule] = useState('');
    const [selectedSection, setSelectedSection] = useState('');
    const [selectedTeacher, setSelectedTeacher] = useState('');

    const [timetable, setTimetable] = useState(null);
    const [loading, setLoading] = useState(false);
    const [verificationResult, setVerificationResult] = useState(null);
    const [showVerificationModal, setShowVerificationModal] = useState(false);
    const [showAllocationsModal, setShowAllocationsModal] = useState(false);
    const [verifying, setVerifying] = useState(false);
    const [loadingAllocations, setLoadingAllocations] = useState(false);

    const days = ['MON', 'TUE', 'WED', 'THU', 'FRI'];
    const slots = [1, 2, 3, 4, 5, 6, 7, 8];

    useEffect(() => {
        loadInitialData();
    }, [user]); // Reload if user context changes

    useEffect(() => {
        if (user && user.role === 'FACULTY' && user.teacher_id) {
            setSelectedTeacher(user.teacher_id);
        }
    }, [user]);

    const loadInitialData = async () => {
        try {
            const promises = [
                scheduleAPI.getAll(),
                sectionAPI.getAll(),
            ];

            // Only Admins need to load all teachers
            if (user && (user.role === 'ADMIN' || user.role === 'HOD')) {
                promises.push(teacherAPI.getAll());
            }

            const [schedulesRes, sectionsRes, teachersRes] = await Promise.all(promises);

            setSchedules(schedulesRes.data.results || schedulesRes.data || []);
            setSections(sectionsRes.data.results || sectionsRes.data || []);
            if (teachersRes) {
                setTeachers(teachersRes.data.results || teachersRes.data || []);
            }

            // Auto-select latest schedule for Faculty
            if (user?.role === 'FACULTY' && !selectedSchedule) {
                const availableSchedules = schedulesRes.data.results || schedulesRes.data || [];
                if (availableSchedules.length > 0) {
                    setSelectedSchedule(availableSchedules[0].schedule_id);
                }
            }
        } catch (error) {
            console.error('Error loading data:', error);
        }
    };

    const loadTimetable = async () => {
        if (!selectedSchedule) return;

        setLoading(true);
        try {
            // If Faculty, force selectedTeacher to be their ID (security/UX)
            const teacherId = (user && user.role === 'FACULTY') ? user.teacher_id : selectedTeacher;

            const response = await schedulerAPI.getTimetable(
                selectedSchedule,
                selectedSection || null,
                teacherId || null
            );
            setTimetable(response.data);
        } catch (error) {
            console.error('Error loading timetable:', error);
        } finally {
            setLoading(false);
        }
    };

    const loadAllocations = async () => {
        if (!selectedSchedule) {
            alert("Please select a schedule first.");
            return;
        }
        setLoadingAllocations(true);
        try {
            // Use the new API for scheduled assignments
            const response = await schedulerAPI.getElectiveAssignments(selectedSchedule);
            setAllocations(response.data || []);
            setShowAllocationsModal(true);
        } catch (error) {
            console.error('Error loading assignments:', error);
            alert('Failed to load elective assignments');
        } finally {
            setLoadingAllocations(false);
        }
    };

    const handleVerifySchedule = async () => {
        if (!selectedSchedule) return;

        setVerifying(true);
        try {
            const response = await schedulerAPI.validateSchedule(selectedSchedule);
            setVerificationResult(response.data);
            setShowVerificationModal(true);
        } catch (error) {
            console.error('Verification failed:', error);
            alert('Failed to verify schedule');
        } finally {
            setVerifying(false);
        }
    };

    useEffect(() => {
        if (selectedSchedule) {
            loadTimetable();
        }
    }, [selectedSchedule, selectedSection, selectedTeacher]);

    return (
        <div className="fade-in">
            <div className="page-header">
                <h1 className="page-title">
                    {user?.role === 'FACULTY' ? 'My Timetable' : 'View Timetable'}
                </h1>
                <p className="page-description">
                    {user?.role === 'FACULTY'
                        ? `Viewing schedule for ${user.first_name} ${user.last_name}`
                        : 'View generated timetable schedules'}
                </p>
            </div>

            {/* Filters */}
            <div className="card">
                <div className="filters">
                    <div className="filter-group">
                        <label className="filter-label">Select Schedule</label>
                        <select
                            className="filter-select"
                            value={selectedSchedule}
                            onChange={(e) => setSelectedSchedule(e.target.value)}
                        >
                            <option value="">-- Select Schedule --</option>
                            {schedules.map((schedule) => (
                                <option key={schedule.schedule_id} value={schedule.schedule_id}>
                                    {schedule.name} (Year {schedule.year}, {schedule.semester})
                                </option>
                            ))}
                        </select>
                        {(selectedSchedule && (user?.role === 'ADMIN' || user?.role === 'HOD')) && (
                            <div style={{ display: 'flex', gap: '0.5rem', marginTop: '0.75rem', flexWrap: 'wrap' }}>
                                <button
                                    className="btn btn-success"
                                    onClick={handleVerifySchedule}
                                    disabled={verifying}
                                    style={{ flex: 1 }}
                                >
                                    {verifying ? 'Verifying...' : 'Verify Schedule'}
                                </button>
                                <button
                                    className="btn btn-info"
                                    onClick={loadAllocations}
                                    disabled={loadingAllocations}
                                    style={{ flex: 1 }}
                                >
                                    {loadingAllocations ? 'Loading...' : 'View scheduled Electives'}
                                </button>
                                <button
                                    className="btn btn-danger"
                                    onClick={async () => {
                                        if (window.confirm("Are you sure you want to delete this schedule?")) {
                                            try {
                                                await scheduleAPI.delete(selectedSchedule);
                                                alert("Schedule deleted successfully.");
                                                setSelectedSchedule('');
                                                setTimetable(null);
                                                loadInitialData();
                                            } catch (err) {
                                                alert("Error deleting schedule");
                                            }
                                        }
                                    }}
                                    style={{ flex: 1 }}
                                >
                                    Delete Schedule
                                </button>
                            </div>
                        )}
                    </div>

                    {/* Section Filter */}
                    <div className="filter-group">
                        <label className="filter-label">
                            {user?.role === 'FACULTY' ? 'Filter My Schedule by Section' : 'Filter by Section'}
                        </label>
                        <select
                            className="filter-select"
                            value={selectedSection}
                            onChange={(e) => setSelectedSection(e.target.value)}
                        >
                            <option value="">All Sections</option>
                            {sections.map((section) => (
                                <option key={section.class_id} value={section.class_id}>
                                    {section.class_id}
                                </option>
                            ))}
                        </select>
                    </div>

                    {/* Teacher Filter - Only for Admin */}
                    {(user?.role === 'ADMIN' || user?.role === 'HOD') && (
                        <div className="filter-group">
                            <label className="filter-label">Filter by Teacher (Optional)</label>
                            <select
                                className="filter-select"
                                value={selectedTeacher}
                                onChange={(e) => setSelectedTeacher(e.target.value)}
                            >
                                <option value="">All Teachers</option>
                                {teachers.map((teacher) => (
                                    <option key={teacher.teacher_id} value={teacher.teacher_id}>
                                        {teacher.teacher_name}
                                    </option>
                                ))}
                            </select>
                        </div>
                    )}
                </div>
            </div>

            {/* Timetable Grid */}
            {loading && (
                <div className="loading">
                    <div className="spinner"></div>
                    <p>Loading timetable...</p>
                </div>
            )}

            {!loading && timetable && (
                <div className="card">
                    <div className="card-header">
                        <h2 className="card-title">Weekly Schedule</h2>
                        <div style={{ display: 'flex', gap: '8px' }}>
                            {user?.role === 'FACULTY' && (
                                <span className="badge-pill badge-primary">Faculty View</span>
                            )}
                            {(selectedTeacher && user?.role !== 'FACULTY') && (
                                <span className="badge-pill badge-info">
                                    Teacher: {teachers.find(t => t.teacher_id === selectedTeacher)?.teacher_name || selectedTeacher}
                                </span>
                            )}
                        </div>
                    </div>

                    <div className="timetable-grid">
                        {/* Header Row */}
                        <div className="grid-header">Time</div>
                        {days.map((day) => (
                            <div key={day} className="grid-header">{day}</div>
                        ))}

                        {/* Time Slots */}
                        {slots.map((slot) => (
                            <>
                                <div key={`time-${slot}`} className="grid-time">
                                    <div>Slot {slot}</div>
                                </div>
                                {days.map((day) => (
                                    <div key={`${day}-${slot}`} className="grid-cell">
                                        {timetable[day]?.[slot]?.map((classItem, idx) => (
                                            <div
                                                key={idx}
                                                className={`class-block ${classItem.is_lab_session ? 'lab' : 'theory'} ${classItem.teacher_id === (user?.teacher_id || selectedTeacher) ? 'highlight-teacher' : ''}`}
                                            >
                                                <div className="class-code">
                                                    {classItem.course_code}
                                                    {classItem.is_lab_session && <span className="lab-badge">LAB</span>}
                                                </div>
                                                <div className="class-teacher">{classItem.teacher_name}</div>
                                                <div className="class-room">Room: {classItem.room}</div>
                                                <div className="class-room">Sec: {classItem.section}</div>
                                            </div>
                                        ))}
                                    </div>
                                ))}
                            </>
                        ))}
                    </div>
                </div>
            )}

            {!loading && !timetable && selectedSchedule && (
                <div className="alert alert-info">
                    {user?.role === 'FACULTY'
                        ? "You have no classes assigned in this schedule selection."
                        : "No timetable data available for this selection."}
                </div>
            )}

            {!selectedSchedule && (
                <div className="alert alert-info">
                    Please select a schedule to view the timetable.
                </div>
            )}

            {/* Verification Modal */}
            {showVerificationModal && verificationResult && (
                <div style={{
                    position: 'fixed', top: 0, left: 0, right: 0, bottom: 0,
                    background: 'rgba(0, 0, 0, 0.5)',
                    backdropFilter: 'blur(4px)',
                    WebkitBackdropFilter: 'blur(4px)',
                    display: 'flex', alignItems: 'center', justifyContent: 'center',
                    zIndex: 1000,
                    animation: 'fadeIn 0.3s ease-out',
                }}>
                    <div style={{
                        background: 'var(--card-bg)',
                        border: '1px solid var(--card-border)',
                        borderRadius: 'var(--radius-lg)',
                        boxShadow: 'var(--shadow-xl)',
                        padding: 'var(--spacing-lg)',
                        maxWidth: '480px',
                        width: '90%',
                        maxHeight: '80vh',
                        overflow: 'auto',
                    }}>
                        <h3 style={{
                            fontSize: '1.25rem',
                            fontWeight: 700,
                            color: 'var(--text-primary)',
                            marginBottom: '0.25rem',
                        }}>
                            {verificationResult.valid ? 'Schedule Verified' : 'Issues Detected'}
                        </h3>
                        <p style={{
                            color: 'var(--text-muted)',
                            fontSize: '0.875rem',
                            marginBottom: 'var(--spacing-md)',
                        }}>
                            {verificationResult.valid
                                ? 'No conflicts found. This schedule is ready to publish.'
                                : `${verificationResult.conflicts.length} conflict(s) need attention before publishing.`
                            }
                        </p>

                        {!verificationResult.valid && (
                            <div style={{
                                background: 'var(--bg-tertiary)',
                                borderRadius: 'var(--radius-md)',
                                padding: 'var(--spacing-sm) var(--spacing-md)',
                                marginBottom: 'var(--spacing-lg)',
                                maxHeight: '220px',
                                overflowY: 'auto',
                                border: '1px solid var(--border)',
                            }}>
                                {verificationResult.conflicts.map((conflict, idx) => (
                                    <div key={idx} style={{
                                        padding: '0.5rem 0',
                                        borderBottom: idx < verificationResult.conflicts.length - 1 ? '1px solid var(--border)' : 'none',
                                        fontSize: '0.85rem',
                                        color: 'var(--text-primary)',
                                    }}>
                                        {conflict}
                                    </div>
                                ))}
                            </div>
                        )}

                        <button
                            className="btn btn-primary"
                            onClick={() => setShowVerificationModal(false)}
                            style={{ width: '100%' }}
                        >
                            Close
                        </button>
                    </div>
                </div>
            )}

            {/* Elective Allocations Modal */}
            {showAllocationsModal && (
                <div style={{
                    position: 'fixed', top: 0, left: 0, right: 0, bottom: 0,
                    background: 'rgba(0, 0, 0, 0.5)',
                    backdropFilter: 'blur(4px)',
                    WebkitBackdropFilter: 'blur(4px)',
                    display: 'flex', alignItems: 'center', justifyContent: 'center',
                    zIndex: 1000,
                    animation: 'fadeIn 0.3s ease-out',
                }}>
                    <div style={{
                        background: 'var(--card-bg)',
                        border: '1px solid var(--card-border)',
                        borderRadius: 'var(--radius-lg)',
                        boxShadow: 'var(--shadow-xl)',
                        padding: 'var(--spacing-lg)',
                        maxWidth: '900px',
                        width: '95%',
                        maxHeight: '85vh',
                        overflow: 'auto',
                    }}>
                        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem' }}>
                            <h3 style={{ fontSize: '1.25rem', fontWeight: 700 }}>Scheduled Elective Classes</h3>
                            <button onClick={() => setShowAllocationsModal(false)} style={{ background: 'none', border: 'none', fontSize: '1.5rem', cursor: 'pointer' }}>&times;</button>
                        </div>

                        <div style={{ overflowX: 'auto' }}>
                            <table className="data-table" style={{ width: '100%', fontSize: '0.9rem' }}>
                                <thead>
                                    <tr>
                                        <th>Course</th>
                                        <th>Teacher</th>
                                        <th>Section/Group</th>
                                        <th>Room</th>
                                        <th>Day & Time</th>
                                    </tr>
                                </thead>
                                <tbody>
                                    {allocations.length > 0 ? (
                                        allocations.map((alloc, idx) => (
                                            <tr key={idx}>
                                                <td>
                                                    <div style={{ fontWeight: 600 }}>{alloc.course_code}</div>
                                                    <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>{alloc.course_name}</div>
                                                </td>
                                                <td>{alloc.teacher_name}</td>
                                                <td>{alloc.section}</td>
                                                <td>{alloc.room}</td>
                                                <td>{alloc.day} Slot {alloc.slot} <br /> <span style={{ fontSize: '0.8em' }}>({alloc.time})</span></td>
                                            </tr>
                                        ))
                                    ) : (
                                        <tr>
                                            <td colSpan="5" style={{ textAlign: 'center', padding: '2rem' }}>No scheduled elective assignments found for this schedule.</td>
                                        </tr>
                                    )}
                                </tbody>
                            </table>
                        </div>
                    </div>
                </div>
            )}
        </div>
    );
}

export default ViewTimetable;
