import { BrowserRouter, Routes, Route, Navigate, Outlet } from 'react-router-dom';
import Login from './pages/Login';
import DashboardLayout from './layouts/DashboardLayout';
import UploadPage from './pages/UploadPage';
import { useAuthStore } from './store/authStore';

const ProtectedRoute = () => {
  const isAuthenticated = useAuthStore((state) => state.isAuthenticated);
  return isAuthenticated ? <Outlet /> : <Navigate to="/" />;
};

function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<Login />} />

        <Route element={<ProtectedRoute />}>
          <Route path="/dashboard" element={<DashboardLayout />}>
            <Route index element={<div className="p-4"><h3>Welcome to the Scheduler Dashboard</h3></div>} />
            <Route path="upload" element={<UploadPage />} />
            <Route path="schedule" element={<div>Schedule Grid Coming Soon...</div>} />
          </Route>
        </Route>

      </Routes>
    </BrowserRouter>
  );
}

export default App;
