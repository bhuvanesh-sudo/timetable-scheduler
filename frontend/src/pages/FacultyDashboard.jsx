/**
 * Faculty Dashboard - My Schedule
 * 
 * Shows the authenticated faculty member's schedule.
 * Automatically filters by the linked Teacher record.
 */

import { useState, useEffect } from 'react';
import { facultyAPI } from '../services/api';

function FacultyDashboard() {
    const [timetable, setTimetable] = useState(null);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState(null);

    const days = ['MON', 'TUE', 'WED', 'THU', 'FRI'];
    const slots = [1, 2, 3, 4, 5, 6, 7, 8];

    useEffect(() => {
        loadMySchedule();
    }, []);

    // Fetch schedule for the logged-in faculty
    const loadMySchedule = async () => {
        setLoading(true);
        setError(null);
        try {
            // Pass null to let backend decide the latest schedule
            const response = await facultyAPI.getMySchedule(null);

            if (response.data.timetable) {
                setTimetable(response.data.timetable);
            } else {
                setTimetable(null);
                setError("No timetable data found.");
            }
        } catch (err) {
            console.error('Error loading my schedule:', err);
            if (err.response?.status === 400 && err.response?.data?.error?.includes('No teacher record')) {
                setError("Your account is not linked to a Teacher record. Please contact the administrator.");
            } else if (err.response?.status === 404) {
                setError("No generated schedules found.");
            } else {
                setError("Failed to load timetable.");
            }
            setTimetable(null);
        } finally {
            setLoading(false);
        }
    };

    return (
        <div>
            <div className="page-header">
                <h1 className="page-title">My Schedule</h1>
                <p className="page-description">View your assigned classes and labs</p>
            </div>

            {/* Error Message */}
            {error && (
                <div className="alert alert-danger">
                    {error}
                </div>
            )}

            {/* Timetable Grid */}
            {loading && (
                <div className="loading">
                    <div className="spinner"></div>
                    <p>Loading your schedule...</p>
                </div>
            )}

            {!loading && timetable && (
                <div className="card">
                    <div className="card-header">
                        <h2 className="card-title">Weekly Timetable</h2>
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
                                                    <span style={{ marginLeft: '5px', opacity: 0.8 }}>
                                                        ({classItem.section})
                                                    </span>
                                                    {classItem.is_lab_session && <span className="lab-badge">LAB</span>}
                                                </div>
                                                <div className="class-teacher" style={{ fontWeight: 'bold' }}>
                                                    {classItem.course_name}
                                                </div>
                                                <div className="class-room">Room: {classItem.room}</div>
                                                <div className="class-time">
                                                    {classItem.start_time} - {classItem.end_time}
                                                </div>
                                            </div>
                                        ))}
                                    </div>
                                ))}
                            </>
                        ))}
                    </div>
                </div>
            )}

            {!loading && !timetable && !error && (
                <div className="alert alert-info">
                    No classes found for this schedule.
                </div>
            )}
        </div>
    );
}

export default FacultyDashboard;
