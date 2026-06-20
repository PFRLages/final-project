// src/pages/management/Holidays.jsx
import { useEffect, useState } from "react";
import api from "../../api/client";

export default function Holidays() {
  const [holidays, setHolidays] = useState([]);
  const [countries, setCountries] = useState([]);           // for the dropdowns
  const [filter, setFilter] = useState("");                 // filter by country
  const [form, setForm] = useState({ country: "", date: "", name: "" });
  const [error, setError] = useState("");
  const [uploadCountry, setUploadCountry] = useState("");
  const [uploadFile, setUploadFile] = useState(null);
  const [uploadMsg, setUploadMsg] = useState("");

  async function load() {
    const res = await api.get("/api/holidays", { params: filter ? { country: filter } : {} });
    setHolidays(res.data);
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
    setError("");
    try {
      await api.post("/api/holidays", form);               // backend fills day + year
      setForm({ country: "", date: "", name: "" });
      load();
    } catch (err) {
      setError(err.response?.data?.detail || "Could not add holiday");
    }
  }

  async function handleUpload(e) {
    e.preventDefault();
    setUploadMsg("");
    try {
      const data = new FormData();
      data.append("country", uploadCountry);
      data.append("file", uploadFile);
      const res = await api.post("/api/holidays/upload", data);
      let msg = `Added ${res.data.added}, skipped ${res.data.skipped} duplicate(s).`;
      if (res.data.errors.length) msg += ` ${res.data.errors.length} row(s) had bad dates.`;
      setUploadMsg(msg);
      setUploadCountry("");
      setUploadFile(null);
      e.target.reset();
      load();
    } catch (err) {
      setUploadMsg(err.response?.data?.detail || "Upload failed");
    }
  }

  async function handleDelete(id) {
    if (!confirm("Delete this holiday?")) return;
    await api.delete(`/api/holidays/${id}`);
    load();
  }

  return (
    <div>
      <h1 className="mb-4">Holidays</h1>

      {/* Add a holiday */}
      <form onSubmit={handleCreate} className="row g-2 mb-3">
        <div className="col-12 col-md-3">
          <select className="form-select" value={form.country}
            onChange={(e) => setForm({ ...form, country: e.target.value })} required
            data-testid="holiday-country-select">
            <option value="">Select country...</option>
            {countries.map((c) => <option key={c.id} value={c.name}>{c.name}</option>)}
          </select>
        </div>
        <div className="col-12 col-md-3">
          <input className="form-control" type="date" value={form.date}
            onChange={(e) => setForm({ ...form, date: e.target.value })} required
            data-testid="holiday-date-input" />
        </div>
        <div className="col-12 col-md-4">
          <input className="form-control" placeholder="Name" value={form.name}
            onChange={(e) => setForm({ ...form, name: e.target.value })} required
            data-testid="holiday-name-input" />
        </div>
        <div className="col-12 col-md-2 d-grid">
          <button className="btn btn-danger" type="submit" data-testid="holiday-add-button">Add</button>
        </div>
      </form>
      
      {/* Bulk upload */}
      <form onSubmit={handleUpload} className="card card-body mb-3" style={{ maxWidth: 720 }}>
        <h6 className="mb-2">Bulk upload holidays (CSV / TXT / Excel)</h6>
        <div className="row g-2">
          <div className="col-12 col-md-4">
            <select className="form-select" value={uploadCountry}
              onChange={(e) => setUploadCountry(e.target.value)} required
              data-testid="upload-country-select">
              <option value="">Select country...</option>
              {countries.map((c) => <option key={c.id} value={c.name}>{c.name}</option>)}
            </select>
          </div>
          <div className="col-12 col-md-5">
            <input className="form-control" type="file" accept=".csv,.txt,.xlsx"
              onChange={(e) => setUploadFile(e.target.files[0])} required
              data-testid="upload-file-input" />
          </div>
          <div className="col-12 col-md-3 d-grid">
            <button className="btn btn-primary" type="submit" data-testid="upload-holidays-button">Upload</button>
          </div>
        </div>
        <small className="text-muted mt-2">
          Each row = <code>date,name</code> — e.g. <code>2026-01-01,New Year's Day</code>.
          Excel: column A = date (YYYY-MM-DD), column B = name.
        </small>
        {uploadMsg && <div className="alert alert-info mt-2 mb-0">{uploadMsg}</div>}
      </form>
      {error && <p className="text-danger">{error}</p>}

      {/* Filter by country */}
      <div className="mb-3" style={{ maxWidth: 300 }}>
        <select className="form-select" value={filter}
          onChange={(e) => setFilter(e.target.value)} data-testid="holiday-filter-select">
          <option value="">All countries</option>
          {countries.map((c) => <option key={c.id} value={c.name}>{c.name}</option>)}
        </select>
      </div>

      {/* List */}
      <table className="table table-striped table-bordered">
        <thead className="table-dark">
          <tr><th>Date</th><th>Day</th><th>Name</th><th>Country</th><th></th></tr>
        </thead>
        <tbody>
          {holidays.map((h) => (
            <tr key={h.id}>
              <td>{h.date}</td>
              <td>{h.day_of_week}</td>
              <td>{h.name}</td>
              <td>{h.country}</td>
              <td>
                <button className="btn btn-sm btn-outline-danger" onClick={() => handleDelete(h.id)}>
                  Delete
                </button>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}