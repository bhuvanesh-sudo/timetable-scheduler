/**
 * View Timetable Page
 * 
 * Author: Frontend Team (Bhuvanesh, Akshitha)
 */

import { useState, useEffect } from 'react';
import { scheduleAPI, schedulerAPI, sectionAPI } from '../services/api';

function ViewTimetable() {
    const [schedules, setSchedules] = useState([]);
    const [sections, setSections] = useState([]);
    const [selectedSchedule, setSelectedSchedule] = useState('');
    const [selectedSection, setSelectedSection] = useState('');
    const [timetable, setTimetable] = useState(null);
    const [loading, setLoading] = useState(false);

    const days = ['MON', 'TUE', 'WED', 'THU', 'FRI'];
    const slots = [1, 2, 3, 4, 5, 6, 7, 8];

    useEffect(() => {
        loadInitialData();
    }, []);

    const loadInitialData = async () => {
        try {
            const [schedulesRes, sectionsRes] = await Promise.all([
                scheduleAPI.getAll(),
                sectionAPI.getAll(),
            ]);
            setSchedules(schedulesRes.data.results || []);
            setSections(sectionsRes.data.results || []);
        } catch (error) {
            console.error('Error loading data:', error);
        }
    };

    const loadTimetable = async () => {
        if (!selectedSchedule) return;

        setLoading(true);
        try {
            const response = await schedulerAPI.getTimetable(
                selectedSchedule,
                selectedSection || null
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
    }, [selectedSchedule, selectedSection]);

    return (
        <div>
            <div className="page-header">
                <h1 className="page-title">View Timetable</h1>
                <p className="page-description">View generated timetable schedules</p>
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
                                    All Years, {schedule.semester}
                                </option>
                            ))}
                        </select>
                    </div>

                    <div className="filter-group">
                        <label className="filter-label">Filter by Section (Optional)</label>
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
                        <h2 className="card-title">Timetable Grid</h2>
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
                                                className={`class-block ${classItem.is_lab_session ? 'lab' : 'theory'}`}
                                            >
                                                <div className="class-code">
                                                    {classItem.course_code}
                                                    {classItem.is_lab_session && <span className="lab-badge">LAB</span>}
                                                </div>
                                                <div className="class-teacher">{classItem.teacher_name}</div>
                                                <div className="class-room">Room: {classItem.room}</div>
                                                {selectedSection === '' && (
                                                    <div className="class-room">Sec: {classItem.section}</div>
                                                )}
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
                    No timetable data available for the selected schedule.
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
