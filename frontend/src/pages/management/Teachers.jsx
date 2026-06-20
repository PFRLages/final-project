// src/pages/management/Teachers.jsx
import { useEffect, useState } from "react";
import api from "../../api/client";

export default function Teachers() {
    const [teachers, setTeachers] = useState([]);
    const [search, setSearch] = useState("");
    const [form, setForm] = useState({ name: "", email: "", mobile: "" });
    const [error, setError] = useState("");
    const [temp, setTemp] = useState(null);   // shows the new login + temp password

    async function load() {
        const res = await api.get("/api/teachers", { params: search ? { search } : {} });
        setTeachers(res.data);
    }
    useEffect(() => { load(); }, []);

    async function handleCreate(e) {
        e.preventDefault();
        setError(""); setTemp(null);
        try {
            const res = await api.post("/api/teachers", form);
            setTemp({ email: res.data.teacher.email, password: res.data.temp_password });
            setForm({ name: "", email: "", mobile: "" });
            load();
        } catch (err) { setError(err.response?.data?.detail || "Could not add teacher"); }
    }

    async function handleDelete(id) {
        if (!confirm("Delete this teacher?")) return;
        await api.delete(`/api/teachers/${id}`);
        load();
    }

    return (
        <div>
            <h1 className="mb-4">Teachers</h1>

            {temp && (
                <div className="alert alert-success">
                    Login created — <b>{temp.email}</b> · temporary password: <b>{temp.password}</b>
                    <div className="small">Share these. They'll be asked to change the password on first login.</div>
                </div>
            )}

            <form onSubmit={handleCreate} className="row g-2 mb-3">
                <div className="col"><input className="form-control" placeholder="Name" value={form.name}
                    onChange={(e) => setForm({ ...form, name: e.target.value })} required /></div>
                <div className="col"><input className="form-control" type="email" placeholder="Email" value={form.email}
                    onChange={(e) => setForm({ ...form, email: e.target.value })} required /></div>
                <div className="col"><input className="form-control" placeholder="Mobile" value={form.mobile}
                    onChange={(e) => setForm({ ...form, mobile: e.target.value })} /></div>
                <div className="col-auto"><button className="btn btn-danger" type="submit">Add</button></div>
            </form>
            {error && <p className="text-danger">{error}</p>}

            <div className="input-group mb-3" style={{ maxWidth: 400 }}>
                <input className="form-control" placeholder="Search by name or email"
                    value={search} onChange={(e) => setSearch(e.target.value)} />
                <button className="btn btn-outline-secondary" onClick={load}>Search</button>
            </div>

            <table className="table table-striped table-bordered">
                <thead className="table-dark"><tr><th>Name</th><th>Email</th><th>Mobile</th><th></th></tr></thead>
                <tbody>
                    {teachers.map((t) => (
                        <tr key={t.id}>
                            <td>{t.name}</td><td>{t.email}</td><td>{t.mobile || "-"}</td>
                            <td><button className="btn btn-sm btn-outline-danger" onClick={() => handleDelete(t.id)}>Delete</button></td>
                        </tr>
                    ))}
                </tbody>
            </table>
        </div>
    );
}