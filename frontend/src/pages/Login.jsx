// src/pages/Login.jsx
import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { useAuth } from "../context/AuthContext";

export default function Login() {
  const { login } = useAuth();
  const navigate = useNavigate();

  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [showPassword, setShowPassword] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError("");
    setSubmitting(true);
    try {
      const user = await login(email, password);
      // Send user to the right home based on their role
      if (user.must_change_password) navigate("/change-password");
      else navigate(`/${user.role}`);
    } catch (err) {
      setError(err?.response?.data?.detail || "Invalid email or password");
    } finally {
      setSubmitting(false);
    }
  };

  return (
    // min-vh-100 + w-100 + flex centering = card sits dead center on full screen
    <div className="min-vh-100 w-100 bg-light d-flex justify-content-center align-items-center p-3">
      <div className="card shadow-sm border-0" style={{ maxWidth: "400px", width: "100%" }}>
        <div className="card-body p-4">
          <h1 className="h4 text-center mb-1 fw-bold">English Passion</h1>
          <p className="text-center text-muted mb-4">School Management System</p>

          {error && (
            <div className="alert alert-danger py-2" role="alert" data-testid="login-error">
              {error}
            </div>
          )}

          <form onSubmit={handleSubmit}>
            <div className="mb-3">
              <label className="form-label">Email</label>
              <input
                type="email"
                className="form-control"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                required
                data-testid="login-email-input"
              />
            </div>

            <div className="mb-3">
              <label className="form-label">Password</label>
              <div className="input-group">
                <input
                  type={showPassword ? "text" : "password"}
                  className="form-control"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  required
                  data-testid="login-password-input"
                />
                <button
                  type="button"
                  className="btn btn-outline-secondary"
                  onClick={() => setShowPassword((s) => !s)}
                  data-testid="toggle-password-visibility"
                >
                  {showPassword ? "Hide" : "Show"}
                </button>
              </div>
            </div>

            <button
              type="submit"
              className="btn btn-primary w-100"
              disabled={submitting}
              data-testid="login-submit-button"
            >
              {submitting ? "Signing in..." : "Sign In"}
            </button>
          </form>
        </div>
      </div>
    </div>
  );
}