// src/components/ProtectedRoute.jsx
import { Navigate, Outlet } from "react-router-dom";
import { useAuth } from "../context/AuthContext";

export default function ProtectedRoute({ allowedRoles, children }) {
  const { user, loading } = useAuth();

  // Still checking the token — don't decide yet
  if (loading) return null;

  // Not logged in -> go to login
  if (!user) return <Navigate to="/login" replace />;

  // Force first-time password change (but allow the change-password page itself)
  if (user.must_change_password && window.location.pathname !== "/change-password") {
    return <Navigate to="/change-password" replace />;
  }

  // Logged in but wrong role -> send to their own home
  if (allowedRoles && !allowedRoles.includes(user.role)) {
    return <Navigate to={`/${user.role}`} replace />;
  }

  // If used as a wrapper (App.jsx group route) render <Outlet />,
  // otherwise render the single child passed in.
  return children ? children : <Outlet />;
}