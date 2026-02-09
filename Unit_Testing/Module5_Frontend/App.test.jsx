import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import App from '../../frontend/src/App';
import * as api from '../../frontend/src/services/api';

// Mock the API module
vi.mock('../../frontend/src/services/api', () => {
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
    });

    it('Smoke Test: Renders successfully without crashing', () => {
        render(<App />);
        // Should verify some initial state, likely the login page or a redirect
        // Since we are unauthenticated by default, we expect to be on the login page
        // Look for "Sign In" or similar text from the Login component
    });

    it('Unauthenticated State: Protected route redirects to login', async () => {
        // Manually set the path to a protected route
        window.history.pushState({}, 'Dashboard', '/dashboard');

        render(<App />);

        // Expect to be redirected to Login
        // We can check for the presence of the username input field as a proxy for the login page
        expect(screen.getByPlaceholderText(/username/i)).toBeInTheDocument();
        // Ensure we are NOT seeing the Dashboard layout (e.g. Sidebar)
        expect(screen.queryByText('M3 Timetable')).not.toBeInTheDocument();
    });

    it('Login Flow: Successful login redirects to Dashboard', async () => {
        const user = userEvent.setup();
        render(<App />);

        // 1. Simulate typing
        const usernameInput = screen.getByPlaceholderText(/username/i);
        const passwordInput = screen.getByPlaceholderText(/••••••••/i);
        const submitButton = screen.getByRole('button', { name: /^Sign In$/i });

        await user.type(usernameInput, 'testadmin');
        await user.type(passwordInput, 'password123');

        // 2. Mock API response
        const mockAuthResponse = {
            data: {
                access: 'fake-access-token',
                refresh: 'fake-refresh-token',
            },
        };
        const mockUserResponse = {
            data: {
                username: 'testadmin',
                role: 'ADMIN',
            },
        };

        // Mock the post request for login (AuthContext uses default export)
        api.default.post.mockResolvedValueOnce(mockAuthResponse);

        // Mock the get request for user profile which is called after login
        api.default.get.mockResolvedValueOnce(mockUserResponse);


        // 3. Click Sign In
        await user.click(submitButton);

        // 4. Verify Redirect
        await waitFor(() => {
            // Verify sidebar is present (Dashboard loaded)
            expect(screen.getByText('M3 Timetable')).toBeInTheDocument();
        });
    });

    it('Error Handling: Shows error on failed login', async () => {
        const user = userEvent.setup();
        render(<App />);

        const usernameInput = screen.getByPlaceholderText(/username/i);
        const passwordInput = screen.getByPlaceholderText(/••••••••/i);
        const submitButton = screen.getByRole('button', { name: /^Sign In$/i });

        await user.type(usernameInput, 'wronguser');
        await user.type(passwordInput, 'wrongpass');

        // Mock API failure
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
