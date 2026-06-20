// src/pages/management/Students.jsx
import { useEffect, useState } from "react";
import api from "../../api/client";

const LEVELS = ["beginner", "preintermediate", "intermediate", "advanced", "proficient"];

export default function Students() {
  const [students, setStudents] = useState([]);
  const [countries, setCountries] = useState([]);
  const [search, setSearch] = useState("");
  const [countryFilter, setCountryFilter] = useState("");
  const [form, setForm] = useState({ name: "", email: "", level: "", country: "" });
  const [error, setError] = useState("");
  const [temp, setTemp] = useState(null);

  async function load() {
    const res = await api.get("/api/students", { params: search ? { search } : {} });
    setStudents(res.data);
  }
  async function loadCountries() {
    const res = await api.get("/api/countries");
    setCountries(res.data);
  }
  useEffect(() => {
    load();
    loadCountries();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  async function handleCreate(e) {
    e.preventDefault();
    setError(""); setTemp(null);
    try {
      const res = await api.post("/api/students", form);
      setTemp({ email: res.data.student.email, password: res.data.temp_password });
      setForm({ name: "", email: "", level: "", country: "" });
      load();
    } catch (err) { setError(err.response?.data?.detail || "Could not add student"); }
  }

  async function handleDelete(id) {
    if (!confirm("Delete this student?")) return;
    await api.delete(`/api/students/${id}`);
    load();
  }

  return (
    <div>
      <h1 className="mb-4">Students</h1>

      {temp && (
        <div className="alert alert-success">
          Login created — <b>{temp.email}</b> · temporary password: <b>{temp.password}</b>
          <div className="small">They'll change the password on first login.</div>
        </div>
      )}

      <form onSubmit={handleCreate} className="row g-2 mb-3">
        <div className="col-12 col-md-3">
          <input className="form-control" placeholder="Name" value={form.name}
            onChange={(e) => setForm({ ...form, name: e.target.value })} required
            data-testid="student-name-input" />
        </div>
        <div className="col-12 col-md-3">
          <input className="form-control" type="email" placeholder="Email" value={form.email}
            onChange={(e) => setForm({ ...form, email: e.target.value })} required
            data-testid="student-email-input" />
        </div>
        <div className="col-12 col-md-2">
          <select className="form-select" value={form.level}
            onChange={(e) => setForm({ ...form, level: e.target.value })} required
            data-testid="student-level-select">
            <option value="">Level...</option>
            {LEVELS.map((l) => <option key={l} value={l}>{l}</option>)}
          </select>
        </div>
        <div className="col-12 col-md-2">
          <select className="form-select" value={form.country}
            onChange={(e) => setForm({ ...form, country: e.target.value })} required
            data-testid="student-country-select">
            <option value="">Country...</option>
            {countries.map((c) => <option key={c.id} value={c.name}>{c.name}</option>)}
          </select>
        </div>
        <div className="col-12 col-md-2 d-grid">
          <button className="btn btn-danger" type="submit" data-testid="student-add-button">Add</button>
        </div>
      </form>
      {error && <p className="text-danger">{error}</p>}

      <div className="row g-2 mb-3" style={{ maxWidth: 640 }}>
        <div className="col">
          <div className="input-group">
            <input className="form-control" placeholder="Search by name or email"
              value={search} onChange={(e) => setSearch(e.target.value)} />
            <button className="btn btn-outline-secondary" onClick={load}>Search</button>
          </div>
        </div>
        <div className="col-auto">
          <select className="form-select" value={countryFilter}
            onChange={(e) => setCountryFilter(e.target.value)} data-testid="student-country-filter">
            <option value="">All countries</option>
            {countries.map((c) => <option key={c.id} value={c.name}>{c.name}</option>)}
          </select>
        </div>
      </div>

      <table className="table table-striped table-bordered">
        <thead className="table-dark">
          <tr><th>Name</th><th>Email</th><th>Level</th><th>Country</th><th></th></tr>
        </thead>
        <tbody>
          {students.filter((s) => !countryFilter || s.country === countryFilter).map((s) => (
            <tr key={s.id}>
              <td>{s.name}</td><td>{s.email}</td><td>{s.level || "-"}</td><td>{s.country || "-"}</td>
              <td><button className="btn btn-sm btn-outline-danger" onClick={() => handleDelete(s.id)}>Delete</button></td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}