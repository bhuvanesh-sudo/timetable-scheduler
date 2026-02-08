/**
 * Data Management Page - View and manage system data
 * 
 * Author: Frontend Team (Bhuvanesh, Akshitha)
 */

import { useState, useEffect } from 'react';
import { teacherAPI, courseAPI, roomAPI, sectionAPI } from '../services/api';

function DataManagement() {
    const [activeTab, setActiveTab] = useState('teachers');
    const [teachers, setTeachers] = useState([]);
    const [courses, setCourses] = useState([]);
    const [rooms, setRooms] = useState([]);
    const [sections, setSections] = useState([]);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        loadData();
    }, []);

    const loadData = async () => {
        try {
            const [teachersRes, coursesRes, roomsRes, sectionsRes] = await Promise.all([
                teacherAPI.getAll(),
                courseAPI.getAll(),
                roomAPI.getAll(),
                sectionAPI.getAll(),
            ]);

            setTeachers(teachersRes.data.results || []);
            setCourses(coursesRes.data.results || []);
            setRooms(roomsRes.data.results || []);
            setSections(sectionsRes.data.results || []);
        } catch (error) {
            console.error('Error loading data:', error);
        } finally {
            setLoading(false);
        }
    };

    if (loading) {
        return (
            <div className="loading">
                <div className="spinner"></div>
                <p>Loading data...</p>
            </div>
        );
    }

    return (
        <div>
            <div className="page-header">
                <h1 className="page-title">Data Management</h1>
                <p className="page-description">View and manage system data</p>
            </div>

            {/* Tabs */}
            <div className="card">
                <div style={{ display: 'flex', gap: '1rem', marginBottom: '1.5rem', borderBottom: '1px solid var(--border)', paddingBottom: '1rem' }}>
                    <button
                        className={`btn ${activeTab === 'teachers' ? 'btn-primary' : 'btn-secondary'}`}
                        onClick={() => setActiveTab('teachers')}
                    >
                        Teachers ({teachers.length})
                    </button>
                    <button
                        className={`btn ${activeTab === 'courses' ? 'btn-primary' : 'btn-secondary'}`}
                        onClick={() => setActiveTab('courses')}
                    >
                        Courses ({courses.length})
                    </button>
                    <button
                        className={`btn ${activeTab === 'rooms' ? 'btn-primary' : 'btn-secondary'}`}
                        onClick={() => setActiveTab('rooms')}
                    >
                        Rooms ({rooms.length})
                    </button>
                    <button
                        className={`btn ${activeTab === 'sections' ? 'btn-primary' : 'btn-secondary'}`}
                        onClick={() => setActiveTab('sections')}
                    >
                        Sections ({sections.length})
                    </button>
                </div>

                {/* Teachers Tab */}
                {activeTab === 'teachers' && (
                    <div className="table-container">
                        <table className="data-table">
                            <thead>
                                <tr>
                                    <th>Teacher ID</th>
                                    <th>Name</th>
                                    <th>Email</th>
                                    <th>Department</th>
                                    <th>Max Hours/Week</th>
                                </tr>
                            </thead>
                            <tbody>
                                {teachers.map((teacher) => (
                                    <tr key={teacher.teacher_id}>
                                        <td>{teacher.teacher_id}</td>
                                        <td>{teacher.teacher_name}</td>
                                        <td>{teacher.email}</td>
                                        <td>{teacher.department}</td>
                                        <td>{teacher.max_hours_per_week}</td>
                                    </tr>
                                ))}
                            </tbody>
                        </table>
                    </div>
                )}

                {/* Courses Tab */}
                {activeTab === 'courses' && (
                    <div className="table-container">
                        <table className="data-table">
                            <thead>
                                <tr>
                                    <th>Course ID</th>
                                    <th>Course Name</th>
                                    <th>Year</th>
                                    <th>Semester</th>
                                    <th>Credits</th>
                                    <th>Weekly Slots</th>
                                    <th>Type</th>
                                </tr>
                            </thead>
                            <tbody>
                                {courses.map((course) => (
                                    <tr key={course.course_id}>
                                        <td>{course.course_id}</td>
                                        <td>{course.course_name}</td>
                                        <td>{course.year}</td>
                                        <td>{course.semester}</td>
                                        <td>{course.credits}</td>
                                        <td>{course.weekly_slots}</td>
                                        <td>
                                            {course.is_lab ? '🔬 Lab' : '📚 Theory'}
                                            {course.is_elective && ' (Elective)'}
                                        </td>
                                    </tr>
                                ))}
                            </tbody>
                        </table>
                    </div>
                )}

                {/* Rooms Tab */}
                {activeTab === 'rooms' && (
                    <div className="table-container">
                        <table className="data-table">
                            <thead>
                                <tr>
                                    <th>Room ID</th>
                                    <th>Block</th>
                                    <th>Floor</th>
                                    <th>Type</th>
                                </tr>
                            </thead>
                            <tbody>
                                {rooms.map((room) => (
                                    <tr key={room.room_id}>
                                        <td>{room.room_id}</td>
                                        <td>{room.block}</td>
                                        <td>{room.floor}</td>
                                        <td>{room.room_type}</td>
                                    </tr>
                                ))}
                            </tbody>
                        </table>
                    </div>
                )}

                {/* Sections Tab */}
                {activeTab === 'sections' && (
                    <div className="table-container">
                        <table className="data-table">
                            <thead>
                                <tr>
                                    <th>Class ID</th>
                                    <th>Year</th>
                                    <th>Section</th>
                                    <th>Semester</th>
                                    <th>Department</th>
                                </tr>
                            </thead>
                            <tbody>
                                {sections.map((section) => (
                                    <tr key={section.class_id}>
                                        <td>{section.class_id}</td>
                                        <td>{section.year}</td>
                                        <td>{section.section}</td>
                                        <td>{section.sem}</td>
                                        <td>{section.department}</td>
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

export default DataManagement;
