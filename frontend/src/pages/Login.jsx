import React, { useState } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import '../styles/Login.css'; // We'll create this simple CSS

const Login = () => {
    const [username, setUsername] = useState('');
    const [password, setPassword] = useState('');
    const [selectedRole, setSelectedRole] = useState('HOD'); // Default to HOD
    const [error, setError] = useState('');
    const [isLoading, setIsLoading] = useState(false);
    const { login } = useAuth();
    const navigate = useNavigate();
    const location = useLocation();

    const from = location.state?.from?.pathname || '/';

    const handleSubmit = async (e) => {
        e.preventDefault();
        setError('');
        setIsLoading(true);

        const result = await login(username, password);

        if (result.success) {
            navigate(from, { replace: true });
        } else {
            setError(result.error);
        }
        setIsLoading(false);
    };

    return (
        <div className="login-container">
            <div className="login-card">
                <div className="login-header">
                    <h1>M3 HOD Portal</h1>
                    <p>Enter Credentials</p>
                </div>

                <div className="role-selector">
                    <button
                        type="button"
                        className={`role-tab ${selectedRole === 'ADMIN' ? 'active' : ''}`}
                        onClick={() => setSelectedRole('ADMIN')}
                    >
                        Administrator
                    </button>
                    <button
                        type="button"
                        className={`role-tab ${selectedRole === 'HOD' ? 'active' : ''}`}
                        onClick={() => setSelectedRole('HOD')}
                    >
                        HOD
                    </button>
                    <button
                        type="button"
                        className={`role-tab ${selectedRole === 'FACULTY' ? 'active' : ''}`}
                        onClick={() => setSelectedRole('FACULTY')}
                    >
                        Faculty
                    </button>
                </div>

                {error && <div className="login-error">{error}</div>}

                <form onSubmit={handleSubmit} className="login-form">
                    <div className="form-group">
                        <label htmlFor="username">Username / Email</label>
                        <input
                            type="text"
                            id="username"
                            value={username}
                            onChange={(e) => setUsername(e.target.value)}
                            placeholder="Enter your username"
                            required
                        />
                    </div>

                    <div className="form-group">
                        <label htmlFor="password">Password</label>
                        <input
                            type="password"
                            id="password"
                            value={password}
                            onChange={(e) => setPassword(e.target.value)}
                            placeholder="Enter your password"
                            required
                        />
                    </div>

                    <button type="submit" className="login-btn" disabled={isLoading}>
                        {isLoading ? 'Signing in...' : 'Sign In'}
                    </button>

                    <div className="login-divider">
                        <span>OR</span>
                    </div>

                    <button type="button" className="google-btn" disabled>
                        Sign in with Google (Coming Soon)
                    </button>
                </form>
            </div>
        </div>
    );
};

export default Login;
