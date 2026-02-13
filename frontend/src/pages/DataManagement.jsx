/**
 * Data Management Page - Full CRUD for system data
 * 
 * Features:
 * - Inline editing (click cells to edit)
 * - Bulk delete with checkboxes
 * - Add new records
 * 
 * Author: Frontend Team (Bhuvanesh, Akshitha)
 */

import { useState, useEffect } from 'react';
import { teacherAPI, courseAPI, roomAPI, sectionAPI, teacherCourseMappingAPI, timeslotAPI, electiveAllocationAPI, systemAPI } from '../services/api';

function DataManagement() {
    const [activeTab, setActiveTab] = useState('teachers');
    const [teachers, setTeachers] = useState([]);
    const [courses, setCourses] = useState([]);
    const [rooms, setRooms] = useState([]);
    const [sections, setSections] = useState([]);
    const [mappings, setMappings] = useState([]);
    const [timeslots, setTimeslots] = useState([]);
    const [electiveAllocations, setElectiveAllocations] = useState([]);
    const [loading, setLoading] = useState(true);

    // Selection state for bulk delete
    const [selectedItems, setSelectedItems] = useState(new Set());

    // Editing state
    const [editingCell, setEditingCell] = useState(null); // {id, field}
    const [editValue, setEditValue] = useState('');

    // Add new record state
    const [showAddForm, setShowAddForm] = useState(false);
    const [newRecord, setNewRecord] = useState({});

    // CSV Import state
    const [showImportModal, setShowImportModal] = useState(false);
    const [csvFile, setCsvFile] = useState(null);
    const [csvData, setCsvData] = useState([]);
    const [importErrors, setImportErrors] = useState([]);

    useEffect(() => {
        loadData();
    }, []);

    const loadData = async () => {
        try {
            const [teachersRes, coursesRes, roomsRes, sectionsRes, mappingsRes, timeslotsRes, electiveAllocationsRes] = await Promise.all([
                teacherAPI.getAll(),
                courseAPI.getAll(),
                roomAPI.getAll(),
                sectionAPI.getAll(),
                teacherCourseMappingAPI.getAll(),
                timeslotAPI.getAll(),
                electiveAllocationAPI.getAll(),
            ]);

            setTeachers(teachersRes.data.results || teachersRes.data || []);
            setCourses(coursesRes.data.results || coursesRes.data || []);
            setRooms(roomsRes.data.results || roomsRes.data || []);
            setSections(sectionsRes.data.results || sectionsRes.data || []);
            setMappings(mappingsRes.data.results || mappingsRes.data || []);
            setTimeslots(timeslotsRes.data.results || timeslotsRes.data || []);
            setElectiveAllocations(electiveAllocationsRes.data.results || electiveAllocationsRes.data || []);
        } catch (error) {
            console.error('Error loading data:', error);
        } finally {
            setLoading(false);
        }
    };

    // Selection handlers
    const toggleSelection = (id) => {
        const newSelection = new Set(selectedItems);
        if (newSelection.has(id)) {
            newSelection.delete(id);
        } else {
            newSelection.add(id);
        }
        setSelectedItems(newSelection);
    };

    const toggleSelectAll = () => {
        const currentData = getCurrentData();
        if (selectedItems.size === currentData.length) {
            setSelectedItems(new Set());
        } else {
            setSelectedItems(new Set(currentData.map(item => getItemId(item))));
        }
    };

    // Inline editing handlers
    const startEdit = (id, field, currentValue) => {
        setEditingCell({ id, field });
        setEditValue(currentValue);
    };

    const saveEdit = async (id) => {
        try {
            const { field } = editingCell;
            const api = getActiveAPI();

            // Get current item
            const currentData = getCurrentData();
            const item = currentData.find(i => getItemId(i) === id);

            // Update the item
            const updatedItem = { ...item, [field]: editValue };
            await api.update(id, updatedItem);

            // Reload data
            await loadData();
            setEditingCell(null);
            setEditValue('');
        } catch (error) {
            console.error('Error updating:', error);
            alert('Failed to update: ' + (error.response?.data?.error || error.message));
        }
    };

    const cancelEdit = () => {
        setEditingCell(null);
        setEditValue('');
    };

    // Bulk delete handler
    const handleBulkDelete = async () => {
        if (selectedItems.size === 0) {
            alert('Please select items to delete');
            return;
        }

        if (!window.confirm(`Delete ${selectedItems.size} selected item(s)?`)) {
            return;
        }

        try {
            const api = getActiveAPI();
            await Promise.all(
                Array.from(selectedItems).map(id => api.delete(id))
            );

            setSelectedItems(new Set());
            await loadData();
            alert('Items deleted successfully');
        } catch (error) {
            console.error('Error deleting:', error);
            alert('Failed to delete some items');
        }
    };

    const handleClearAllData = async () => {
        if (!window.confirm('WARNING: This will delete ALL data (Teachers, Courses, Rooms, Sections, etc.) from the system. This action cannot be undone. Are you sure?')) {
            return;
        }

        if (!window.confirm('Are you ABSOLUTELY sure? All schedules and entries will also be deleted.')) {
            return;
        }

        try {
            setLoading(true);
            await systemAPI.clearAllData();
            await loadData();
            alert('All data cleared successfully');
        } catch (error) {
            console.error('Error clearing data:', error);
            alert('Failed to clear data: ' + (error.response?.data?.error || error.message));
        } finally {
            setLoading(false);
        }
    };

    // Add new record handler
    const handleAddNew = async () => {
        try {
            const api = getActiveAPI();
            await api.create(newRecord);

            setShowAddForm(false);
            setNewRecord({});
            await loadData();
            alert('Record added successfully');
        } catch (error) {
            console.error('Error adding:', error);
            alert('Failed to add record: ' + (error.response?.data?.error || error.message));
        }
    };

    // Helper functions
    const getCurrentData = () => {
        switch (activeTab) {
            case 'teachers': return teachers;
            case 'courses': return courses;
            case 'elective-courses': return courses.filter(c => c.is_elective);
            case 'rooms': return rooms;
            case 'sections': return sections;
            case 'mappings': return mappings;
            case 'timeslots': return timeslots;
            case 'elective-allocations': return electiveAllocations;
            default: return [];
        }
    };

    const getActiveAPI = () => {
        switch (activeTab) {
            case 'teachers': return teacherAPI;
            case 'courses': return courseAPI;
            case 'elective-courses': return courseAPI;
            case 'rooms': return roomAPI;
            case 'sections': return sectionAPI;
            case 'mappings': return teacherCourseMappingAPI;
            case 'timeslots': return timeslotAPI;
            case 'elective-allocations': return electiveAllocationAPI;
            default: return teacherAPI;
        }
    };

    const getItemId = (item) => {
        if (!item) return null;
        switch (activeTab) {
            case 'teachers': return item.teacher_id;
            case 'courses': return item.course_id;
            case 'elective-courses': return item.course_id;
            case 'rooms': return item.room_id;
            case 'sections': return item.class_id;
            case 'mappings': return item.id;
            case 'timeslots': return item.slot_id;
            case 'elective-allocations': return item.id;
            default: return item.id;
        }
    };

    const getNewRecordTemplate = () => {
        switch (activeTab) {
            case 'teachers':
                return { teacher_id: '', teacher_name: '', email: '', department: '', max_hours_per_week: 20 };
            case 'courses':
                return { course_id: '', course_name: '', year: 1, semester: 'odd', lectures: 3, theory: 0, practicals: 0, credits: 3, is_lab: false, is_elective: false, weekly_slots: 3, elective_group: 'NA', is_schedulable: true };
            case 'rooms':
                return { room_id: '', block: '', floor: 1, room_type: 'CLASSROOM' };
            case 'sections':
                return { class_id: '', year: 1, section: 'A', department: '' };
            case 'mappings':
                return { teacher: '', course: '', preference_level: 3 };
            case 'timeslots':
                return { slot_id: '', day: 'MON', slot_number: 1, start_time: '09:00', end_time: '10:00' };
            case 'elective-courses':
                return { course_id: '', course_name: '', year: 1, semester: 'odd', lectures: 3, theory: 0, practicals: 0, credits: 3, is_lab: false, is_elective: true, weekly_slots: 3, elective_group: '', is_schedulable: true };
            case 'elective-allocations':
                return { course: '', section_group: '', teacher: '' };
            default:
                return {};
        }
    };

    // CSV Import functions
    const getExpectedSchema = () => {
        switch (activeTab) {
            case 'teachers':
                return ['teacher_id', 'teacher_name', 'email', 'department', 'max_hours_per_week'];
            case 'courses':
                return ['course_id', 'course_name', 'year', 'semester', 'lectures', 'theory', 'practicals', 'credits', 'is_lab', 'is_elective', 'weekly_slots'];
            case 'rooms':
                return ['room_id', 'block', 'floor', 'room_type'];
            case 'sections':
                return ['class_id', 'year', 'section', 'department'];
            case 'mappings':
                return ['teacher_id', 'course_id']; // course_name is optional/ignored, preference_level optional
            case 'timeslots':
                return ['slot_id', 'day', 'slot_number', 'start_time', 'end_time'];
            case 'elective-courses':
                return ['course_id', 'course_name', 'year', 'semester', 'lectures', 'theory', 'practicals', 'credits', 'is_lab', 'is_elective', 'weekly_slots', 'elective_group', 'is_schedulable'];
            case 'elective-allocations':
                return ['course_id', 'section_group', 'teacher_id'];
            default:
                return [];
        }
    };

    const parseCSV = (text) => {
        const lines = text.split('\n').filter(line => line.trim());
        if (lines.length === 0) return { headers: [], rows: [] };

        const headers = lines[0].split(',').map(h => h.trim());
        const rows = lines.slice(1).map(line => {
            const values = line.split(',').map(v => v.trim());
            const row = {};
            headers.forEach((header, index) => {
                row[header] = values[index];
            });
            return row;
        });

        return { headers, rows };
    };

    const validateSchema = (headers) => {
        const expected = getExpectedSchema();
        const missing = expected.filter(field => !headers.includes(field));
        const extra = headers.filter(field => !expected.includes(field));

        return {
            valid: missing.length === 0,
            missing,
            extra
        };
    };

    const handleFileSelect = (event) => {
        const file = event.target.files[0];
        if (!file) return;

        if (!file.name.endsWith('.csv')) {
            alert('Please select a CSV file');
            return;
        }

        setCsvFile(file);

        const reader = new FileReader();
        reader.onload = (e) => {
            const text = e.target.result;
            const { headers, rows } = parseCSV(text);

            const validation = validateSchema(headers);

            if (!validation.valid) {
                setImportErrors([
                    `Schema mismatch!`,
                    validation.missing.length > 0 ? `Missing columns: ${validation.missing.join(', ')}` : null,
                    validation.extra.length > 0 ? `Extra columns (will be ignored): ${validation.extra.join(', ')}` : null,
                ].filter(Boolean));
                setCsvData([]);
            } else {
                setImportErrors([]);
                setCsvData(rows);
            }
        };

        reader.readAsText(file);
    };

    const handleImportCSV = async () => {
        if (csvData.length === 0) {
            alert('No valid data to import');
            return;
        }

        if (!window.confirm(`Import ${csvData.length} records from CSV?`)) {
            return;
        }

        try {
            const api = getActiveAPI();
            let successCount = 0;
            let errorCount = 0;
            const errors = [];

            // Deduplicate data if needed
            let dataToImport = csvData;
            if (activeTab === 'mappings') {
                const seen = new Set();
                dataToImport = csvData.filter(row => {
                    if (!row.teacher_id || !row.course_id) return false;
                    const key = `${row.teacher_id}-${row.course_id}`;
                    if (seen.has(key)) return false;
                    seen.add(key);
                    return true;
                });
            }

            for (const row of dataToImport) {
                try {
                    const processedRow = { ...row };

                    if (activeTab === 'teachers') {
                        processedRow.max_hours_per_week = parseInt(processedRow.max_hours_per_week);
                    } else if (activeTab === 'courses' || activeTab === 'elective-courses') {
                        processedRow.year = parseInt(processedRow.year);
                        // processedRow.semester is already a string ('odd'/'even'), no parseInt needed
                        processedRow.credits = parseInt(processedRow.credits);
                        processedRow.weekly_slots = parseInt(processedRow.weekly_slots);
                        processedRow.lectures = parseInt(processedRow.lectures);
                        processedRow.theory = parseInt(processedRow.theory);
                        processedRow.practicals = parseInt(processedRow.practicals);
                        processedRow.is_lab = processedRow.is_lab === 'true' || processedRow.is_lab === '1';
                        processedRow.is_elective = processedRow.is_elective === 'true' || processedRow.is_elective === '1' || activeTab === 'elective-courses';
                        processedRow.is_schedulable = processedRow.is_schedulable === 'true' || processedRow.is_schedulable === '1' || processedRow.is_schedulable === undefined;
                    } else if (activeTab === 'rooms') {
                        processedRow.floor = parseInt(processedRow.floor);
                    } else if (activeTab === 'sections') {
                        processedRow.year = parseInt(processedRow.year);
                    } else if (activeTab === 'mappings') {
                        processedRow.teacher = processedRow.teacher_id;
                        processedRow.course = processedRow.course_id;
                        processedRow.preference_level = processedRow.preference_level ? parseInt(processedRow.preference_level) : 3;
                    } else if (activeTab === 'timeslots') {
                        processedRow.slot_number = parseInt(processedRow.slot_number);
                    } else if (activeTab === 'elective-allocations') {
                        processedRow.course = processedRow.course_id;
                        processedRow.teacher = processedRow.teacher_id;
                    }

                    await api.create(processedRow);
                    successCount++;
                } catch (error) {
                    errorCount++;
                    errors.push(`Row ${successCount + errorCount}: ${error.response?.data?.error || error.message}`);
                }
            }

            setShowImportModal(false);
            setCsvFile(null);
            setCsvData([]);
            setImportErrors([]);
            await loadData();

            alert(`Import complete!\nSuccess: ${successCount}\nFailed: ${errorCount}${errors.length > 0 ? '\n\nErrors:\n' + errors.slice(0, 5).join('\n') : ''}`);
        } catch (error) {
            console.error('Error importing CSV:', error);
            alert('Failed to import CSV');
        }
    };

    // Render editable cell
    const renderEditableCell = (item, field, value) => {
        const id = getItemId(item);
        const isEditing = editingCell?.id === id && editingCell?.field === field;

        if (isEditing) {
            return (
                <input
                    type={typeof value === 'number' ? 'number' : 'text'}
                    value={editValue}
                    onChange={(e) => setEditValue(e.target.value)}
                    onBlur={() => saveEdit(id)}
                    onKeyDown={(e) => {
                        if (e.key === 'Enter') saveEdit(id);
                        if (e.key === 'Escape') cancelEdit();
                    }}
                    autoFocus
                    style={{ width: '100%', padding: '0.25rem', border: '2px solid var(--primary-color)', borderRadius: '4px' }}
                />
            );
        }

        return (
            <span
                onClick={() => startEdit(id, field, value)}
                style={{ cursor: 'pointer', padding: '0.25rem', display: 'block', borderRadius: '4px' }}
                onMouseEnter={(e) => e.target.style.background = '#f0f0f0'}
                onMouseLeave={(e) => e.target.style.background = 'transparent'}
                title="Click to edit"
            >
                {value}
            </span>
        );
    };

    if (loading) {
        return (
            <div className="loading">
                <div className="spinner"></div>
                <p>Loading data...</p>
            </div>
        );
    }

    const currentData = getCurrentData();

    return (
        <div>
            <div className="page-header">
                <h1 className="page-title">Data Management</h1>
                <p className="page-description">Full CRUD operations - Click cells to edit, select rows to delete</p>
            </div>

            {/* Tabs */}
            <div className="card">
                <div style={{ display: 'flex', gap: '1rem', marginBottom: '1.5rem', borderBottom: '1px solid var(--border)', paddingBottom: '1rem' }}>
                    <button
                        className={`btn ${activeTab === 'teachers' ? 'btn-primary' : 'btn-secondary'}`}
                        onClick={() => { setActiveTab('teachers'); setSelectedItems(new Set()); }}
                    >
                        Teachers ({teachers.length})
                    </button>
                    <button
                        className={`btn ${activeTab === 'courses' ? 'btn-primary' : 'btn-secondary'}`}
                        onClick={() => { setActiveTab('courses'); setSelectedItems(new Set()); }}
                    >
                        Courses ({courses.length})
                    </button>
                    <button
                        className={`btn ${activeTab === 'rooms' ? 'btn-primary' : 'btn-secondary'}`}
                        onClick={() => { setActiveTab('rooms'); setSelectedItems(new Set()); }}
                    >
                        Rooms ({rooms.length})
                    </button>
                    <button
                        className={`btn ${activeTab === 'sections' ? 'btn-primary' : 'btn-secondary'}`}
                        onClick={() => { setActiveTab('sections'); setSelectedItems(new Set()); }}
                    >
                        Sections ({sections.length})
                    </button>
                    <button
                        className={`btn ${activeTab === 'mappings' ? 'btn-primary' : 'btn-secondary'}`}
                        onClick={() => { setActiveTab('mappings'); setSelectedItems(new Set()); }}
                    >
                        Mappings ({mappings.length})
                    </button>
                    <button
                        className={`btn ${activeTab === 'timeslots' ? 'btn-primary' : 'btn-secondary'}`}
                        onClick={() => { setActiveTab('timeslots'); setSelectedItems(new Set()); }}
                    >
                        TimeSlots ({timeslots.length})
                    </button>
                    <button
                        className={`btn ${activeTab === 'elective-courses' ? 'btn-primary' : 'btn-secondary'}`}
                        onClick={() => { setActiveTab('elective-courses'); setSelectedItems(new Set()); }}
                    >
                        Elective Courses ({courses.filter(c => c.is_elective).length})
                    </button>
                    <button
                        className={`btn ${activeTab === 'elective-allocations' ? 'btn-primary' : 'btn-secondary'}`}
                        onClick={() => { setActiveTab('elective-allocations'); setSelectedItems(new Set()); }}
                    >
                        Elective Allocation ({electiveAllocations.length})
                    </button>
                </div>

                {/* Action Buttons */}
                <div style={{ display: 'flex', gap: '1rem', marginBottom: '1rem' }}>
                    <button
                        className="btn btn-success"
                        onClick={() => { setShowAddForm(true); setNewRecord(getNewRecordTemplate()); }}
                    >
                        + Add New
                    </button>
                    <button
                        className="btn btn-primary"
                        onClick={() => setShowImportModal(true)}
                    >
                        Import CSV
                    </button>
                    <button
                        className="btn btn-danger"
                        onClick={handleClearAllData}
                        style={{ marginLeft: 'auto' }}
                    >
                        Clear All Data
                    </button>
                    {selectedItems.size > 0 && (
                        <button
                            className="btn btn-danger"
                            onClick={handleBulkDelete}
                        >
                            Delete Selected ({selectedItems.size})
                        </button>
                    )}
                </div>

                {/* Teachers Table */}
                {activeTab === 'teachers' && (
                    <div className="table-container">
                        <table className="data-table" style={{ width: '100%', borderCollapse: 'collapse' }}>
                            <thead>
                                <tr style={{ background: '#f8f9fa' }}>
                                    <th style={{ padding: '12px', borderBottom: '2px solid #ddd' }}>
                                        <input
                                            type="checkbox"
                                            checked={selectedItems.size === teachers.length && teachers.length > 0}
                                            onChange={toggleSelectAll}
                                        />
                                    </th>
                                    <th style={{ padding: '12px', borderBottom: '2px solid #ddd' }}>Teacher ID</th>
                                    <th style={{ padding: '12px', borderBottom: '2px solid #ddd' }}>Name</th>
                                    <th style={{ padding: '12px', borderBottom: '2px solid #ddd' }}>Email</th>
                                    <th style={{ padding: '12px', borderBottom: '2px solid #ddd' }}>Department</th>
                                    <th style={{ padding: '12px', borderBottom: '2px solid #ddd' }}>Max Hours/Week</th>
                                </tr>
                            </thead>
                            <tbody>
                                {teachers.map((teacher) => (
                                    <tr key={teacher.teacher_id} style={{ borderBottom: '1px solid #eee' }}>
                                        <td style={{ padding: '12px' }}>
                                            <input
                                                type="checkbox"
                                                checked={selectedItems.has(teacher.teacher_id)}
                                                onChange={() => toggleSelection(teacher.teacher_id)}
                                            />
                                        </td>
                                        <td style={{ padding: '12px' }}>{teacher.teacher_id}</td>
                                        <td style={{ padding: '12px' }}>{renderEditableCell(teacher, 'teacher_name', teacher.teacher_name)}</td>
                                        <td style={{ padding: '12px' }}>{renderEditableCell(teacher, 'email', teacher.email)}</td>
                                        <td style={{ padding: '12px' }}>{renderEditableCell(teacher, 'department', teacher.department)}</td>
                                        <td style={{ padding: '12px' }}>{renderEditableCell(teacher, 'max_hours_per_week', teacher.max_hours_per_week)}</td>
                                    </tr>
                                ))}
                            </tbody>
                        </table>
                    </div>
                )}

                {/* Courses Table (Regular and Elective) */}
                {(activeTab === 'courses' || activeTab === 'elective-courses') && (
                    <div className="table-container">
                        <table className="data-table" style={{ width: '100%', borderCollapse: 'collapse' }}>
                            <thead>
                                <tr style={{ background: '#f8f9fa' }}>
                                    <th style={{ padding: '12px', borderBottom: '2px solid #ddd' }}>
                                        <input type="checkbox" checked={selectedItems.size === courses.length && courses.length > 0} onChange={toggleSelectAll} />
                                    </th>
                                    <th style={{ padding: '12px', borderBottom: '2px solid #ddd' }}>ID</th>
                                    <th style={{ padding: '12px', borderBottom: '2px solid #ddd' }}>Name</th>
                                    <th style={{ padding: '12px', borderBottom: '2px solid #ddd' }}>Yr/Sem</th>
                                    <th style={{ padding: '12px', borderBottom: '2px solid #ddd' }}>L-T-P-C</th>
                                    <th style={{ padding: '12px', borderBottom: '2px solid #ddd' }}>Slots</th>
                                    <th style={{ padding: '12px', borderBottom: '2px solid #ddd' }}>Lab?</th>
                                    <th style={{ padding: '12px', borderBottom: '2px solid #ddd' }}>Elective?</th>
                                    <th style={{ padding: '12px', borderBottom: '2px solid #ddd' }}>Group</th>
                                    <th style={{ padding: '12px', borderBottom: '2px solid #ddd' }}>Schedulable?</th>
                                </tr>
                            </thead>
                            <tbody>
                                {courses.filter(c => activeTab === 'courses' ? true : c.is_elective).map((course) => (
                                    <tr key={course.course_id} style={{ borderBottom: '1px solid #eee' }}>
                                        <td style={{ padding: '12px' }}>
                                            <input type="checkbox" checked={selectedItems.has(course.course_id)} onChange={() => toggleSelection(course.course_id)} />
                                        </td>
                                        <td style={{ padding: '12px' }}>{course.course_id}</td>
                                        <td style={{ padding: '12px' }}>{renderEditableCell(course, 'course_name', course.course_name)}</td>
                                        <td style={{ padding: '12px' }}>{course.year}/{course.semester}</td>
                                        <td style={{ padding: '12px' }}>{course.lectures}-{course.theory}-{course.practicals}-{course.credits}</td>
                                        <td style={{ padding: '12px' }}>{renderEditableCell(course, 'weekly_slots', course.weekly_slots)}</td>
                                        <td style={{ padding: '12px' }}>{course.is_lab ? '✅' : '❌'}</td>
                                        <td style={{ padding: '12px' }}>{course.is_elective ? '✅' : '❌'}</td>
                                        <td style={{ padding: '12px' }}>{renderEditableCell(course, 'elective_group', course.elective_group || '-')}</td>
                                        <td style={{ padding: '12px' }}>{course.is_schedulable ? '✅' : '❌'}</td>
                                    </tr>
                                ))}
                            </tbody>
                        </table>
                    </div>
                )}

                {/* Rooms Table */}
                {activeTab === 'rooms' && (
                    <div className="table-container">
                        <table className="data-table" style={{ width: '100%', borderCollapse: 'collapse' }}>
                            <thead>
                                <tr style={{ background: '#f8f9fa' }}>
                                    <th style={{ padding: '12px', borderBottom: '2px solid #ddd' }}>
                                        <input type="checkbox" checked={selectedItems.size === rooms.length && rooms.length > 0} onChange={toggleSelectAll} />
                                    </th>
                                    <th style={{ padding: '12px', borderBottom: '2px solid #ddd' }}>Room ID</th>
                                    <th style={{ padding: '12px', borderBottom: '2px solid #ddd' }}>Block</th>
                                    <th style={{ padding: '12px', borderBottom: '2px solid #ddd' }}>Floor</th>
                                    <th style={{ padding: '12px', borderBottom: '2px solid #ddd' }}>Type</th>
                                </tr>
                            </thead>
                            <tbody>
                                {rooms.map((room) => (
                                    <tr key={room.room_id} style={{ borderBottom: '1px solid #eee' }}>
                                        <td style={{ padding: '12px' }}>
                                            <input type="checkbox" checked={selectedItems.has(room.room_id)} onChange={() => toggleSelection(room.room_id)} />
                                        </td>
                                        <td style={{ padding: '12px' }}>{room.room_id}</td>
                                        <td style={{ padding: '12px' }}>{renderEditableCell(room, 'block', room.block)}</td>
                                        <td style={{ padding: '12px' }}>{renderEditableCell(room, 'floor', room.floor)}</td>
                                        <td style={{ padding: '12px' }}>{renderEditableCell(room, 'room_type', room.room_type)}</td>
                                    </tr>
                                ))}
                            </tbody>
                        </table>
                    </div>
                )}

                {/* Sections Table */}
                {activeTab === 'sections' && (
                    <div className="table-container">
                        <table className="data-table" style={{ width: '100%', borderCollapse: 'collapse' }}>
                            <thead>
                                <tr style={{ background: '#f8f9fa' }}>
                                    <th style={{ padding: '12px', borderBottom: '2px solid #ddd' }}>
                                        <input type="checkbox" checked={selectedItems.size === sections.length && sections.length > 0} onChange={toggleSelectAll} />
                                    </th>
                                    <th style={{ padding: '12px', borderBottom: '2px solid #ddd' }}>Class ID</th>
                                    <th style={{ padding: '12px', borderBottom: '2px solid #ddd' }}>Year</th>
                                    <th style={{ padding: '12px', borderBottom: '2px solid #ddd' }}>Section</th>
                                    <th style={{ padding: '12px', borderBottom: '2px solid #ddd' }}>Department</th>
                                </tr>
                            </thead>
                            <tbody>
                                {sections.map((section) => (
                                    <tr key={section.class_id} style={{ borderBottom: '1px solid #eee' }}>
                                        <td style={{ padding: '12px' }}>
                                            <input type="checkbox" checked={selectedItems.has(section.class_id)} onChange={() => toggleSelection(section.class_id)} />
                                        </td>
                                        <td style={{ padding: '12px' }}>{section.class_id}</td>
                                        <td style={{ padding: '12px' }}>{renderEditableCell(section, 'year', section.year)}</td>
                                        <td style={{ padding: '12px' }}>{renderEditableCell(section, 'section', section.section)}</td>
                                        <td style={{ padding: '12px' }}>{renderEditableCell(section, 'department', section.department)}</td>
                                    </tr>
                                ))}
                            </tbody>
                        </table>
                    </div>
                )}

                {/* Mappings Table */}
                {activeTab === 'mappings' && (
                    <div className="table-container">
                        <table className="data-table" style={{ width: '100%', borderCollapse: 'collapse' }}>
                            <thead>
                                <tr style={{ background: '#f8f9fa' }}>
                                    <th style={{ padding: '12px', borderBottom: '2px solid #ddd' }}>
                                        <input type="checkbox" checked={selectedItems.size === mappings.length && mappings.length > 0} onChange={toggleSelectAll} />
                                    </th>
                                    <th style={{ padding: '12px', borderBottom: '2px solid #ddd' }}>ID</th>
                                    <th style={{ padding: '12px', borderBottom: '2px solid #ddd' }}>Teacher</th>
                                    <th style={{ padding: '12px', borderBottom: '2px solid #ddd' }}>Course</th>
                                    <th style={{ padding: '12px', borderBottom: '2px solid #ddd' }}>Preference</th>
                                </tr>
                            </thead>
                            <tbody>
                                {mappings.map((mapping) => (
                                    <tr key={mapping.id} style={{ borderBottom: '1px solid #eee' }}>
                                        <td style={{ padding: '12px' }}>
                                            <input type="checkbox" checked={selectedItems.has(mapping.id)} onChange={() => toggleSelection(mapping.id)} />
                                        </td>
                                        <td style={{ padding: '12px' }}>{mapping.id}</td>
                                        <td style={{ padding: '12px' }}>{mapping.teacher_name} ({mapping.teacher})</td>
                                        <td style={{ padding: '12px' }}>{mapping.course_name} ({mapping.course})</td>
                                        <td style={{ padding: '12px' }}>{renderEditableCell(mapping, 'preference_level', mapping.preference_level)}</td>
                                    </tr>
                                ))}
                            </tbody>
                        </table>
                    </div>
                )}

                {/* TimeSlots Table */}
                {activeTab === 'timeslots' && (
                    <div className="table-container">
                        <table className="data-table" style={{ width: '100%', borderCollapse: 'collapse' }}>
                            <thead>
                                <tr style={{ background: '#f8f9fa' }}>
                                    <th style={{ padding: '12px', borderBottom: '2px solid #ddd' }}>
                                        <input type="checkbox" checked={selectedItems.size === timeslots.length && timeslots.length > 0} onChange={toggleSelectAll} />
                                    </th>
                                    <th style={{ padding: '12px', borderBottom: '2px solid #ddd' }}>Slot ID</th>
                                    <th style={{ padding: '12px', borderBottom: '2px solid #ddd' }}>Day</th>
                                    <th style={{ padding: '12px', borderBottom: '2px solid #ddd' }}>Slot #</th>
                                    <th style={{ padding: '12px', borderBottom: '2px solid #ddd' }}>Start Time</th>
                                    <th style={{ padding: '12px', borderBottom: '2px solid #ddd' }}>End Time</th>
                                </tr>
                            </thead>
                            <tbody>
                                {timeslots.map((slot) => (
                                    <tr key={slot.slot_id} style={{ borderBottom: '1px solid #eee' }}>
                                        <td style={{ padding: '12px' }}>
                                            <input type="checkbox" checked={selectedItems.has(slot.slot_id)} onChange={() => toggleSelection(slot.slot_id)} />
                                        </td>
                                        <td style={{ padding: '12px' }}>{slot.slot_id}</td>
                                        <td style={{ padding: '12px' }}>{renderEditableCell(slot, 'day', slot.day)}</td>
                                        <td style={{ padding: '12px' }}>{renderEditableCell(slot, 'slot_number', slot.slot_number)}</td>
                                        <td style={{ padding: '12px' }}>{renderEditableCell(slot, 'start_time', slot.start_time)}</td>
                                        <td style={{ padding: '12px' }}>{renderEditableCell(slot, 'end_time', slot.end_time)}</td>
                                    </tr>
                                ))}
                            </tbody>
                        </table>
                    </div>
                )}

                {/* Elective Allocation Table */}
                {activeTab === 'elective-allocations' && (
                    <div className="table-container">
                        <table className="data-table" style={{ width: '100%', borderCollapse: 'collapse' }}>
                            <thead>
                                <tr style={{ background: '#f8f9fa' }}>
                                    <th style={{ padding: '12px', borderBottom: '2px solid #ddd' }}>
                                        <input type="checkbox" checked={selectedItems.size === electiveAllocations.length && electiveAllocations.length > 0} onChange={toggleSelectAll} />
                                    </th>
                                    <th style={{ padding: '12px', borderBottom: '2px solid #ddd' }}>ID</th>
                                    <th style={{ padding: '12px', borderBottom: '2px solid #ddd' }}>Course</th>
                                    <th style={{ padding: '12px', borderBottom: '2px solid #ddd' }}>Section Group</th>
                                    <th style={{ padding: '12px', borderBottom: '2px solid #ddd' }}>Teacher</th>
                                </tr>
                            </thead>
                            <tbody>
                                {electiveAllocations.map((alloc) => (
                                    <tr key={alloc.id} style={{ borderBottom: '1px solid #eee' }}>
                                        <td style={{ padding: '12px' }}>
                                            <input type="checkbox" checked={selectedItems.has(alloc.id)} onChange={() => toggleSelection(alloc.id)} />
                                        </td>
                                        <td style={{ padding: '12px' }}>{alloc.id}</td>
                                        <td style={{ padding: '12px' }}>{alloc.course_name} ({alloc.course})</td>
                                        <td style={{ padding: '12px' }}>{renderEditableCell(alloc, 'section_group', alloc.section_group)}</td>
                                        <td style={{ padding: '12px' }}>{alloc.teacher_name} ({alloc.teacher})</td>
                                    </tr>
                                ))}
                            </tbody>
                        </table>
                    </div>
                )}
            </div>

            {/* Add New Record Modal */}
            {showAddForm && (
                <div className="modal-overlay" style={{ position: 'fixed', top: 0, left: 0, right: 0, bottom: 0, background: 'rgba(0,0,0,0.5)', display: 'flex', alignItems: 'center', justifyContent: 'center', zIndex: 1000 }}>
                    <div className="modal-content" style={{ background: 'white', padding: '2rem', borderRadius: '8px', maxWidth: '600px', width: '90%', maxHeight: '80vh', overflow: 'auto' }}>
                        <h2>Add New {activeTab.slice(0, -1).charAt(0).toUpperCase() + activeTab.slice(1, -1)}</h2>

                        {/* Dynamic form based on active tab */}
                        {activeTab === 'teachers' && (
                            <div>
                                <div style={{ marginBottom: '1rem' }}>
                                    <label style={{ display: 'block', marginBottom: '0.5rem', fontWeight: '500' }}>Teacher ID:</label>
                                    <input type="text" value={newRecord.teacher_id || ''} onChange={(e) => setNewRecord({ ...newRecord, teacher_id: e.target.value })} style={{ width: '100%', padding: '0.5rem', border: '1px solid #ddd', borderRadius: '4px' }} />
                                </div>
                                <div style={{ marginBottom: '1rem' }}>
                                    <label style={{ display: 'block', marginBottom: '0.5rem', fontWeight: '500' }}>Name:</label>
                                    <input type="text" value={newRecord.teacher_name || ''} onChange={(e) => setNewRecord({ ...newRecord, teacher_name: e.target.value })} style={{ width: '100%', padding: '0.5rem', border: '1px solid #ddd', borderRadius: '4px' }} />
                                </div>
                                <div style={{ marginBottom: '1rem' }}>
                                    <label style={{ display: 'block', marginBottom: '0.5rem', fontWeight: '500' }}>Email:</label>
                                    <input type="email" value={newRecord.email || ''} onChange={(e) => setNewRecord({ ...newRecord, email: e.target.value })} style={{ width: '100%', padding: '0.5rem', border: '1px solid #ddd', borderRadius: '4px' }} />
                                </div>
                                <div style={{ marginBottom: '1rem' }}>
                                    <label style={{ display: 'block', marginBottom: '0.5rem', fontWeight: '500' }}>Department:</label>
                                    <input type="text" value={newRecord.department || ''} onChange={(e) => setNewRecord({ ...newRecord, department: e.target.value })} style={{ width: '100%', padding: '0.5rem', border: '1px solid #ddd', borderRadius: '4px' }} />
                                </div>
                                <div style={{ marginBottom: '1rem' }}>
                                    <label style={{ display: 'block', marginBottom: '0.5rem', fontWeight: '500' }}>Max Hours/Week:</label>
                                    <input type="number" value={newRecord.max_hours_per_week || 20} onChange={(e) => setNewRecord({ ...newRecord, max_hours_per_week: parseInt(e.target.value) })} style={{ width: '100%', padding: '0.5rem', border: '1px solid #ddd', borderRadius: '4px' }} />
                                </div>
                            </div>
                        )}

                        {(activeTab === 'courses' || activeTab === 'elective-courses') && (
                            <div>
                                <div style={{ marginBottom: '1rem' }}>
                                    <label style={{ display: 'block', marginBottom: '0.5rem', fontWeight: '500' }}>Course ID:</label>
                                    <input type="text" value={newRecord.course_id || ''} onChange={(e) => setNewRecord({ ...newRecord, course_id: e.target.value })} style={{ width: '100%', padding: '0.5rem', border: '1px solid #ddd', borderRadius: '4px' }} />
                                </div>
                                <div style={{ marginBottom: '1rem' }}>
                                    <label style={{ display: 'block', marginBottom: '0.5rem', fontWeight: '500' }}>Course Name:</label>
                                    <input type="text" value={newRecord.course_name || ''} onChange={(e) => setNewRecord({ ...newRecord, course_name: e.target.value })} style={{ width: '100%', padding: '0.5rem', border: '1px solid #ddd', borderRadius: '4px' }} />
                                </div>
                                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem', marginBottom: '1rem' }}>
                                    <div>
                                        <label style={{ display: 'block', marginBottom: '0.5rem', fontWeight: '500' }}>Year:</label>
                                        <input type="number" value={newRecord.year || 1} onChange={(e) => setNewRecord({ ...newRecord, year: parseInt(e.target.value) })} style={{ width: '100%', padding: '0.5rem', border: '1px solid #ddd', borderRadius: '4px' }} />
                                    </div>
                                    <div>
                                        <label style={{ display: 'block', marginBottom: '0.5rem', fontWeight: '500' }}>Semester:</label>
                                        <select value={newRecord.semester || 'odd'} onChange={(e) => setNewRecord({ ...newRecord, semester: e.target.value })} style={{ width: '100%', padding: '0.5rem', border: '1px solid #ddd', borderRadius: '4px' }}>
                                            <option value="odd">Odd</option>
                                            <option value="even">Even</option>
                                        </select>
                                    </div>
                                </div>
                                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: '1rem', marginBottom: '1rem' }}>
                                    <div>
                                        <label style={{ display: 'block', marginBottom: '0.5rem', fontWeight: '500' }}>Lectures:</label>
                                        <input type="number" value={newRecord.lectures || 3} onChange={(e) => setNewRecord({ ...newRecord, lectures: parseInt(e.target.value) })} style={{ width: '100%', padding: '0.5rem', border: '1px solid #ddd', borderRadius: '4px' }} />
                                    </div>
                                    <div>
                                        <label style={{ display: 'block', marginBottom: '0.5rem', fontWeight: '500' }}>Theory:</label>
                                        <input type="number" value={newRecord.theory || 0} onChange={(e) => setNewRecord({ ...newRecord, theory: parseInt(e.target.value) })} style={{ width: '100%', padding: '0.5rem', border: '1px solid #ddd', borderRadius: '4px' }} />
                                    </div>
                                    <div>
                                        <label style={{ display: 'block', marginBottom: '0.5rem', fontWeight: '500' }}>Practicals:</label>
                                        <input type="number" value={newRecord.practicals || 0} onChange={(e) => setNewRecord({ ...newRecord, practicals: parseInt(e.target.value) })} style={{ width: '100%', padding: '0.5rem', border: '1px solid #ddd', borderRadius: '4px' }} />
                                    </div>
                                </div>
                                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: '1rem', marginBottom: '1rem' }}>
                                    <div>
                                        <label style={{ display: 'block', marginBottom: '0.5rem', fontWeight: '500' }}>Credits:</label>
                                        <input type="number" value={newRecord.credits || 3} onChange={(e) => setNewRecord({ ...newRecord, credits: parseInt(e.target.value) })} style={{ width: '100%', padding: '0.5rem', border: '1px solid #ddd', borderRadius: '4px' }} />
                                    </div>
                                    <div>
                                        <label style={{ display: 'block', marginBottom: '0.5rem', fontWeight: '500' }}>Weekly Slots:</label>
                                        <input type="number" value={newRecord.weekly_slots || 3} onChange={(e) => setNewRecord({ ...newRecord, weekly_slots: parseInt(e.target.value) })} style={{ width: '100%', padding: '0.5rem', border: '1px solid #ddd', borderRadius: '4px' }} />
                                    </div>
                                    <div>
                                        <label style={{ display: 'block', marginBottom: '0.5rem', fontWeight: '500' }}>Elective Group:</label>
                                        <input type="text" value={newRecord.elective_group || ''} onChange={(e) => setNewRecord({ ...newRecord, elective_group: e.target.value })} style={{ width: '100%', padding: '0.5rem', border: '1px solid #ddd', borderRadius: '4px' }} />
                                    </div>
                                </div>
                                <div style={{ display: 'flex', gap: '1rem', marginBottom: '1rem' }}>
                                    <label style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', cursor: 'pointer' }}>
                                        <input type="checkbox" checked={newRecord.is_lab || false} onChange={(e) => setNewRecord({ ...newRecord.is_lab, is_lab: e.target.checked })} />
                                        Is Lab
                                    </label>
                                    <label style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', cursor: 'pointer' }}>
                                        <input type="checkbox" checked={newRecord.is_elective || activeTab === 'elective-courses'} onChange={(e) => setNewRecord({ ...newRecord, is_elective: e.target.checked })} />
                                        Is Elective
                                    </label>
                                    <label style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', cursor: 'pointer' }}>
                                        <input type="checkbox" checked={newRecord.is_schedulable !== false} onChange={(e) => setNewRecord({ ...newRecord, is_schedulable: e.target.checked })} />
                                        Is Schedulable
                                    </label>
                                </div>
                            </div>
                        )}

                        {activeTab === 'rooms' && (
                            <div>
                                <div style={{ marginBottom: '1rem' }}>
                                    <label style={{ display: 'block', marginBottom: '0.5rem', fontWeight: '500' }}>Room ID:</label>
                                    <input type="text" value={newRecord.room_id || ''} onChange={(e) => setNewRecord({ ...newRecord, room_id: e.target.value })} style={{ width: '100%', padding: '0.5rem', border: '1px solid #ddd', borderRadius: '4px' }} />
                                </div>
                                <div style={{ marginBottom: '1rem' }}>
                                    <label style={{ display: 'block', marginBottom: '0.5rem', fontWeight: '500' }}>Block:</label>
                                    <input type="text" value={newRecord.block || ''} onChange={(e) => setNewRecord({ ...newRecord, block: e.target.value })} style={{ width: '100%', padding: '0.5rem', border: '1px solid #ddd', borderRadius: '4px' }} />
                                </div>
                                <div style={{ marginBottom: '1rem' }}>
                                    <label style={{ display: 'block', marginBottom: '0.5rem', fontWeight: '500' }}>Floor:</label>
                                    <input type="number" value={newRecord.floor || 1} onChange={(e) => setNewRecord({ ...newRecord, floor: parseInt(e.target.value) })} style={{ width: '100%', padding: '0.5rem', border: '1px solid #ddd', borderRadius: '4px' }} />
                                </div>
                                <div style={{ marginBottom: '1rem' }}>
                                    <label style={{ display: 'block', marginBottom: '0.5rem', fontWeight: '500' }}>Room Type:</label>
                                    <select value={newRecord.room_type || 'CLASSROOM'} onChange={(e) => setNewRecord({ ...newRecord, room_type: e.target.value })} style={{ width: '100%', padding: '0.5rem', border: '1px solid #ddd', borderRadius: '4px' }}>
                                        <option value="CLASSROOM">Classroom</option>
                                        <option value="LAB">Lab</option>
                                        <option value="SEMINAR">Seminar Hall</option>
                                    </select>
                                </div>
                            </div>
                        )}

                        {activeTab === 'sections' && (
                            <div>
                                <div style={{ marginBottom: '1rem' }}>
                                    <label style={{ display: 'block', marginBottom: '0.5rem', fontWeight: '500' }}>Class ID:</label>
                                    <input type="text" value={newRecord.class_id || ''} onChange={(e) => setNewRecord({ ...newRecord, class_id: e.target.value })} style={{ width: '100%', padding: '0.5rem', border: '1px solid #ddd', borderRadius: '4px' }} />
                                </div>
                                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem', marginBottom: '1rem' }}>
                                    <div>
                                        <label style={{ display: 'block', marginBottom: '0.5rem', fontWeight: '500' }}>Year:</label>
                                        <input type="number" value={newRecord.year || 1} onChange={(e) => setNewRecord({ ...newRecord, year: parseInt(e.target.value) })} style={{ width: '100%', padding: '0.5rem', border: '1px solid #ddd', borderRadius: '4px' }} />
                                    </div>
                                    <div>
                                        <label style={{ display: 'block', marginBottom: '0.5rem', fontWeight: '500' }}>Section:</label>
                                        <input type="text" value={newRecord.section || 'A'} onChange={(e) => setNewRecord({ ...newRecord, section: e.target.value })} style={{ width: '100%', padding: '0.5rem', border: '1px solid #ddd', borderRadius: '4px' }} />
                                    </div>
                                </div>
                                <div style={{ marginBottom: '1rem' }}>
                                    <label style={{ display: 'block', marginBottom: '0.5rem', fontWeight: '500' }}>Semester:</label>
                                    <input type="number" value={newRecord.sem || 1} onChange={(e) => setNewRecord({ ...newRecord, sem: parseInt(e.target.value) })} style={{ width: '100%', padding: '0.5rem', border: '1px solid #ddd', borderRadius: '4px' }} />
                                </div>
                                <div style={{ marginBottom: '1rem' }}>
                                    <label style={{ display: 'block', marginBottom: '0.5rem', fontWeight: '500' }}>Department:</label>
                                    <input type="text" value={newRecord.department || ''} onChange={(e) => setNewRecord({ ...newRecord, department: e.target.value })} style={{ width: '100%', padding: '0.5rem', border: '1px solid #ddd', borderRadius: '4px' }} />
                                </div>
                            </div>
                        )}

                        {activeTab === 'mappings' && (
                            <div>
                                <div style={{ marginBottom: '1rem' }}>
                                    <label style={{ display: 'block', marginBottom: '0.5rem', fontWeight: '500' }}>Teacher ID:</label>
                                    <input type="text" value={newRecord.teacher || ''} onChange={(e) => setNewRecord({ ...newRecord, teacher: e.target.value })} style={{ width: '100%', padding: '0.5rem', border: '1px solid #ddd', borderRadius: '4px' }} />
                                </div>
                                <div style={{ marginBottom: '1rem' }}>
                                    <label style={{ display: 'block', marginBottom: '0.5rem', fontWeight: '500' }}>Course ID:</label>
                                    <input type="text" value={newRecord.course || ''} onChange={(e) => setNewRecord({ ...newRecord, course: e.target.value })} style={{ width: '100%', padding: '0.5rem', border: '1px solid #ddd', borderRadius: '4px' }} />
                                </div>
                                <div style={{ marginBottom: '1rem' }}>
                                    <label style={{ display: 'block', marginBottom: '0.5rem', fontWeight: '500' }}>Preference Level (1-5):</label>
                                    <input type="number" min="1" max="5" value={newRecord.preference_level || 3} onChange={(e) => setNewRecord({ ...newRecord, preference_level: parseInt(e.target.value) })} style={{ width: '100%', padding: '0.5rem', border: '1px solid #ddd', borderRadius: '4px' }} />
                                </div>
                            </div>
                        )}
                        {activeTab === 'timeslots' && (
                            <div>
                                <div style={{ marginBottom: '1rem' }}>
                                    <label style={{ display: 'block', marginBottom: '0.5rem', fontWeight: '500' }}>Slot ID:</label>
                                    <input type="text" value={newRecord.slot_id || ''} onChange={(e) => setNewRecord({ ...newRecord, slot_id: e.target.value })} style={{ width: '100%', padding: '0.5rem', border: '1px solid #ddd', borderRadius: '4px' }} />
                                </div>
                                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem', marginBottom: '1rem' }}>
                                    <div>
                                        <label style={{ display: 'block', marginBottom: '0.5rem', fontWeight: '500' }}>Day:</label>
                                        <select value={newRecord.day || 'MON'} onChange={(e) => setNewRecord({ ...newRecord, day: e.target.value })} style={{ width: '100%', padding: '0.5rem', border: '1px solid #ddd', borderRadius: '4px' }}>
                                            <option value="MON">Monday</option>
                                            <option value="TUE">Tuesday</option>
                                            <option value="WED">Wednesday</option>
                                            <option value="THU">Thursday</option>
                                            <option value="FRI">Friday</option>
                                            <option value="SAT">Saturday</option>
                                        </select>
                                    </div>
                                    <div>
                                        <label style={{ display: 'block', marginBottom: '0.5rem', fontWeight: '500' }}>Slot Number:</label>
                                        <input type="number" value={newRecord.slot_number || 1} onChange={(e) => setNewRecord({ ...newRecord, slot_number: parseInt(e.target.value) })} style={{ width: '100%', padding: '0.5rem', border: '1px solid #ddd', borderRadius: '4px' }} />
                                    </div>
                                </div>
                                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem', marginBottom: '1rem' }}>
                                    <div>
                                        <label style={{ display: 'block', marginBottom: '0.5rem', fontWeight: '500' }}>Start Time:</label>
                                        <input type="time" value={newRecord.start_time || '09:00'} onChange={(e) => setNewRecord({ ...newRecord, start_time: e.target.value })} style={{ width: '100%', padding: '0.5rem', border: '1px solid #ddd', borderRadius: '4px' }} />
                                    </div>
                                    <div>
                                        <label style={{ display: 'block', marginBottom: '0.5rem', fontWeight: '500' }}>End Time:</label>
                                        <input type="time" value={newRecord.end_time || '10:00'} onChange={(e) => setNewRecord({ ...newRecord, end_time: e.target.value })} style={{ width: '100%', padding: '0.5rem', border: '1px solid #ddd', borderRadius: '4px' }} />
                                    </div>
                                </div>
                            </div>
                        )}

                        {activeTab === 'elective-allocations' && (
                            <div>
                                <div style={{ marginBottom: '1rem' }}>
                                    <label style={{ display: 'block', marginBottom: '0.5rem', fontWeight: '500' }}>Course ID (Elective):</label>
                                    <input type="text" value={newRecord.course || ''} onChange={(e) => setNewRecord({ ...newRecord, course: e.target.value })} style={{ width: '100%', padding: '0.5rem', border: '1px solid #ddd', borderRadius: '4px' }} />
                                </div>
                                <div style={{ marginBottom: '1rem' }}>
                                    <label style={{ display: 'block', marginBottom: '0.5rem', fontWeight: '500' }}>Section Group (e.g., CSE3):</label>
                                    <input type="text" value={newRecord.section_group || ''} onChange={(e) => setNewRecord({ ...newRecord, section_group: e.target.value })} style={{ width: '100%', padding: '0.5rem', border: '1px solid #ddd', borderRadius: '4px' }} />
                                </div>
                                <div style={{ marginBottom: '1rem' }}>
                                    <label style={{ display: 'block', marginBottom: '0.5rem', fontWeight: '500' }}>Teacher ID:</label>
                                    <input type="text" value={newRecord.teacher || ''} onChange={(e) => setNewRecord({ ...newRecord, teacher: e.target.value })} style={{ width: '100%', padding: '0.5rem', border: '1px solid #ddd', borderRadius: '4px' }} />
                                </div>
                            </div>
                        )}

                        <div style={{ display: 'flex', gap: '1rem', justifyContent: 'flex-end', marginTop: '1.5rem' }}>
                            <button onClick={handleAddNew} className="btn btn-primary">
                                Add
                            </button>
                            <button onClick={() => { setShowAddForm(false); setNewRecord({}); }} className="btn btn-secondary">
                                Cancel
                            </button>
                        </div>
                    </div>
                </div>
            )}

            {/* CSV Import Modal */}
            {showImportModal && (
                <div className="modal-overlay" style={{ position: 'fixed', top: 0, left: 0, right: 0, bottom: 0, background: 'rgba(0,0,0,0.5)', display: 'flex', alignItems: 'center', justifyContent: 'center', zIndex: 1000 }}>
                    <div className="modal-content" style={{ background: 'white', padding: '2rem', borderRadius: '8px', maxWidth: '600px', width: '90%' }}>
                        <h2>Import CSV - {activeTab.charAt(0).toUpperCase() + activeTab.slice(1)}</h2>

                        <div style={{ marginBottom: '1.5rem', padding: '1rem', background: '#f8f9fa', borderRadius: '4px' }}>
                            <h4 style={{ marginTop: 0 }}>Expected CSV Format:</h4>
                            <code style={{ display: 'block', padding: '0.5rem', background: 'white', borderRadius: '4px', fontSize: '0.875rem' }}>
                                {getExpectedSchema().join(',')}
                            </code>
                        </div>

                        <div style={{ marginBottom: '1rem' }}>
                            <label style={{ display: 'block', marginBottom: '0.5rem', fontWeight: '500' }}>Select CSV File:</label>
                            <input
                                type="file"
                                accept=".csv"
                                onChange={handleFileSelect}
                                style={{ width: '100%', padding: '0.5rem', border: '1px solid #ddd', borderRadius: '4px' }}
                            />
                        </div>

                        {importErrors.length > 0 && (
                            <div style={{ marginBottom: '1rem', padding: '1rem', background: '#fee', border: '1px solid #fcc', borderRadius: '4px', color: '#c00' }}>
                                {importErrors.map((error, idx) => (
                                    <div key={idx}>{error}</div>
                                ))}
                            </div>
                        )}

                        {csvData.length > 0 && (
                            <div style={{ marginBottom: '1rem', padding: '1rem', background: '#efe', border: '1px solid #cfc', borderRadius: '4px', color: '#060' }}>
                                ✓ Valid CSV with {csvData.length} records ready to import
                            </div>
                        )}

                        <div style={{ display: 'flex', gap: '1rem', justifyContent: 'flex-end', marginTop: '1.5rem' }}>
                            <button
                                onClick={handleImportCSV}
                                className="btn btn-primary"
                                disabled={csvData.length === 0}
                                style={{ opacity: csvData.length === 0 ? 0.5 : 1 }}
                            >
                                Import {csvData.length} Records
                            </button>
                            <button
                                onClick={() => {
                                    setShowImportModal(false);
                                    setCsvFile(null);
                                    setCsvData([]);
                                    setImportErrors([]);
                                }}
                                className="btn btn-secondary"
                            >
                                Cancel
                            </button>
                        </div>
                    </div>
                </div>
            )}
        </div>
    );
}

export default DataManagement;
