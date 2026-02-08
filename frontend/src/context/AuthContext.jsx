import React, { createContext, useState, useEffect, useContext } from 'react';
import axios from 'axios';
import schedulerAPI from '../services/api';

const AuthContext = createContext();

export const useAuth = () => useContext(AuthContext);

export const AuthProvider = ({ children }) => {
    const [user, setUser] = useState(null);
    const [loading, setLoading] = useState(true);
    const [accessToken, setAccessToken] = useState(localStorage.getItem('access_token'));
    const [refreshToken, setRefreshToken] = useState(localStorage.getItem('refresh_token'));

    useEffect(() => {
        // Initialize from local storage or verify existing token
        if (accessToken) {
            // Configure axios default
            schedulerAPI.defaults.headers.common['Authorization'] = `Bearer ${accessToken}`;

            // Should verify token or fetch user profile here
            fetchUserProfile();
        } else {
            setLoading(false);
        }
    }, [accessToken]);

    const fetchUserProfile = async () => {
        try {
            const response = await schedulerAPI.get('/auth/me/');
            setUser(response.data);
        } catch (error) {
            console.error("Failed to fetch user profile", error);
            // If token invalid, try refresh or logout
            logout();
        } finally {
            setLoading(false);
        }
    };

    const login = async (username, password) => {
        try {
            const response = await schedulerAPI.post('/auth/token/', { username, password });
            const { access, refresh } = response.data;

            setAccessToken(access);
            setRefreshToken(refresh);
            localStorage.setItem('access_token', access);
            localStorage.setItem('refresh_token', refresh);

            schedulerAPI.defaults.headers.common['Authorization'] = `Bearer ${access}`;
            await fetchUserProfile();
            return { success: true };
        } catch (error) {
            console.error("Login failed", error);
            return {
                success: false,
                error: error.response?.data?.detail || 'Login failed. Please check your credentials.'
            };
        }
    };

    const logout = () => {
        setUser(null);
        setAccessToken(null);
        setRefreshToken(null);
        localStorage.removeItem('access_token');
        localStorage.removeItem('refresh_token');
        delete schedulerAPI.defaults.headers.common['Authorization'];
    };

    const value = {
        user,
        loading,
        accessToken,
        login,
        logout,
        isAuthenticated: !!user
    };

    return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
};
