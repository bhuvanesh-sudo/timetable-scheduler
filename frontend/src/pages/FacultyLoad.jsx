import { useState, useEffect } from 'react';
import { schedulerAPI, scheduleAPI } from '../services/api';

function FacultyLoad() {
    const [facultyData, setFacultyData] = useState([]);
    const [schedules, setSchedules] = useState([]);
    const [selectedSchedule, setSelectedSchedule] = useState('');
    const [loading, setLoading] = useState(false);
    const [searchTerm, setSearchTerm] = useState('');

    useEffect(() => {
        loadSchedules();
    }, []);

    useEffect(() => {
        loadFacultySummary();
    }, [selectedSchedule]);

    const loadSchedules = async () => {
        try {
            const res = await scheduleAPI.getAll();
            const data = res.data.results || res.data || [];
            setSchedules(data);
            if (data.length > 0) {
                setSelectedSchedule(data[0].schedule_id);
            }
        } catch (err) {
            console.error('Error loading schedules:', err);
        }
    };

    const loadFacultySummary = async () => {
        setLoading(true);
        try {
            const res = await schedulerAPI.getFacultySummary(selectedSchedule);
            setFacultyData(res.data);
        } catch (err) {
            console.error('Error loading faculty summary:', err);
        } finally {
            setLoading(false);
        }
    };

    const filteredFaculty = facultyData.filter(f => {
        const search = searchTerm.toLowerCase();
        const matchesBasic = f.teacher_name.toLowerCase().includes(search) ||
            f.department.toLowerCase().includes(search);

        const matchesCore = f.core_assignments.some(c => c.course_name.toLowerCase().includes(search));
        const matchesElective = f.elective_assignments.some(c => c.course_name.toLowerCase().includes(search));

        return matchesBasic || matchesCore || matchesElective;
    });

    return (
        <div className="fade-in">
            <div className="page-header">
                <h1 className="page-title">Faculty Load & Mappings</h1>
                <p className="page-description">
                    View faculty member course mappings and their current workload for the academic year.
                </p>
            </div>

            <div className="card" style={{ marginBottom: '1.5rem' }}>
                <div style={{ display: 'flex', gap: '1rem', flexWrap: 'wrap' }}>
                    <div className="filter-group" style={{ flex: 1, minWidth: '200px' }}>
                        <label className="filter-label">Select Schedule for Workload</label>
                        <select
                            className="filter-select"
                            value={selectedSchedule}
                            onChange={(e) => setSelectedSchedule(e.target.value)}
                        >
                            <option value="">-- No Schedule (View Mappings Only) --</option>
                            {schedules.map((s) => (
                                <option key={s.schedule_id} value={s.schedule_id}>
                                    {s.name} (Year {s.year}, {s.semester})
                                </option>
                            ))}
                        </select>
                    </div>
                    <div className="filter-group" style={{ flex: 1, minWidth: '200px' }}>
                        <label className="filter-label">Search Faculty or Course</label>
                        <input
                            type="text"
                            className="filter-select"
                            placeholder="Name, dept, or course name..."
                            value={searchTerm}
                            onChange={(e) => setSearchTerm(e.target.value)}
                        />
                    </div>
                </div>
            </div>

            {loading ? (
                <div className="loading">
                    <div className="spinner"></div>
                    <p>Loading faculty data...</p>
                </div>
            ) : (
                <div className="card">
                    <div className="table-responsive">
                        <table className="data-table">
                            <thead>
                                <tr>
                                    <th>Faculty Name</th>
                                    <th>Dept</th>
                                    <th>Courses Handled</th>
                                    <th>Sections</th>
                                    <th>Workload</th>
                                    <th>Utilization</th>
                                </tr>
                            </thead>
                            <tbody>
                                {filteredFaculty.length > 0 ? (
                                    filteredFaculty.map((f) => {
                                        const utilization = (f.current_load / f.max_hours) * 100;
                                        let statusClass = 'success';
                                        if (utilization > 95) statusClass = 'danger'; // 95% limit
                                        else if (utilization > 70) statusClass = 'warning';

                                        const allAssignments = [
                                            ...f.core_assignments.map(c => ({ ...c, type: 'core' })),
                                            ...f.elective_assignments.map(c => ({ ...c, type: 'elective' }))
                                        ];

                                        return (
                                            <tr key={f.teacher_id}>
                                                <td style={{ verticalAlign: 'top' }}>
                                                    <div style={{ fontWeight: 600 }}>{f.teacher_name}</div>
                                                    <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>{f.teacher_id}</div>
                                                </td>
                                                <td style={{ verticalAlign: 'top' }}>{f.department}</td>
                                                <td style={{ verticalAlign: 'top' }}>
                                                    <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
                                                        {allAssignments.map((a, i) => (
                                                            <div key={i} style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                                                                <span className={`badge-pill badge-${a.type === 'core' ? 'info' : 'primary'}`} style={{ fontSize: '0.7rem', minWidth: '80px', textAlign: 'center' }}>
                                                                    {a.type.toUpperCase()}
                                                                </span>
                                                                <span style={{ fontSize: '0.85rem', fontWeight: 500 }}>{a.course_name}</span>
                                                            </div>
                                                        ))}
                                                        {allAssignments.length === 0 && <span style={{ color: 'var(--text-muted)', fontSize: '0.85rem' }}>No assignments</span>}
                                                    </div>
                                                </td>
                                                <td style={{ verticalAlign: 'top' }}>
                                                    <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
                                                        {allAssignments.map((a, i) => (
                                                            <div key={i} style={{ height: '22px', display: 'flex', alignItems: 'center' }}>
                                                                {a.sections && a.sections.length > 0 ? (
                                                                    <div style={{ display: 'flex', gap: '4px' }}>
                                                                        {a.sections.map((s, si) => (
                                                                            <span key={si} className="badge-pill" style={{ fontSize: '0.7rem', background: '#e2e8f0', color: '#475569' }}>
                                                                                {s}
                                                                            </span>
                                                                        ))}
                                                                    </div>
                                                                ) : (
                                                                    <span style={{ fontSize: '0.75rem', color: '#94a3b8' }}>N/A</span>
                                                                )}
                                                            </div>
                                                        ))}
                                                    </div>
                                                </td>
                                                <td style={{ verticalAlign: 'top' }}>
                                                    <div style={{ fontWeight: 600 }}>{f.current_load} / {f.max_hours} hrs</div>
                                                </td>
                                                <td style={{ verticalAlign: 'top' }}>
                                                    <div className="progress-container" style={{ width: '100px' }}>
                                                        <div
                                                            className={`progress-bar bg-${statusClass}`}
                                                            style={{ width: `${Math.min(utilization, 100)}%` }}
                                                        ></div>
                                                    </div>
                                                    <span style={{ fontSize: '0.75rem' }}>{Math.round(utilization)}%</span>
                                                </td>
                                            </tr>
                                        );
                                    })
                                ) : (
                                    <tr>
                                        <td colSpan="6" style={{ textAlign: 'center', padding: '2rem' }}>No faculty found</td>
                                    </tr>
                                )}
                            </tbody>
                        </table>
                    </div>
                </div>
            )}
        </div>
    );
}

export default FacultyLoad;
