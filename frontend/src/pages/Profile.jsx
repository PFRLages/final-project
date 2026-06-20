// src/pages/Profile.jsx
import { useState } from "react";
import { Link } from "react-router-dom";
import { useAuth } from "../context/AuthContext";
import api from "../api/client";

export default function Profile() {
  const { user, refreshUser } = useAuth();
  const [name, setName] = useState(user.name || "");
  const [mobile, setMobile] = useState(user.mobile || "");
  const [saved, setSaved] = useState(false);

  async function handleSave(e) {
    e.preventDefault();
    await api.put("/api/auth/me", { name, mobile });
    await refreshUser();
    setSaved(true);
  }

  return (
    <div style={{ maxWidth: 600 }}>
      <h1 className="mb-4">My Profile</h1>

      <form onSubmit={handleSave}>
        <label className="form-label">Email</label>
        <input className="form-control mb-3" value={user.email} disabled />

        <label className="form-label">Name</label>
        <input className="form-control mb-3" value={name}
          onChange={(e) => { setName(e.target.value); setSaved(false); }} />

        <label className="form-label">Mobile</label>
        <input className="form-control mb-3" value={mobile}
          onChange={(e) => { setMobile(e.target.value); setSaved(false); }} />

        <button className="btn btn-danger" type="submit">Save</button>
        {saved && <span className="text-success ms-3">Saved ✓</span>}
      </form>

      <hr className="my-4" />
      <Link to="/change-password" className="btn btn-outline-secondary">Change password</Link>
    </div>
  );
}