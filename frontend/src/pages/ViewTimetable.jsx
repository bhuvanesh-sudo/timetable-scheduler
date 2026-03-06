/**
 * View Timetable Page — With Drag-and-Drop Move Support
 *
 * Features:
 *  - Full HTML5 drag-and-drop for class blocks (Admin/HOD only)
 *  - Real-time visual indicators: green = valid drop, red = conflict
 *  - Optimistic-locking to prevent concurrent admin overwrites
 *  - Conflict tooltip shown on hover over a red drop zone
 *
 * Author: Frontend Team (Bhuvanesh, Akshitha)
 * Sprint: 2
 */

import { useState, useEffect, useRef, useCallback } from 'react';
import { scheduleAPI, schedulerAPI, sectionAPI, teacherAPI } from '../services/api';
import { useAuth } from '../context/AuthContext';
import jsPDF from 'jspdf';
import autoTable from 'jspdf-autotable';

// ─── Helpers ──────────────────────────────────────────────────────────────────

const DAYS = ['MON', 'TUE', 'WED', 'THU', 'FRI'];
const SLOTS = [1, 2, 3, 4, 5, 6, 7, 8];

// Debounce utility — avoids spamming validate-move on every dragover pixel
function useDebouncedCallback(fn, delay) {
    const timer = useRef(null);
    return useCallback((...args) => {
        clearTimeout(timer.current);
        timer.current = setTimeout(() => fn(...args), delay);
    }, [fn, delay]);
}

// ─── Component ────────────────────────────────────────────────────────────────

