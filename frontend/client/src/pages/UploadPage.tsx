import React, { useState } from 'react';
import api from '../services/api';
import { UploadCloud, CheckCircle, AlertCircle } from 'lucide-react';

const UploadPage: React.FC = () => {
    const [file, setFile] = useState<File | null>(null);
    const [type, setType] = useState('faculty');
    const [status, setStatus] = useState<'idle' | 'uploading' | 'success' | 'error'>('idle');
    const [message, setMessage] = useState('');

    const handleUpload = async () => {
        if (!file) return;

        const formData = new FormData();
        formData.append('file', file);

        setStatus('uploading');
        try {
            const res = await api.post(`/upload/${type}/`, formData, {
                headers: { 'Content-Type': 'multipart/form-data' },
            });
            setStatus('success');
            setMessage(`Successfully imported ${res.data.details.created} new records.`);
        } catch (err: any) {
            console.error("Upload Error:", err);
            setStatus('error');
            const status = err.response?.status;
            const errorMsg = err.response?.data?.error || err.response?.data?.detail || err.message;
            setMessage(`Failed (${status}): ${errorMsg}`);
        }
    };

    return (
        <div className="max-w-2xl mx-auto">
            <h2 className="text-2xl font-bold mb-6">Data Import</h2>

            <div className="bg-white p-8 rounded-xl shadow-sm border border-gray-100">
                <div className="mb-6">
                    <label className="block text-sm font-medium text-gray-700 mb-2">Data Type</label>
                    <button
                        type="button"
                        onClick={() => setType('faculty')}
                        className={`px-4 py-2 rounded-lg border ${type === 'faculty' ? 'bg-blue-50 border-blue-500 text-blue-700' : 'border-gray-200'}`}
                    >
                        Faculty
                    </button>
                    <button
                        type="button"
                        onClick={() => setType('classrooms')}
                        className={`px-4 py-2 rounded-lg border ${type === 'classrooms' ? 'bg-blue-50 border-blue-500 text-blue-700' : 'border-gray-200'}`}
                    >
                        Classrooms
                    </button>
                    <button
                        type="button"
                        onClick={() => setType('courses')}
                        className={`px-4 py-2 rounded-lg border ${type === 'courses' ? 'bg-blue-50 border-blue-500 text-blue-700' : 'border-gray-200'}`}
                    >
                        Courses
                    </button>
                    <button
                        type="button"
                        onClick={() => setType('sections')}
                        className={`px-4 py-2 rounded-lg border ${type === 'sections' ? 'bg-blue-50 border-blue-500 text-blue-700' : 'border-gray-200'}`}
                    >
                        Sections
                    </button>
                    <button
                        type="button"
                        onClick={() => setType('assignments')}
                        className={`px-4 py-2 rounded-lg border ${type === 'assignments' ? 'bg-blue-50 border-blue-500 text-blue-700' : 'border-gray-200'}`}
                    >
                        Assignments
                    </button>
                </div>
            </div>

            <div className="border-2 border-dashed border-gray-300 rounded-xl p-10 text-center hover:bg-gray-50 transition-colors">
                <input
                    type="file"
                    onChange={(e) => setFile(e.target.files?.[0] || null)}
                    className="hidden"
                    id="file-upload"
                    accept=".csv"
                />
                <label htmlFor="file-upload" className="cursor-pointer flex flex-col items-center">
                    <UploadCloud size={48} className="text-gray-400 mb-4" />
                    <span className="text-lg font-medium text-gray-700">
                        {file ? file.name : "Click to upload CSV"}
                    </span>
                    <span className="text-sm text-gray-500 mt-2">.csv files only</span>
                </label>
            </div>

            {status !== 'idle' && (
                <div className={`mt-6 p-4 rounded-lg flex items-center ${status === 'success' ? 'bg-green-50 text-green-700' : status === 'error' ? 'bg-red-50 text-red-700' : 'bg-blue-50 text-blue-700'}`}>
                    {status === 'success' && <CheckCircle className="mr-3" />}
                    {status === 'error' && <AlertCircle className="mr-3" />}
                    {status === 'uploading' && <span className="mr-3 loading">⏳</span>}
                    {message || "Uploading..."}
                </div>
            )}

            <button
                onClick={handleUpload}
                disabled={!file || status === 'uploading'}
                className="w-full mt-6 bg-blue-600 text-white py-3 rounded-lg hover:bg-blue-700 disabled:opacity-50"
            >
                {status === 'uploading' ? 'Processing...' : 'Start Import'}
            </button>
        </div>
    );
};

export default UploadPage;
