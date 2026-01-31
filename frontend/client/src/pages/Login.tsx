import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuthStore } from '../store/authStore';
import api from '../services/api';

const Login: React.FC = () => {
    const [email, setEmail] = useState('');
    const [password, setPassword] = useState('');
    const [error, setError] = useState('');
    const navigate = useNavigate();
    const login = useAuthStore((state) => state.login);

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        try {
            // For Sprint 1, we might not have a full JWT endpoint working perfectly 
            // without simplejwt installed in urls. 
            // mocking the login for local dev if backend auth fails (fallback)
            // BUT we should try the real endpoint first.

            const response = await api.post('/token/', { username: email, password });
            login(response.data.access, { username: email, role: 'ADMIN' }); // Todo: Fetch real role
            navigate('/dashboard');

        } catch (err: any) {
            console.error("Login Error:", err);
            setError(err.response?.data?.detail || 'Login failed. Check backend connection.');
        }
    };

    return (
        <div className="flex items-center justify-center min-h-screen bg-gray-100">
            <div className="px-8 py-6 mt-4 text-left bg-white shadow-lg rounded-xl h-[400px] w-[350px]">
                <h3 className="text-2xl font-bold text-center text-blue-600">Scheduler Login</h3>
                <form onSubmit={handleSubmit} className="mt-4">
                    <div className="mt-4">
                        <label className="block text-gray-700">Email</label>
                        <input
                            type="text"
                            placeholder="Email"
                            className="w-full px-4 py-2 mt-2 border rounded-md focus:outline-none focus:ring-1 focus:ring-blue-600"
                            value={email}
                            onChange={(e) => setEmail(e.target.value)}
                        />
                    </div>
                    <div className="mt-4">
                        <label className="block text-gray-700">Password</label>
                        <input
                            type="password"
                            placeholder="Password"
                            className="w-full px-4 py-2 mt-2 border rounded-md focus:outline-none focus:ring-1 focus:ring-blue-600"
                            value={password}
                            onChange={(e) => setPassword(e.target.value)}
                        />
                    </div>
                    <div className="flex items-baseline justify-between">
                        <button className="w-full px-6 py-2 mt-6 text-white bg-blue-600 rounded-lg hover:bg-blue-900">Login</button>
                    </div>
                    {error && <p className="mt-4 text-red-500 text-center">{error}</p>}
                </form>
            </div>
        </div>
    );
};

export default Login;
