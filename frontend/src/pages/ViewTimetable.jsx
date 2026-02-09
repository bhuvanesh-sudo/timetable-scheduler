/**
 * View Timetable Page
 * 
 * Author: Frontend Team (Bhuvanesh, Akshitha)
 */

import { useState, useEffect } from 'react';
import { scheduleAPI, schedulerAPI, sectionAPI, teacherAPI } from '../services/api';
import { useAuth } from '../context/AuthContext';

function ViewTimetable() {
    const { user } = useAuth();
    const [schedules, setSchedules] = useState([]);
    const [sections, setSections] = useState([]);
    const [teachers, setTeachers] = useState([]);

    const [selectedSchedule, setSelectedSchedule] = useState('');
    const [selectedSection, setSelectedSection] = useState('');
    const [selectedTeacher, setSelectedTeacher] = useState('');

    const [timetable, setTimetable] = useState(null);
    const [loading, setLoading] = useState(false);

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
                                style={{ marginTop: '0.5rem', width: '100%' }}
                            >
                                Delete Schedule
                            </button>
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
        </div>
    );
}

export default ViewTimetable;
