/**
 * Analytics Page
 * 
 * Author: Frontend Team (Bhuvanesh, Akshitha)
 */

import { useState, useEffect } from 'react';
import { scheduleAPI, schedulerAPI } from '../services/api';

function Analytics() {
    const [schedules, setSchedules] = useState([]);
    const [selectedSchedule, setSelectedSchedule] = useState('');
    const [workloadData, setWorkloadData] = useState([]);
    const [roomData, setRoomData] = useState([]);
    const [loading, setLoading] = useState(false);

    useEffect(() => {
        loadSchedules();
    }, []);

    const loadSchedules = async () => {
        try {
            const response = await scheduleAPI.getAll();
            setSchedules(response.data.results || []);
        } catch (error) {
            console.error('Error loading schedules:', error);
        }
    };

    const loadAnalytics = async () => {
        if (!selectedSchedule) return;

        setLoading(true);
        try {
            const [workload, rooms] = await Promise.all([
                schedulerAPI.getWorkload(selectedSchedule),
                schedulerAPI.getRoomUtilization(selectedSchedule),
            ]);
            setWorkloadData(workload.data);
            setRoomData(rooms.data);
        } catch (error) {
            console.error('Error loading analytics:', error);
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        if (selectedSchedule) {
            loadAnalytics();
        }
    }, [selectedSchedule]);

    return (
        <div>
            <div className="page-header">
                <h1 className="page-title">Analytics</h1>
                <p className="page-description">Workload and utilization analytics</p>
            </div>

            {/* Schedule Selection */}
            <div className="card">
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
                </div>
            </div>

            {loading && (
                <div className="loading">
                    <div className="spinner"></div>
                    <p>Loading analytics...</p>
                </div>
            )}

            {!loading && workloadData.length > 0 && (
                <>
                    {/* Faculty Workload */}
                    <div className="card">
                        <div className="card-header">
                            <h2 className="card-title">Faculty Workload Distribution</h2>
                        </div>
                        <div className="table-container">
                            <table className="data-table">
                                <thead>
                                    <tr>
                                        <th>Teacher ID</th>
                                        <th>Teacher Name</th>
                                        <th>Assigned Hours</th>
                                        <th>Max Hours</th>
                                        <th>Utilization</th>
                                    </tr>
                                </thead>
                                <tbody>
                                    {workloadData.map((item) => (
                                        <tr key={item.teacher_id}>
                                            <td>{item.teacher_id}</td>
                                            <td>{item.teacher_name}</td>
                                            <td>{item.total_hours}</td>
                                            <td>{item.max_hours}</td>
                                            <td>
                                                <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                                                    <div style={{
                                                        width: '100px',
                                                        height: '8px',
                                                        background: 'var(--bg-tertiary)',
                                                        borderRadius: '4px',
                                                        overflow: 'hidden'
                                                    }}>
                                                        <div style={{
                                                            width: `${Math.min(item.utilization, 100)}%`,
                                                            height: '100%',
                                                            background: item.utilization > 90 ? 'var(--danger)' :
                                                                item.utilization > 70 ? 'var(--warning)' :
                                                                    'var(--success)'
                                                        }}></div>
                                                    </div>
                                                    <span>{item.utilization}%</span>
                                                </div>
                                            </td>
                                        </tr>
                                    ))}
                                </tbody>
                            </table>
                        </div>
                    </div>

                    {/* Room Utilization */}
                    <div className="card">
                        <div className="card-header">
                            <h2 className="card-title">Room Utilization</h2>
                        </div>
                        <div className="table-container">
                            <table className="data-table">
                                <thead>
                                    <tr>
                                        <th>Room ID</th>
                                        <th>Room Type</th>
                                        <th>Slots Used</th>
                                        <th>Utilization</th>
                                    </tr>
                                </thead>
                                <tbody>
                                    {roomData.map((item) => (
                                        <tr key={item.room_id}>
                                            <td>{item.room_id}</td>
                                            <td>{item.room_type}</td>
                                            <td>{item.total_slots_used} / 40</td>
                                            <td>
                                                <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                                                    <div style={{
                                                        width: '100px',
                                                        height: '8px',
                                                        background: 'var(--bg-tertiary)',
                                                        borderRadius: '4px',
                                                        overflow: 'hidden'
                                                    }}>
                                                        <div style={{
                                                            width: `${Math.min(item.utilization, 100)}%`,
                                                            height: '100%',
                                                            background: 'var(--primary)'
                                                        }}></div>
                                                    </div>
                                                    <span>{item.utilization}%</span>
                                                </div>
                                            </td>
                                        </tr>
                                    ))}
                                </tbody>
                            </table>
                        </div>
                    </div>
                </>
            )}

            {!selectedSchedule && (
                <div className="alert alert-info">
                    Please select a schedule to view analytics.
                </div>
            )}
        </div>
    );
}

export default Analytics;
