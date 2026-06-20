// src/App.jsx
import { Routes, Route, Navigate } from "react-router-dom";
import { useAuth } from "./context/AuthContext";

import ProtectedRoute from "./components/ProtectedRoute";
import Layout from "./components/Layout";

// Shared pages
import Login from "./pages/Login";
import Profile from "./pages/Profile";
import ChangePassword from "./pages/ChangePassword";

// Management pages (these match the real filenames in src/pages/management)
import Overview from "./pages/management/Overview";
import Students from "./pages/management/Students";
import Teachers from "./pages/management/Teachers";
import Assignments from "./pages/management/Assignments";
import Ebooks from "./pages/management/Ebooks";
import Holidays from "./pages/management/Holidays";
import Payments from "./pages/management/Payments";
import Users from "./pages/management/Users";
import Countries from "./pages/management/Countries";
import TeacherEbooks from "./pages/teacher/Ebooks";

// Teacher pages
import TeacherDashboard from "./pages/teacher/TeacherDashboard";
import Schedule from "./pages/teacher/Schedule";

// Student pages
import StudentDashboard from "./pages/student/StudentDashboard";

export default function App() {
  const { user, loading } = useAuth();

  // Wait until we know if the user is logged in (avoids a flash of /login)
  if (loading) {
    return (
      <div className="min-vh-100 d-flex justify-content-center align-items-center">
        <div className="spinner-border text-primary" role="status">
          <span className="visually-hidden">Loading...</span>
        </div>
      </div>
    );
  }

  return (
    <Routes>
      {/* Public route */}
      <Route path="/login" element={<Login />} />

      {/* First-time password change (any logged-in role) */}
      <Route
        path="/change-password"
        element={
          <ProtectedRoute allowedRoles={["management", "teacher", "student"]}>
            <ChangePassword />
          </ProtectedRoute>
        }
      />

      {/* ===================== MANAGEMENT ===================== */}
      <Route
        element={
          <ProtectedRoute allowedRoles={["management"]}>
            <Layout />
          </ProtectedRoute>
        }
      >
        <Route path="/management" element={<Overview />} />
        <Route path="/management/students" element={<Students />} />
        <Route path="/management/teachers" element={<Teachers />} />
        <Route path="/management/assignments" element={<Assignments />} />
        <Route path="/management/payments" element={<Payments />} />
        <Route path="/management/ebooks" element={<Ebooks />} />
        <Route path="/management/holidays" element={<Holidays />} />
        <Route path="/profile" element={<Profile />} />
        <Route path="/management/users" element={<Users />} />
        <Route path="/management/countries" element={<Countries />} />
        <Route path="/teacher/ebooks" element={<TeacherEbooks />} />
      </Route>

      {/* ===================== TEACHER ===================== */}
      <Route
        element={
          <ProtectedRoute allowedRoles={["teacher"]}>
            <Layout />
          </ProtectedRoute>
        }
      >
        <Route path="/teacher" element={<TeacherDashboard />} />
        <Route path="/teacher/schedule" element={<Schedule />} />
      </Route>

      {/* ===================== STUDENT ===================== */}
      <Route
        element={
          <ProtectedRoute allowedRoles={["student"]}>
            <Layout />
          </ProtectedRoute>
        }
      >
        <Route path="/student" element={<StudentDashboard />} />
      </Route>

      {/* Default + catch-all: send to the right home (or login) */}
      <Route path="/" element={<Navigate to={user ? `/${user.role}` : "/login"} replace />} />
      <Route path="*" element={<Navigate to={user ? `/${user.role}` : "/login"} replace />} />
    </Routes>
  );
}