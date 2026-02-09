import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import tailwindcss from '@tailwindcss/vite'

// https://vite.dev/config/
export default defineConfig({
  plugins: [
    react(),
    tailwindcss(),
  ],
  test: {
    globals: true,
    environment: 'jsdom',
    setupFiles: './src/setupTests.js',
    include: ['../Unit_Testing/Module5_Frontend/**/*.test.jsx'],
  },
  resolve: {
    alias: {
      react: '/home/bv-fedora/Documents/Projects/timetable-scheduler/frontend/node_modules/react',
      'react/jsx-dev-runtime': '/home/bv-fedora/Documents/Projects/timetable-scheduler/frontend/node_modules/react/jsx-dev-runtime.js',
      'react/jsx-runtime': '/home/bv-fedora/Documents/Projects/timetable-scheduler/frontend/node_modules/react/jsx-runtime.js',
      '@testing-library/react': '/home/bv-fedora/Documents/Projects/timetable-scheduler/frontend/node_modules/@testing-library/react',
      '@testing-library/user-event': '/home/bv-fedora/Documents/Projects/timetable-scheduler/frontend/node_modules/@testing-library/user-event',
    },
  },
  server: {
    fs: {
      allow: ['..'],
    },
  },
})