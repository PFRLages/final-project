// src/pages/management/Payments.jsx
import { useEffect, useState } from "react";
import api from "../../api/client";

export default function Payments() {
  const [students, setStudents] = useState([]);
  const [studentId, setStudentId] = useState("");
  const [year, setYear] = useState(2026);
  const [data, setData] = useState(null);

  useEffect(() => { api.get("/api/students").then((r) => setStudents(r.data)); }, []);

  async function loadYear() {
    const res = await api.get("/api/payments/year", { params: { student_id: studentId, year } });
    setData(res.data);
  }
  async function generate() {
    await api.post("/api/payments/generate-year", { student_id: studentId, year: Number(year) });
    loadYear();
  }
  function editRow(id, field, value) {
    setData((d) => ({ ...d, rows: d.rows.map((r) => (r.id === id ? { ...r, [field]: value } : r)) }));
  }
  async function saveRow(row) {
    await api.put(`/api/payments/${row.id}`, {
      payment_date: row.payment_date || null,
      amount: row.amount ? Number(row.amount) : null,
      make_up_classes_count: Number(row.make_up_classes_count) || 0,
    });
    loadYear();
  }

  return (
    <div>
      <h1 className="mb-4">Payments</h1>

      <div className="row g-2 mb-3">
        <div className="col-md-4">
          <select className="form-select" value={studentId} onChange={(e) => setStudentId(e.target.value)}>
            <option value="">Select a student...</option>
            {students.map((s) => <option key={s.id} value={s.id}>{s.name}</option>)}
          </select>
        </div>
        <div className="col-auto">
          <input className="form-control" type="number" style={{ width: 110 }}
            value={year} onChange={(e) => setYear(e.target.value)} />
        </div>
        <div className="col-auto">
          <button className="btn btn-danger" disabled={!studentId} onClick={generate}>Generate year</button>
          <button className="btn btn-outline-secondary ms-2" disabled={!studentId} onClick={loadYear}>Load</button>
        </div>
      </div>

      {data && (
        <>
          <p>
            {data.all_settled
              ? <span className="badge bg-success">All settled</span>
              : <span className="badge bg-warning text-dark">Not fully settled</span>}
            <span className="ms-3">Total paid: ₩{data.total_paid.toLocaleString()}</span>
          </p>
          <table className="table table-bordered align-middle">
            <thead className="table-dark">
              <tr><th>Month</th><th>From</th><th>To</th><th>Date Paid</th><th>Amount (₩)</th><th>Make-up</th><th></th></tr>
            </thead>
            <tbody>
              {data.rows.map((p) => (
                <tr key={p.id} className={p.paid ? "table-success" : ""}>
                  <td>{p.month_name}</td>
                  <td>{p.period_from}</td>
                  <td>{p.period_to}</td>
                  <td><input className="form-control form-control-sm" type="date"
                    value={p.payment_date || ""} onChange={(e) => editRow(p.id, "payment_date", e.target.value)} /></td>
                  <td style={{ width: 130 }}><input className="form-control form-control-sm" type="number"
                    value={p.amount ?? ""} onChange={(e) => editRow(p.id, "amount", e.target.value)} /></td>
                  <td style={{ width: 90 }}><input className="form-control form-control-sm" type="number"
                    value={p.make_up_classes_count} onChange={(e) => editRow(p.id, "make_up_classes_count", e.target.value)} /></td>
                  <td><button className="btn btn-sm btn-primary" onClick={() => saveRow(p)}>Save</button></td>
                </tr>
              ))}
            </tbody>
          </table>
        </>
      )}
    </div>
  );
}