function ViewTimetable() {
    const { user } = useAuth();

    // ── Data state ──
    const [schedules, setSchedules] = useState([]);
    const [sections, setSections] = useState([]);
    const [teachers, setTeachers] = useState([]);
    const [selectedSchedule, setSelectedSchedule] = useState('');
    const [selectedSection, setSelectedSection] = useState('');
    const [selectedTeacher, setSelectedTeacher] = useState('');
    const [timetable, setTimetable] = useState(null);
    const [loading, setLoading] = useState(false);

    // ── Verification modal ──
    const [verificationResult, setVerificationResult] = useState(null);
    const [showVerificationModal, setShowVerificationModal] = useState(false);
    const [verifying, setVerifying] = useState(false);

    // ── Publish state ──
    const [publishing, setPublishing] = useState(false);

    // ── Drag-and-drop state ──
    const [dragging, setDragging] = useState(null);          // { entryId, day, slot, lastModified, classItem }
    const [dropTargets, setDropTargets] = useState({});      // { "DAY-SLOT": { valid: bool|null, conflicts: [] } }
    const [activeDropCell, setActiveDropCell] = useState(null); // "DAY-SLOT" currently being hovered
    const [moveStatus, setMoveStatus] = useState(null);      // { type: 'success'|'error'|'warn', message }
    const validationAbortRef = useRef(null);                  // abort controller for in-flight validate-move

    const isAdminOrHOD = user?.role === 'ADMIN' || user?.role === 'HOD';

    // ── Initial data load ──
    useEffect(() => {
        loadInitialData();
    }, [user]);

    useEffect(() => {
        if (user && user.role === 'FACULTY' && user.teacher_id) {
            setSelectedTeacher(user.teacher_id);
        }
    }, [user]);

    const loadInitialData = async () => {
        try {
            const promises = [scheduleAPI.getAll(), sectionAPI.getAll()];
            if (user && (user.role === 'ADMIN' || user.role === 'HOD')) {
                promises.push(teacherAPI.getAll());
            }
            const [schedulesRes, sectionsRes, teachersRes] = await Promise.all(promises);
            setSchedules(schedulesRes.data.results || schedulesRes.data || []);
            setSections(sectionsRes.data.results || sectionsRes.data || []);
            if (teachersRes) setTeachers(teachersRes.data.results || teachersRes.data || []);

            if (user?.role === 'FACULTY' && !selectedSchedule) {
                const avail = schedulesRes.data.results || schedulesRes.data || [];
                if (avail.length > 0) setSelectedSchedule(avail[0].schedule_id);
            }
        } catch (error) {
            console.error('Error loading data:', error);
        }
    };

    const loadTimetable = async () => {
        if (!selectedSchedule) return;
        setLoading(true);
        try {
            const teacherId = (user && user.role === 'FACULTY') ? user.teacher_id : selectedTeacher;
            const response = await schedulerAPI.getTimetable(
                selectedSchedule, selectedSection || null, teacherId || null
            );
            setTimetable(response.data);
            // Reset DnD state when timetable is (re)loaded
            setDropTargets({});
            setDragging(null);
            setMoveStatus(null);
        } catch (error) {
            console.error('Error loading timetable:', error);
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        if (selectedSchedule) loadTimetable();
    }, [selectedSchedule, selectedSection, selectedTeacher]);

    // ── Verify ──
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

    // ── Publish ──
    const handlePublishSchedule = async () => {
        if (!selectedSchedule) return;
        const scheduleName = schedules.find(s => s.schedule_id == selectedSchedule)?.name || 'this schedule';
        if (!window.confirm(`Publish "${scheduleName}"? This will notify all teachers whose timetable has changed.`)) return;

        setPublishing(true);
        try {
            const response = await schedulerAPI.publish(selectedSchedule);
            setMoveStatus({
                type: 'success',
                message: response.data.message || 'Schedule published successfully!',
            });
            // Refresh schedule list to update statuses
            const schedulesRes = await scheduleAPI.getAll();
            setSchedules(schedulesRes.data.results || schedulesRes.data || []);
        } catch (error) {
            const errMsg = error.response?.data?.error || 'Failed to publish schedule';
            setMoveStatus({ type: 'error', message: errMsg });
        } finally {
            setPublishing(false);
        }
    };

    const selectedScheduleObj = schedules.find(s => s.schedule_id == selectedSchedule);
    const isPublished = selectedScheduleObj?.status === 'PUBLISHED';

    // ── PDF ──
    const handleDownloadPDF = () => {
        if (!timetable) return;
        const doc = new jsPDF();
        doc.setFontSize(18);
        const title = user?.role === 'FACULTY'
            ? `Timetable - ${user.first_name} ${user.last_name}`
            : `Timetable - ${schedules.find(s => s.schedule_id === selectedSchedule)?.name || 'Schedule'}`;
        doc.text(title, 14, 22);
        doc.setFontSize(11);
        let subtitle = '';
        if (selectedSection) subtitle += `Section: ${selectedSection}  `;
        if (selectedTeacher && user?.role !== 'FACULTY') {
            const tName = teachers.find(t => t.teacher_id === selectedTeacher)?.teacher_name || selectedTeacher;
            subtitle += `Teacher: ${tName}`;
        }
        if (subtitle) doc.text(subtitle, 14, 30);

        const tableColumn = ["Time", ...DAYS];
        const tableRows = [];
        SLOTS.forEach(slot => {
            const rowData = [`Slot ${slot}`];
            DAYS.forEach(day => {
                const classes = timetable[day]?.[slot] || [];
                const cellContent = classes.map(c =>
                    `${c.course_code}\n${c.room} (${c.section})` + (c.is_lab_session ? ' [LAB]' : '')
                ).join('\n\n');
                rowData.push(cellContent);
            });
            tableRows.push(rowData);
        });

        autoTable(doc, {
            head: [tableColumn],
            body: tableRows,
            startY: subtitle ? 35 : 25,
            theme: 'grid',
            styles: { fontSize: 8, cellPadding: 2, overflow: 'linebreak' },
            headStyles: { fillColor: [124, 58, 237], textColor: 255 },
            columnStyles: { 0: { cellWidth: 20, fontStyle: 'bold' } },
            didParseCell: (data) => {
                if (data.section === 'body' && data.column.index > 0 && data.cell.raw) {
                    if (data.cell.raw.toString().includes('[LAB]')) {
                        data.cell.styles.fillColor = [240, 248, 255];
                    }
                }
            }
        });
        doc.save('timetable.pdf');
    };

    // ──────────────────────────────────────────────────────────────────────────
    // DRAG-AND-DROP HANDLERS
    // ──────────────────────────────────────────────────────────────────────────

    const handleDragStart = (e, classItem, day, slot) => {
        if (!isAdminOrHOD) return;
        // Pack drag data into dataTransfer (required by HTML5 spec)
        e.dataTransfer.effectAllowed = 'move';
        e.dataTransfer.setData('application/json', JSON.stringify({
            entryId: classItem.entry_id,
            lastModified: classItem.last_modified,
        }));
        setDragging({ entryId: classItem.entry_id, day, slot, lastModified: classItem.last_modified, classItem });
        // Reset all drop-target metadata
        setDropTargets({});
        setMoveStatus(null);
    };

    const handleDragEnd = () => {
        setDragging(null);
        setDropTargets({});
        setActiveDropCell(null);
        if (validationAbortRef.current) {
            validationAbortRef.current = null;
        }
    };

    // Called when the dragged item enters a new cell — do instant validation
    const handleCellDragEnter = useCallback(async (e, day, slot) => {
        e.preventDefault();
        if (!dragging) return;

        const cellKey = `${day}-${slot}`;
        setActiveDropCell(cellKey);

        // Already validated this cell → skip
        if (dropTargets[cellKey] !== undefined) return;
        // Dragging to same cell → mark valid immediately
        if (dragging.day === day && dragging.slot === slot) {
            setDropTargets(prev => ({ ...prev, [cellKey]: { valid: true, conflicts: [] } }));
            return;
        }

        // Mark as "pending" so we render a neutral indicator
        setDropTargets(prev => ({ ...prev, [cellKey]: null }));

        try {
            const res = await schedulerAPI.validateMove(dragging.entryId, day, slot);
            setDropTargets(prev => ({
                ...prev,
                [cellKey]: {
                    valid: res.data.valid,
                    conflicts: res.data.conflicts || [],
                }
            }));
        } catch {
            setDropTargets(prev => ({ ...prev, [cellKey]: { valid: false, conflicts: ['Validation failed'] } }));
        }
    }, [dragging, dropTargets]);

    const handleCellDragOver = (e) => {
        e.preventDefault();
        e.dataTransfer.dropEffect = 'move';
    };

    const handleCellDragLeave = (e, day, slot) => {
        // Only clear activeDropCell when leaving into something outside the grid cell
        const related = e.relatedTarget;
        if (related && e.currentTarget.contains(related)) return;
        setActiveDropCell(prev => (prev === `${day}-${slot}` ? null : prev));
    };

    const handleDrop = async (e, targetDay, targetSlot) => {
        e.preventDefault();
        if (!dragging) return;

        const cellKey = `${targetDay}-${targetSlot}`;
        const validation = dropTargets[cellKey];

        // Deny if we know it's invalid
        if (validation && !validation.valid) {
            setMoveStatus({
                type: 'error',
                message: `Cannot move here: ${validation.conflicts[0] || 'Conflict detected'}`
            });
            setDragging(null);
            setDropTargets({});
            setActiveDropCell(null);
            return;
        }

        // Same cell drop → no-op
        if (dragging.day === targetDay && dragging.slot === targetSlot) {
            setDragging(null);
            setDropTargets({});
            setActiveDropCell(null);
            return;
        }

        try {
            const response = await schedulerAPI.moveEntry({
                entry_id: dragging.entryId,
                target_day: targetDay,
                target_slot: targetSlot,
                last_modified: dragging.lastModified,
            });

            if (response.data.success) {
                setMoveStatus({ type: 'success', message: `Moved to ${targetDay} Slot ${targetSlot} ✓` });
                await loadTimetable(); // Refresh grid
            }
        } catch (err) {
            const errData = err.response?.data;
            if (err.response?.status === 409) {
                setMoveStatus({
                    type: 'warn',
                    message: errData?.error || 'Concurrent edit detected — please refresh.'
                });
                await loadTimetable();
            } else {
                const msg = errData?.conflicts?.[0] || errData?.error || 'Move failed';
                setMoveStatus({ type: 'error', message: msg });
            }
        } finally {
            setDragging(null);
            setDropTargets({});
            setActiveDropCell(null);
        }
    };

    // Auto-dismiss status banner after 5 s
    useEffect(() => {
        if (!moveStatus) return;
        const t = setTimeout(() => setMoveStatus(null), 5000);
        return () => clearTimeout(t);
    }, [moveStatus]);

    // ── Cell drop-zone style helper ──────────────────────────────────────────
    const getCellDropStyle = (day, slot) => {
        if (!dragging) return {};
        const cellKey = `${day}-${slot}`;
        const isActive = activeDropCell === cellKey;
        const validation = dropTargets[cellKey];

        if (!isActive && !validation) return {};

        if (validation === null) {
            // Pending validation
            return {
                outline: '2px dashed #94a3b8',
                background: 'rgba(148,163,184,0.15)',
            };
        }
        if (validation?.valid) {
            return {
                outline: '2px solid #10b981',
                background: 'rgba(16,185,129,0.12)',
                boxShadow: '0 0 12px rgba(16,185,129,0.3)',
            };
        }
        if (validation?.valid === false) {
            return {
                outline: '2px solid #ef4444',
                background: 'rgba(239,68,68,0.1)',
                boxShadow: '0 0 12px rgba(239,68,68,0.25)',
            };
        }
        return {};
    };

    // ── Render ────────────────────────────────────────────────────────────────
    return (
        <div className="fade-in">
            <div className="page-header">
                <h1 className="page-title">
                    {user?.role === 'FACULTY' ? 'My Timetable' : 'View Timetable'}
                </h1>
                <p className="page-description">
                    {user?.role === 'FACULTY'
                        ? `Viewing schedule for ${user.first_name} ${user.last_name}`
                        : isAdminOrHOD
                            ? 'View & manually rearrange classes by dragging blocks to a new slot'
                            : 'View generated timetable schedules'}
                </p>
            </div>

            {/* Move Status Banner */}
            {moveStatus && (
                <div
                    className={`alert ${moveStatus.type === 'success' ? 'alert-success' : moveStatus.type === 'warn' ? 'alert-info' : 'alert-error'}`}
                    style={{
                        display: 'flex', alignItems: 'center', gap: '0.5rem',
                        animation: 'fadeIn 0.3s ease',
                        marginBottom: '1rem',
                    }}
                >
                    <span style={{ fontSize: '1.1rem' }}>
                        {moveStatus.type === 'success' ? '✅' : moveStatus.type === 'warn' ? '⚠️' : '❌'}
                    </span>
                    {moveStatus.message}
                </div>
            )}

            {/* Admin DnD Legend */}
            {isAdminOrHOD && timetable && (
                <div style={{
                    display: 'flex', gap: '1.25rem', alignItems: 'center',
                    marginBottom: '1rem', fontSize: '0.8rem', color: 'var(--text-muted)',
                    flexWrap: 'wrap',
                }}>
                    <span style={{ fontWeight: 600, color: 'var(--text-secondary)' }}>Drag & Drop:</span>
                    <span style={{ display: 'flex', alignItems: 'center', gap: '0.4rem' }}>
                        <span style={{ width: 12, height: 12, borderRadius: 3, background: '#059669', display: 'inline-block', flexShrink: 0 }} />
                        Valid drop zone
                    </span>
                    <span style={{ display: 'flex', alignItems: 'center', gap: '0.4rem' }}>
                        <span style={{ width: 12, height: 12, borderRadius: 3, background: '#dc2626', display: 'inline-block', flexShrink: 0 }} />
                        Conflict — drop blocked
                    </span>
                    <span style={{ display: 'flex', alignItems: 'center', gap: '0.4rem' }}>
                        <span style={{ width: 12, height: 12, borderRadius: 3, border: '1.5px dashed var(--text-muted)', display: 'inline-block', flexShrink: 0 }} />
                        Validating…
                    </span>
                </div>
            )}

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
                        {(selectedSchedule && isAdminOrHOD) && (
                            <div style={{ display: 'flex', gap: '0.5rem', marginTop: '0.75rem' }}>
                                <button
                                    className="btn btn-success"
                                    onClick={handleVerifySchedule}
                                    disabled={verifying}
                                    style={{ flex: 1 }}
                                >
                                    {verifying ? 'Verifying...' : 'Verify Schedule'}
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
                                {user?.role === 'ADMIN' && (
                                    <button
                                        className="btn"
                                        onClick={handlePublishSchedule}
                                        disabled={publishing || isPublished}
                                        style={{
                                            flex: 1,
                                            background: isPublished ? 'var(--text-muted)' : 'linear-gradient(135deg, #6366f1, #8b5cf6)',
                                            color: '#fff',
                                            border: 'none',
                                            cursor: isPublished ? 'not-allowed' : 'pointer',
                                            fontWeight: 600,
                                        }}
                                    >
                                        {publishing ? 'Publishing...' : isPublished ? '✓ Published' : '🚀 Publish Schedule'}
                                    </button>
                                )}
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

                    {/* Teacher Filter — Only for Admin/HOD */}
                    {isAdminOrHOD && (
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

            {/* Loading */}
            {loading && (
                <div className="loading">
                    <div className="spinner"></div>
                    <p>Loading timetable...</p>
                </div>
            )}

            {/* Timetable Grid */}
            {!loading && timetable && (
                <div className="card">
                    <div className="card-header">
                        <h2 className="card-title">Weekly Schedule</h2>
                        <div style={{ display: 'flex', gap: '8px', alignItems: 'center', flexWrap: 'wrap' }}>
                            <button
                                className="btn btn-primary"
                                onClick={handleDownloadPDF}
                                style={{ fontSize: '0.875rem', padding: '0.25rem 0.5rem' }}
                            >
                                Download PDF
                            </button>
                            {user?.role === 'FACULTY' && (
                                <span className="badge-pill badge-primary">Faculty View</span>
                            )}
                            {(selectedTeacher && user?.role !== 'FACULTY') && (
                                <span className="badge-pill badge-info">
                                    Teacher: {teachers.find(t => t.teacher_id === selectedTeacher)?.teacher_name || selectedTeacher}
                                </span>
                            )}
                            {isAdminOrHOD && (
                                <span style={{
                                    display: 'inline-flex', alignItems: 'center', gap: '0.3rem',
                                    fontSize: '0.75rem', color: 'var(--text-muted)',
                                    border: '1px dashed var(--border)', borderRadius: '0.5rem',
                                    padding: '0.2rem 0.6rem',
                                }}>
                                    ✋ Drag blocks to move classes
                                </span>
                            )}
                        </div>
                    </div>

                    <div
                        className="timetable-grid"
                        style={{ userSelect: dragging ? 'none' : 'auto' }}
                    >
                        {/* Header Row */}
                        <div className="grid-header">Time</div>
                        {DAYS.map((day) => (
                            <div key={day} className="grid-header">{day}</div>
                        ))}

                        {/* Time Slots */}
                        {SLOTS.map((slot) => (
                            <>
                                <div key={`time-${slot}`} className="grid-time">
                                    <div>Slot {slot}</div>
                                </div>
                                {DAYS.map((day) => {
                                    const cellKey = `${day}-${slot}`;
                                    const validation = dropTargets[cellKey];
                                    const dropStyle = getCellDropStyle(day, slot);
                                    const hasConflictHint = validation?.valid === false && activeDropCell === cellKey;

                                    return (
                                        <div
                                            key={cellKey}
                                            className="grid-cell"
                                            style={{
                                                ...dropStyle,
                                                transition: 'outline 0.15s ease, background 0.15s ease, box-shadow 0.15s ease',
                                                position: 'relative',
                                            }}
                                            onDragEnter={(e) => handleCellDragEnter(e, day, slot)}
                                            onDragOver={handleCellDragOver}
                                            onDragLeave={(e) => handleCellDragLeave(e, day, slot)}
                                            onDrop={(e) => handleDrop(e, day, slot)}
                                        >
                                            {/* Conflict tooltip */}
                                            {hasConflictHint && validation?.conflicts?.length > 0 && (
                                                <div style={{
                                                    position: 'absolute',
                                                    top: '50%',
                                                    left: '50%',
                                                    transform: 'translate(-50%, -50%)',
                                                    background: '#dc2626',
                                                    color: '#ffffff',
                                                    borderRadius: '0.5rem',
                                                    padding: '0.4rem 0.75rem',
                                                    fontSize: '0.72rem',
                                                    fontWeight: 700,
                                                    zIndex: 50,
                                                    pointerEvents: 'none',
                                                    whiteSpace: 'nowrap',
                                                    width: 'max-content',
                                                    boxShadow: '0 4px 16px rgba(0,0,0,0.45)',
                                                    border: '1.5px solid #ef4444',
                                                    letterSpacing: '0.01em',
                                                }}>
                                                    ⛔ {validation.conflicts[0]}
                                                </div>
                                            )}

                                            {/* Valid drop hint */}
                                            {activeDropCell === cellKey && validation?.valid === true && (
                                                <div style={{
                                                    position: 'absolute',
                                                    top: '50%',
                                                    left: '50%',
                                                    transform: 'translate(-50%, -50%)',
                                                    background: '#059669',          /* solid emerald — visible on any bg */
                                                    color: '#ffffff',
                                                    borderRadius: '0.5rem',
                                                    padding: '0.35rem 0.7rem',
                                                    fontSize: '0.72rem',
                                                    fontWeight: 700,
                                                    zIndex: 50,
                                                    pointerEvents: 'none',
                                                    whiteSpace: 'nowrap',
                                                    boxShadow: '0 4px 16px rgba(0,0,0,0.35)',
                                                    border: '1.5px solid #10b981',
                                                    letterSpacing: '0.01em',
                                                }}>
                                                    ✓ Drop to move here
                                                </div>
                                            )}

                                            {/* Class blocks */}
                                            {(timetable[day]?.[slot] || []).map((classItem, idx) => {
                                                const isDraggingThis = dragging?.entryId === classItem.entry_id;
                                                return (
                                                    <div
                                                        key={idx}
                                                        className={`class-block ${classItem.is_lab_session ? 'lab' : 'theory'} ${classItem.teacher_id === (user?.teacher_id || selectedTeacher) ? 'highlight-teacher' : ''}`}
                                                        draggable={isAdminOrHOD && !!classItem.entry_id}
                                                        onDragStart={(e) => handleDragStart(e, classItem, day, slot)}
                                                        onDragEnd={handleDragEnd}
                                                        style={{
                                                            cursor: isAdminOrHOD ? 'grab' : 'default',
                                                            opacity: isDraggingThis ? 0.35 : 1,
                                                            transition: 'opacity 0.2s ease, transform 0.2s ease',
                                                            transform: isDraggingThis ? 'scale(0.95)' : undefined,
                                                        }}
                                                        title={
                                                            isAdminOrHOD
                                                                ? `Drag to move ${classItem.course_code} (${classItem.section})`
                                                                : undefined
                                                        }
                                                    >
                                                        {/* Drag handle icon */}
                                                        {isAdminOrHOD && (
                                                            <div style={{
                                                                fontSize: '0.6rem',
                                                                color: 'var(--text-muted)',
                                                                marginBottom: '2px',
                                                                letterSpacing: '1px',
                                                                userSelect: 'none',
                                                            }}>
                                                                ⠿
                                                            </div>
                                                        )}
                                                        <div className="class-code">
                                                            {classItem.course_code}
                                                            {classItem.is_lab_session && <span className="lab-badge">LAB</span>}
                                                        </div>
                                                        <div className="class-teacher">{classItem.teacher_name}</div>
                                                        <div className="class-room">Room: {classItem.room}</div>
                                                        <div className="class-room">Sec: {classItem.section}</div>
                                                    </div>
                                                );
                                            })}
                                        </div>
                                    );
                                })}
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
                            fontSize: '1.25rem', fontWeight: 700,
                            color: 'var(--text-primary)', marginBottom: '0.25rem',
                        }}>
                            {verificationResult.valid ? '✅ Schedule Verified' : '⚠️ Issues Detected'}
                        </h3>
                        <p style={{
                            color: 'var(--text-muted)', fontSize: '0.875rem',
                            marginBottom: 'var(--spacing-md)',
                        }}>
                            {verificationResult.valid
                                ? 'No conflicts found. This schedule is ready to publish.'
                                : `${verificationResult.conflicts.length} conflict(s) need attention before publishing.`}
                        </p>

                        {!verificationResult.valid && (
                            <div style={{
                                background: 'var(--bg-tertiary)', borderRadius: 'var(--radius-md)',
                                padding: 'var(--spacing-sm) var(--spacing-md)',
                                marginBottom: 'var(--spacing-lg)',
                                maxHeight: '220px', overflowY: 'auto',
                                border: '1px solid var(--border)',
                            }}>
                                {verificationResult.conflicts.map((conflict, idx) => (
                                    <div key={idx} style={{
                                        padding: '0.5rem 0',
                                        borderBottom: idx < verificationResult.conflicts.length - 1 ? '1px solid var(--border)' : 'none',
                                        fontSize: '0.85rem', color: 'var(--text-primary)',
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
        </div>
    );
}

export default ViewTimetable;
