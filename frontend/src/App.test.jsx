import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import App from './App';
import * as api from './services/api';

// Mock the API module
vi.mock('./services/api', () => {
    const mockRequest = {
        post: vi.fn(),
        get: vi.fn(),
        put: vi.fn(),
        delete: vi.fn(),
        defaults: {
            headers: { common: {} },
        },
        interceptors: {
            request: { use: vi.fn(), eject: vi.fn() },
            response: { use: vi.fn(), eject: vi.fn() },
        },
    };

    return {
        default: mockRequest,
        schedulerAPI: {
            post: vi.fn(),
            get: vi.fn(),
            getWorkload: vi.fn().mockResolvedValue({ data: [] }),
            getRoomUtilization: vi.fn().mockResolvedValue({ data: [] }),
        },
        teacherAPI: { getAll: vi.fn().mockResolvedValue({ data: [] }) },
        courseAPI: { getAll: vi.fn().mockResolvedValue({ data: [] }) },
        roomAPI: { getAll: vi.fn().mockResolvedValue({ data: [] }) },
        sectionAPI: { getAll: vi.fn().mockResolvedValue({ data: [] }) },
        scheduleAPI: { getAll: vi.fn().mockResolvedValue({ data: [] }) },
        auditLogAPI: { getAll: vi.fn().mockResolvedValue({ data: [] }) },
        userAPI: { getAll: vi.fn().mockResolvedValue({ data: [] }) },
        changeRequestAPI: { getAll: vi.fn().mockResolvedValue({ data: [] }) },
    };
});

describe('App Integration Tests', () => {
    beforeEach(() => {
        vi.clearAllMocks();
        localStorage.clear();
        // Clear auth headers
        if (api.default.defaults.headers.common) {
            delete api.default.defaults.headers.common['Authorization'];
        }
    });

    it('Smoke Test: Renders successfully without crashing', () => {
        render(<App />);
    });

    it('Unauthenticated State: Protected route redirects to login', async () => {
        window.history.pushState({}, 'Dashboard', '/dashboard');

        render(<App />);

        expect(screen.getByPlaceholderText(/username/i)).toBeInTheDocument();
        // Check for absence of dashboard indicator
        expect(screen.queryByText(/System Admin Dashboard/i)).not.toBeInTheDocument();
    });

    it('Login Flow: Successful login redirects to Dashboard', async () => {
        const user = userEvent.setup();
        render(<App />);

        const usernameInput = screen.getByPlaceholderText(/username/i);
        const passwordInput = screen.getByPlaceholderText(/••••••••/i);
        const submitButton = screen.getByRole('button', { name: /^Sign In$/i });

        await user.type(usernameInput, 'testadmin');
        await user.type(passwordInput, 'password123');

        // Mock endpoints specifically as AuthContext calls them
        api.default.post.mockImplementation((url) => {
            if (url === '/auth/token/' || url.endsWith('/auth/token/')) {
                return Promise.resolve({
                    data: {
                        access: 'fake-access-token',
                        refresh: 'fake-refresh-token',
                    }
                });
            }
            return Promise.reject(new Error('Unexpected POST to ' + url));
        });

        api.default.get.mockImplementation((url) => {
            if (url === '/auth/me/' || url.endsWith('/auth/me/')) {
                return Promise.resolve({
                    data: {
                        username: 'testadmin',
                        role: 'ADMIN',
                        department: 'Computer Science'
                    }
                });
            }
            return Promise.resolve({ data: { results: [], count: 0 } });
        });

        await user.click(submitButton);

        // Wait for dashboard content - look for text that actually exists
        await waitFor(() => {
            expect(screen.getByText(/System Admin Dashboard/i)).toBeInTheDocument();
        }, { timeout: 3000 });
    });

    it('Error Handling: Shows error on failed login', async () => {
        const user = userEvent.setup();
        render(<App />);

        const usernameInput = screen.getByPlaceholderText(/username/i);
        const passwordInput = screen.getByPlaceholderText(/••••••••/i);
        const submitButton = screen.getByRole('button', { name: /^Sign In$/i });

        await user.type(usernameInput, 'wronguser');
        await user.type(passwordInput, 'wrongpass');

        const mockError = {
            response: {
                data: {
                    detail: 'Invalid credentials',
                },
                status: 401,
            },
        };

        api.default.post.mockRejectedValueOnce(mockError);

        await user.click(submitButton);

        // Check for error message
        await waitFor(() => {
            expect(screen.getByText(/invalid credentials/i)).toBeInTheDocument();
        });
    });
});
