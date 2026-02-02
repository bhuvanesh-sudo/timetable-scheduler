import React, { useState, useCallback } from 'react';
import Papa from 'papaparse';
import api from '../services/api';
import { 
  UploadCloud, 
  FileSpreadsheet, 
  CheckCircle, 
  AlertCircle, 
  X, 
  ArrowRight 
} from 'lucide-react';

const UploadPage: React.FC = () => {
    // State Management
    const [file, setFile] = useState<File | null>(null);
    const [type, setType] = useState('faculty');
    const [previewData, setPreviewData] = useState<any[]>([]);
    const [headers, setHeaders] = useState<string[]>([]);
    const [status, setStatus] = useState<'idle' | 'analyzing' | 'ready' | 'uploading' | 'success' | 'error'>('idle');
    const [uploadResult, setUploadResult] = useState<any>(null);
    const [errorMessage, setErrorMessage] = useState('');

    // 1. Handle File Selection & Local Parsing
    const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
        const selectedFile = e.target.files?.[0];
        if (!selectedFile) return;

        setFile(selectedFile);
        setStatus('analyzing');
        setErrorMessage('');
        setUploadResult(null);

        // Parse CSV locally for preview
        Papa.parse(selectedFile, {
            header: true,
            skipEmptyLines: true,
            preview: 5, // Only grab first 5 rows for speed
            complete: (results) => {
                if (results.data && results.data.length > 0) {
                    setHeaders(Object.keys(results.data[0] as object));
                    setPreviewData(results.data);
                    setStatus('ready');
                } else {
                    setStatus('error');
                    setErrorMessage('The CSV file appears to be empty or invalid.');
                }
            },
            error: (error) => {
                setStatus('error');
                setErrorMessage(`Parsing Error: ${error.message}`);
            }
        });
    };

    // 2. Clear Selection
    const handleClear = () => {
        setFile(null);
        setPreviewData([]);
        setStatus('idle');
        setUploadResult(null);
        setErrorMessage('');
    };

    // 3. Send to Server
    const handleUpload = async () => {
        if (!file) return;

        setStatus('uploading');
        const formData = new FormData();
        formData.append('file', file);

        try {
            const res = await api.post(`/upload/${type}/`, formData, {
                headers: { 'Content-Type': 'multipart/form-data' },
            });
            setStatus('success');
            setUploadResult(res.data.details); // Expecting { created: 10, errors: [] }
        } catch (err: any) {
            console.error("Upload Error:", err);
            setStatus('error');
            const errorMsg = err.response?.data?.error || "Server connection failed";
            setErrorMessage(errorMsg);
        }
    };

    return (
        <div className="max-w-4xl mx-auto space-y-8">
            
            {/* Header Section */}
            <div>
                <h2 className="text-2xl font-bold text-gray-900">Data Import Wizard</h2>
                <p className="text-gray-500 mt-1">Bulk import institutional data via CSV.</p>
            </div>

            {/* Type Selector Tabs */}
            <div className="bg-white p-1 rounded-xl border border-gray-200 inline-flex shadow-sm">
                {['faculty', 'classrooms', 'courses', 'sections', 'assignments'].map((t) => (
                    <button
                        key={t}
                        onClick={() => { setType(t); handleClear(); }}
                        className={`px-4 py-2 rounded-lg text-sm font-medium transition-all ${
                            type === t 
                            ? 'bg-blue-100 text-blue-700 shadow-sm' 
                            : 'text-gray-600 hover:bg-gray-50'
                        }`}
                    >
                        {t.charAt(0).toUpperCase() + t.slice(1)}
                    </button>
                ))}
            </div>

            {/* Main Upload Area */}
            <div className="bg-white rounded-xl shadow-sm border border-gray-200 overflow-hidden">
                
                {/* Stage 1: File Drop Zone (Only show if no file selected) */}
                {status === 'idle' && (
                    <div className="p-12 text-center border-b border-gray-100">
                        <div className="border-2 border-dashed border-gray-300 rounded-xl p-10 hover:bg-blue-50 hover:border-blue-400 transition-colors cursor-pointer group relative">
                            <input
                                type="file"
                                onChange={handleFileSelect}
                                className="absolute inset-0 w-full h-full opacity-0 cursor-pointer"
                                accept=".csv"
                            />
                            <div className="flex flex-col items-center">
                                <div className="w-16 h-16 bg-blue-100 text-blue-600 rounded-full flex items-center justify-center mb-4 group-hover:scale-110 transition-transform">
                                    <UploadCloud size={32} />
                                </div>
                                <h3 className="text-lg font-semibold text-gray-900">Click to upload {type} data</h3>
                                <p className="text-sm text-gray-500 mt-2">or drag and drop CSV file here</p>
                            </div>
                        </div>
                        <div className="mt-6 flex justify-center gap-4 text-sm text-gray-500">
                            <span className="flex items-center"><CheckCircle size={16} className="mr-1 text-green-500"/> UTF-8 Encoding</span>
                            <span className="flex items-center"><CheckCircle size={16} className="mr-1 text-green-500"/> Comma Separated</span>
                        </div>
                    </div>
                )}

                {/* Stage 2: Data Preview (Show if file is valid) */}
                {status !== 'idle' && status !== 'error' && (
                    <div className="p-6">
                        <div className="flex items-center justify-between mb-6">
                            <div className="flex items-center space-x-4">
                                <div className="p-3 bg-green-100 text-green-700 rounded-lg">
                                    <FileSpreadsheet size={24} />
                                </div>
                                <div>
                                    <h4 className="font-semibold text-gray-900">{file?.name}</h4>
                                    <p className="text-sm text-gray-500">{(file!.size / 1024).toFixed(1)} KB • {headers.length} Columns</p>
                                </div>
                            </div>
                            <button onClick={handleClear} className="p-2 hover:bg-gray-100 rounded-full text-gray-400 hover:text-red-500 transition-colors">
                                <X size={20} />
                            </button>
                        </div>

                        {/* The Preview Table */}
                        <div className="border rounded-lg overflow-x-auto mb-6 bg-gray-50">
                            <table className="w-full text-sm text-left">
                                <thead className="text-xs text-gray-500 uppercase bg-gray-100 border-b">
                                    <tr>
                                        {headers.map((h) => <th key={h} className="px-4 py-3 font-medium">{h}</th>)}
                                    </tr>
                                </thead>
                                <tbody>
                                    {previewData.map((row, i) => (
                                        <tr key={i} className="border-b last:border-0 hover:bg-white">
                                            {headers.map((h) => (
                                                <td key={`${i}-${h}`} className="px-4 py-2 font-mono text-gray-700 whitespace-nowrap">
                                                    {row[h]}
                                                </td>
                                            ))}
                                        </tr>
                                    ))}
                                </tbody>
                            </table>
                            <div className="px-4 py-2 text-xs text-gray-400 text-center bg-gray-50 border-t">
                                Showing first 5 rows of preview
                            </div>
                        </div>

                        {/* Action Bar */}
                        {status === 'ready' && (
                            <div className="flex justify-end">
                                <button
                                    onClick={handleUpload}
                                    className="flex items-center bg-blue-600 text-white px-6 py-2.5 rounded-lg hover:bg-blue-700 transition-all shadow-sm hover:shadow-md"
                                >
                                    Start Import <ArrowRight size={18} className="ml-2" />
                                </button>
                            </div>
                        )}

                        {/* Loading State */}
                        {status === 'uploading' && (
                            <div className="text-center py-8">
                                <div className="animate-spin w-8 h-8 border-4 border-blue-600 border-t-transparent rounded-full mx-auto mb-4"></div>
                                <p className="text-gray-600 font-medium">Processing records...</p>
                            </div>
                        )}

                        {/* Success State */}
                        {status === 'success' && uploadResult && (
                            <div className="bg-green-50 border border-green-200 rounded-lg p-4 animate-fade-in">
                                <div className="flex items-start">
                                    <CheckCircle className="text-green-600 mt-1 mr-3 flex-shrink-0" />
                                    <div>
                                        <h4 className="font-bold text-green-800">Import Successful!</h4>
                                        <p className="text-green-700 mt-1">
                                            Successfully processed <strong>{uploadResult.created || 0}</strong> new records.
                                        </p>
                                        {/* If your backend returns details about duplicates/updates, display them here */}
                                        {uploadResult.skipped > 0 && (
                                            <p className="text-sm text-green-600 mt-2">
                                                Note: {uploadResult.skipped} records were skipped (duplicates).
                                            </p>
                                        )}
                                        <button 
                                            onClick={handleClear}
                                            className="mt-4 text-sm font-medium text-green-700 hover:text-green-900 underline"
                                        >
                                            Upload another file
                                        </button>
                                    </div>
                                </div>
                            </div>
                        )}
                    </div>
                )}

                {/* Error State */}
                {status === 'error' && (
                    <div className="p-6 bg-red-50 border-t border-red-100 flex items-start">
                        <AlertCircle className="text-red-600 mt-1 mr-3 flex-shrink-0" />
                        <div className="flex-1">
                            <h4 className="font-bold text-red-800">Import Failed</h4>
                            <p className="text-red-700 mt-1">{errorMessage}</p>
                            <button 
                                onClick={handleClear}
                                className="mt-3 text-sm font-medium text-red-700 hover:text-red-900 bg-red-100 px-3 py-1 rounded"
                            >
                                Try Again
                            </button>
                        </div>
                    </div>
                )}
            </div>
        </div>
    );
};

export default UploadPage;