// src/pages/ChangePassword.jsx
import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { useAuth } from "../context/AuthContext";
import api from "../api/client";

export default function ChangePassword() {
  const { refreshUser } = useAuth();
  const navigate = useNavigate();

  const [currentPassword, setCurrentPassword] = useState("");
  const [newPassword, setNewPassword] = useState("");
  const [showPassword, setShowPassword] = useState(false);
  const [error, setError] = useState("");

  async function handleSubmit(e) {
    e.preventDefault();
    setError("");
    try {
      await api.post("/api/auth/change-password", {
        current_password: currentPassword,
        new_password: newPassword,
      });
      const me = await refreshUser(); // now must_change_password is false
      navigate(`/${me.role}`);
    } catch (err) {
      setError(err.response?.data?.detail || "Could not change password");
    }
  }

  return (
    <div className="d-flex justify-content-center align-items-center min-vh-100 w-100 bg-light p-3">
      <div className="card shadow p-4" style={{ width: 380, maxWidth: "100%" }}>
        <h4>Change your password</h4>
        <p className="text-muted small">Set a new password to continue.</p>
        <form onSubmit={handleSubmit}>
          <input
            type={showPassword ? "text" : "password"}
            className="form-control mb-2"
            placeholder="Current (temporary) password"
            value={currentPassword}
            onChange={(e) => setCurrentPassword(e.target.value)}
            required
            data-testid="current-password-input"
          />
          <input
            type={showPassword ? "text" : "password"}
            className="form-control mb-2"
            placeholder="New password"
            value={newPassword}
            onChange={(e) => setNewPassword(e.target.value)}
            required
            data-testid="new-password-input"
          />
          <div className="form-check mb-3">
            <input
              type="checkbox"
              className="form-check-input"
              id="showPwd"
              checked={showPassword}
              onChange={(e) => setShowPassword(e.target.checked)}
              data-testid="toggle-password-visibility"
            />
            <label className="form-check-label small" htmlFor="showPwd">
              Show passwords
            </label>
          </div>
          {error && <p className="text-danger small">{error}</p>}
          <button type="submit" className="btn btn-danger w-100" data-testid="update-password-button">
            Update password
          </button>
        </form>
      </div>
    </div>
  );
}