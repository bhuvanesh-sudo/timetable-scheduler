import { describe, it, expect, beforeEach, vi } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import { ThemeProvider, useTheme } from '../../frontend/src/context/ThemeContext';
import ViewTimetable from '../../frontend/src/pages/ViewTimetable';
import React from 'react';

// Mock matchMedia for JSDom
Object.defineProperty(window, 'matchMedia', {
    writable: true,
    value: vi.fn().mockImplementation(query => ({
        matches: false,
        media: query,
        onchange: null,
        addListener: vi.fn(),
        removeListener: vi.fn(),
        addEventListener: vi.fn(),
        removeEventListener: vi.fn(),
        dispatchEvent: vi.fn(),
    })),
});

const ThemeTestComponent = () => {
    const { theme, toggleTheme } = useTheme();
    return (
        <div>
            <span data-testid="theme-value">{theme}</span>
            <button onClick={toggleTheme}>Toggle</button>
        </div>
    );
};

describe('Frontend Component Testing (Module 5)', () => {
    describe('Theme System', () => {
        beforeEach(() => {
            localStorage.clear();
            document.documentElement.removeAttribute('data-theme');
        });

        it('should toggle theme correctly', () => {
            render(<ThemeProvider><ThemeTestComponent /></ThemeProvider>);
            expect(screen.getByTestId('theme-value').textContent).toBe('light');
            fireEvent.click(screen.getByText('Toggle'));
            expect(screen.getByTestId('theme-value').textContent).toBe('dark');
        });
    });

    describe('Timetable Grid', () => {
        it('renders the view timetable page title', () => {
            // Minimal render for existence check
            render(<ThemeProvider><ViewTimetable /></ThemeProvider>);
            expect(screen.getByText('View Timetable')).toBeDefined();
        });
    });
});
