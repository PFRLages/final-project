// English Passion — Management "Users" admin page.
// List all login accounts, add management users, reset passwords,
// and deactivate / reactivate (so returning staff can be restored).
import { useEffect, useState } from "react";
import api from "../../api/client";

export default function Users() {
  const [users, setUsers] = useState([]);
  const [roleFilter, setRoleFilter] = useState("");
  const [search, setSearch] = useState("");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  // Add-management-user form
  const [showForm, setShowForm] = useState(false);
  const [form, setForm] = useState({ name: "", email: "", mobile: "" });

  // Temp password banner (shown once after create / reset)
  const [tempInfo, setTempInfo] = useState(null); // { email, password }

  const load = async () => {
    setLoading(true);
    try {
      const params = {};
      if (roleFilter) params.role = roleFilter;
      if (search) params.search = search;
      const res = await api.get("/api/users", { params });
      setUsers(res.data);
      setError("");
    } catch (err) {
      setError(err?.response?.data?.detail || "Failed to load users");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    load();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [roleFilter]);

  const handleCreate = async (e) => {
    e.preventDefault();
    try {
      const res = await api.post("/api/users", form);
      setTempInfo({ email: res.data.user.email, password: res.data.temp_password });
      setForm({ name: "", email: "", mobile: "" });
      setShowForm(false);
      load();
    } catch (err) {
      setError(err?.response?.data?.detail || "Failed to create user");
    }
  };

  const handleReset = async (u) => {
    if (!window.confirm(`Reset password for ${u.email}?`)) return;
    try {
      const res = await api.post(`/api/users/${u.id}/reset-password`);
      setTempInfo({ email: u.email, password: res.data.temp_password });
    } catch (err) {
      setError(err?.response?.data?.detail || "Failed to reset password");
    }
  };

  const handleToggleActive = async (u) => {
    const action = u.active ? "deactivate" : "reactivate";
    if (!window.confirm(`${action} ${u.email}?`)) return;
    try {
      await api.post(`/api/users/${u.id}/${action}`);
      load();
    } catch (err) {
      setError(err?.response?.data?.detail || `Failed to ${action} user`);
    }
  };

  return (
    <div data-testid="users-page">
      <div className="d-flex justify-content-between align-items-center mb-3">
        <h1 className="h3 mb-0">Users</h1>
        <button
          className="btn btn-primary"
          onClick={() => setShowForm((s) => !s)}
          data-testid="add-management-user-button"
        >
          {showForm ? "Cancel" : "+ Add Management User"}
        </button>
      </div>

      {error && <div className="alert alert-danger" data-testid="users-error">{error}</div>}

      {tempInfo && (
        <div className="alert alert-success d-flex justify-content-between align-items-center" data-testid="temp-password-banner">
          <span>
            Temporary password for <strong>{tempInfo.email}</strong>:{" "}
            <code className="fs-6">{tempInfo.password}</code> — share it now, it won't be shown again.
          </span>
          <button className="btn-close" onClick={() => setTempInfo(null)} />
        </div>
      )}

      {showForm && (
        <form className="card card-body mb-3" onSubmit={handleCreate} data-testid="management-user-form">
          <div className="row g-2 align-items-start">
            <div className="col-12 col-md-4">
              <input
                className="form-control"
                placeholder="Full name"
                required
                value={form.name}
                onChange={(e) => setForm({ ...form, name: e.target.value })}
                data-testid="mu-name-input"
              />
            </div>
            <div className="col-12 col-md-3">
              <input
                type="email"
                className="form-control"
                placeholder="Email"
                required
                value={form.email}
                onChange={(e) => setForm({ ...form, email: e.target.value })}
                data-testid="mu-email-input"
              />
            </div>
            <div className="col-12 col-md-3">
              <input
                className="form-control"
                placeholder="Mobile (optional)"
                value={form.mobile}
                onChange={(e) => setForm({ ...form, mobile: e.target.value })}
                data-testid="mu-mobile-input"
              />
            </div>
            <div className="col-12 col-md-2 d-grid">
              <button className="btn btn-success" type="submit" data-testid="mu-save-button">
                Save
              </button>
            </div>
          </div>
        </form>
      )}

      <div className="row g-2 mb-3">
        <div className="col-md-3">
          <select className="form-select" value={roleFilter}
            onChange={(e) => setRoleFilter(e.target.value)} data-testid="role-filter">
            <option value="">All roles</option>
            <option value="management">Management</option>
            <option value="teacher">Teacher</option>
            <option value="student">Student</option>
          </select>
        </div>
        <div className="col-md-4">
          <form onSubmit={(e) => { e.preventDefault(); load(); }}>
            <input className="form-control" placeholder="Search name or email"
              value={search} onChange={(e) => setSearch(e.target.value)} data-testid="user-search-input" />
          </form>
        </div>
      </div>

      {loading ? (
        <p>Loading...</p>
      ) : (
        <div className="table-responsive">
          <table className="table table-hover align-middle">
            <thead>
              <tr>
                <th>Name</th><th>Email</th><th>Role</th><th>Status</th><th className="text-end">Actions</th>
              </tr>
            </thead>
            <tbody>
              {users.map((u) => (
                <tr key={u.id} data-testid={`user-row-${u.id}`}>
                  <td>{u.name}</td>
                  <td>{u.email}</td>
                  <td><span className="badge bg-secondary text-capitalize">{u.role}</span></td>
                  <td>
                    {u.active
                      ? <span className="badge bg-success">Active</span>
                      : <span className="badge bg-danger">Inactive</span>}
                  </td>
                  <td className="text-end">
                    <button className="btn btn-sm btn-outline-secondary me-2"
                      onClick={() => handleReset(u)} data-testid={`reset-pw-${u.id}`}>
                      Reset password
                    </button>
                    <button
                      className={"btn btn-sm " + (u.active ? "btn-outline-danger" : "btn-outline-success")}
                      onClick={() => handleToggleActive(u)} data-testid={`toggle-active-${u.id}`}>
                      {u.active ? "Deactivate" : "Reactivate"}
                    </button>
                  </td>
                </tr>
              ))}
              {users.length === 0 && (
                <tr><td colSpan="5" className="text-center text-muted">No users found</td></tr>
              )}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}