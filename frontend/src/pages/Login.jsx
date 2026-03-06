import React, { useState } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { motion, AnimatePresence } from 'framer-motion';
import { User, Lock, Loader2, ArrowRight, LayoutGrid, Chrome, CheckCircle2 } from 'lucide-react';
import { GoogleLogin } from '@react-oauth/google';
import '../styles/Login.css';

/**
 * Login Page - Amrita Branded Edition
 * 
 * Handles user authentication and role-based redirection.
 */
const Login = () => {
    const [username, setUsername] = useState('');
    const [password, setPassword] = useState('');
    const [error, setError] = useState('');
    const [isLoading, setIsLoading] = useState(false);
    const [matchingUsers, setMatchingUsers] = useState([]);
    const [showSelection, setShowSelection] = useState(false);
    const [googleToken, setGoogleToken] = useState(null);

    const { login, googleLogin } = useAuth();
    const navigate = useNavigate();
    const location = useLocation();

    const from = location.state?.from?.pathname || '/';

    const handleLoginSuccess = (user) => {
        if (user?.role === 'FACULTY') {
            navigate('/timetable', { replace: true });
        } else {
            navigate(from, { replace: true });
        }
    };

    const handleSubmit = async (e) => {
        e.preventDefault();
        setError('');
        setIsLoading(true);

        const result = await login(username, password);

        if (result.success) {
            handleLoginSuccess(result.user);
        } else {
            setError(result.error);
        }
        setIsLoading(false);
    };

    const handleGoogleSuccess = async (credentialResponse) => {
        setError('');
        setIsLoading(true);
        const token = credentialResponse.credential;
        setGoogleToken(token);

        const result = await googleLogin(token);

        if (result.success) {
            if (result.needsSelection) {
                setMatchingUsers(result.users);
                setShowSelection(true);
            } else {
                handleLoginSuccess(result.user);
            }
        } else {
            setError(result.error);
        }
        setIsLoading(false);
    };

    const handleSelectUser = async (userId) => {
        setIsLoading(true);
        const result = await googleLogin(googleToken, userId);
        if (result.success) {
            handleLoginSuccess(result.user);
        } else {
            setError(result.error);
            setShowSelection(false);
        }
        setIsLoading(false);
    };

    return (
        <div className="login-page">

            {/* Left Section: Brand Visuals */}
            <motion.div
                initial={{ opacity: 0, x: -20 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ duration: 0.6 }}
                className="login-brand-section"
            >
                <div className="blob blob-1"></div>
                <div className="blob blob-2"></div>

                <div className="brand-content">
                    <motion.div
                        initial={{ scale: 0.9, opacity: 0 }}
                        animate={{ scale: 1, opacity: 1 }}
                        transition={{ delay: 0.2, duration: 0.5 }}
                        className="brand-logo-wrapper"
                    >
                        <LayoutGrid size={32} color="var(--primary-light)" />
                    </motion.div>

                    <motion.h1
                        initial={{ y: 20, opacity: 0 }}
                        animate={{ y: 0, opacity: 1 }}
                        transition={{ delay: 0.3, duration: 0.5 }}
                        className="brand-title"
                    >
                        Master your <br />
                        <span className="highlight-text">
                            Academic Schedule
                        </span>
                    </motion.h1>

                    <motion.p
                        initial={{ y: 20, opacity: 0 }}
                        animate={{ y: 0, opacity: 1 }}
                        transition={{ delay: 0.4, duration: 0.5 }}
                        className="brand-desc"
                    >
                        Automated conflict-free scheduling for Amrita University.
                        Optimize resources, manage faculty workloads, and generate timetables in seconds.
                    </motion.p>
                </div>
            </motion.div>

            {/* Right Section: Form */}
            <div className="login-form-section">
                <motion.div
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ duration: 0.5, delay: 0.1 }}
                    className="form-card"
                >
                    <div className="form-header">
                        <h2>Welcome back</h2>
                        <p>Sign in to access the dashboard.</p>
                    </div>

                    {error && (
                        <div className="error-alert">
                            <span>⚠️</span> {error}
                        </div>
                    )}

                    <AnimatePresence mode="wait">
                        {!showSelection ? (
                            <motion.div
                                key="login-form"
                                initial={{ opacity: 0 }}
                                animate={{ opacity: 1 }}
                                exit={{ opacity: 0 }}
                            >
                                <form onSubmit={handleSubmit}>
                                    {/* Username Field */}
                                    <div className="form-group">
                                        <label className="input-label">Username / Email</label>
                                        <div className="input-wrapper">
                                            <div className="input-icon">
                                                <User size={20} />
                                            </div>
                                            <input
                                                type="text"
                                                value={username}
                                                onChange={(e) => setUsername(e.target.value)}
                                                required
                                                className="input-field"
                                                placeholder="Enter your username"
                                            />
                                        </div>
                                    </div>

                                    {/* Password Field */}
                                    <div className="form-group">
                                        <label className="input-label">Password</label>
                                        <div className="input-wrapper">
                                            <div className="input-icon">
                                                <Lock size={20} />
                                            </div>
                                            <input
                                                type="password"
                                                value={password}
                                                onChange={(e) => setPassword(e.target.value)}
                                                required
                                                className="input-field"
                                                placeholder="••••••••"
                                            />
                                        </div>
                                    </div>

                                    <motion.button
                                        whileHover={{ scale: 1.02 }}
                                        whileTap={{ scale: 0.98 }}
                                        type="submit"
                                        disabled={isLoading}
                                        className="submit-btn"
                                    >
                                        {isLoading ? (
                                            <>
                                                <Loader2 className="btn-spinner" size={20} />
                                                <span>Verifying...</span>
                                            </>
                                        ) : (
                                            <>
                                                <span>Sign In</span>
                                                <ArrowRight size={18} />
                                            </>
                                        )}
                                    </motion.button>
                                </form>

                                <div className="divider">
                                    <span>Or continue with</span>
                                </div>

                                <div className="google-login-container">
                                    <GoogleLogin
                                        onSuccess={handleGoogleSuccess}
                                        onError={() => setError('Google Login Failed')}
                                        useOneTap
                                        width="100%"
                                        text="signin_with"
                                        shape="rectangular"
                                        theme="outline"
                                    />
                                </div>
                            </motion.div>
                        ) : (
                            <motion.div
                                key="account-selection"
                                initial={{ opacity: 0, x: 20 }}
                                animate={{ opacity: 1, x: 0 }}
                                exit={{ opacity: 0, x: -20 }}
                                className="selection-view"
                            >
                                <div className="selection-header">
                                    <h3>Select Account</h3>
                                    <p>Since you are using a master Gmail account, please select which profile you want to access.</p>
                                </div>

                                <div className="user-list">
                                    {matchingUsers.map(user => (
                                        <button
                                            key={user.id}
                                            onClick={() => handleSelectUser(user.id)}
                                            className="user-select-item"
                                            disabled={isLoading}
                                        >
                                            <div className="user-info">
                                                <span className="user-name">{user.display_name}</span>
                                                <span className="user-role">{user.role} ({user.username})</span>
                                            </div>
                                            <CheckCircle2 size={18} className="select-icon" />
                                        </button>
                                    ))}
                                </div>

                                <button
                                    onClick={() => setShowSelection(false)}
                                    className="back-btn"
                                >
                                    Back to Login
                                </button>
                            </motion.div>
                        )}
                    </AnimatePresence>

                    <div className="form-footer">
                        M3 System for Amrita University v1.0 © 2026
                    </div>
                </motion.div>
            </div>
        </div>
    );
};

export default Login;