import React from 'react';

/**
 * WorkloadChart Component
 * Visualizes faculty workload using a bar chart.
 * Highlights normal, warning (80%+), and overload (100%+) states.
 * 
 * @param {Array} facultyData - List of faculty with assigned_hours and max_hours
 */
const WorkloadChart = ({ facultyData }) => {
    // Handle empty state
    if (!facultyData || facultyData.length === 0) return <div className="loading">No faculty data available</div>;

    // Filter out entries without set capacity to avoid division by zero
    const validData = facultyData.filter(f => f.max_hours > 0);

    // Find the global maximum to scale all bars consistently
    const maxValue = Math.max(...validData.map(f => Math.max(f.assigned_hours || 0, f.max_hours)), 1);

    return (
        <div className="workload-chart-container" style={{ padding: '0.5rem' }}>
            <div className="chart-legend" style={{ display: 'flex', gap: '1.5rem', marginBottom: '1.5rem', fontSize: '0.85rem' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                    <div className="workload-fill normal" style={{ width: '12px', height: '12px', borderRadius: '2px' }}></div>
                    <span>Assigned Hours</span>
                </div>
                <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                    <div style={{ width: '12px', height: '12px', background: 'var(--bg-tertiary)', border: '1px solid var(--border)', borderRadius: '2px' }}></div>
                    <span>Max Capacity</span>
                </div>
                <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                    <div className="workload-fill danger" style={{ width: '12px', height: '12px', borderRadius: '2px' }}></div>
                    <span>Overload</span>
                </div>
            </div>

            <div className="bar-grid">
                {validData.map((faculty) => {
                    const assignedPercent = ((faculty.assigned_hours || 0) / maxValue) * 100;
                    const maxPercent = (faculty.max_hours / maxValue) * 100;
                    const isOverloaded = (faculty.assigned_hours || 0) > faculty.max_hours;
                    const isHighLoad = !isOverloaded && (faculty.assigned_hours || 0) >= faculty.max_hours * 0.8;

                    let fillClass = "normal";
                    if (isOverloaded) fillClass = "danger";
                    else if (isHighLoad) fillClass = "warning";

                    return (
                        <div key={faculty.id} className="workload-bar-container">
                            <div className="workload-label" title={faculty.name}>
                                {faculty.name}
                            </div>
                            <div className="workload-track">
                                {/* Max Capacity Indicator */}
                                <div
                                    style={{
                                        position: 'absolute',
                                        left: 0,
                                        top: 0,
                                        height: '100%',
                                        width: `${maxPercent}%`,
                                        opacity: 0.1,
                                        borderRight: '2px solid var(--text-muted)',
                                        zIndex: 1
                                    }}
                                ></div>
                                {/* Assigned Hours Bar */}
                                <div
                                    className={`workload-fill ${fillClass}`}
                                    style={{
                                        width: `${assignedPercent}%`,
                                        position: 'relative',
                                        zIndex: 2
                                    }}
                                ></div>
                            </div>
                            <div className="workload-meta">
                                {faculty.assigned_hours || 0}/{faculty.max_hours}
                            </div>
                        </div>
                    );
                })}
            </div>
        </div>
    );
};

export default WorkloadChart;
