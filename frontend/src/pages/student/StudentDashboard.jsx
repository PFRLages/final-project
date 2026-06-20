// src/pages/student/StudentDashboard.jsx
// Student view (read-only): my monthly report, my payments, and shared eBooks.
import { useEffect, useState } from "react";
import { useAuth } from "../../context/AuthContext";
import api from "../../api/client";

export default function StudentDashboard() {
  const { user } = useAuth();
  const studentId = user.student_id;          // linked automatically now

  const [tab, setTab] = useState("report");
  const [month, setMonth] = useState(1);
  const [year, setYear] = useState(2026);
  const [report, setReport] = useState(null);
  const [payments, setPayments] = useState(null);
  const [ebooks, setEbooks] = useState([]);

  async function loadReport() {
    const res = await api.get("/api/attendance/report", {
      params: { student_id: studentId, month, year },
    });
    setReport(res.data);
  }

  async function loadPayments() {
    const res = await api.get("/api/payments/year", {
      params: { student_id: studentId, year },
    });
    setPayments(res.data);
  }

  useEffect(() => {
    api.get("/api/ebooks").then((res) => setEbooks(res.data));
  }, []);

  if (!studentId) {
    return <p className="text-danger">Your account isn't linked to a student record yet.</p>;
  }

  return (
    <div>
      <h1 className="mb-3">My Dashboard</h1>

      <ul className="nav nav-tabs mb-3">
        {[["report", "My Report"], ["payments", "My Payments"], ["ebooks", "eBooks"]].map(([key, label]) => (
          <li className="nav-item" key={key}>
            <button className={"nav-link " + (tab === key ? "active" : "")} onClick={() => setTab(key)}>
              {label}
            </button>
          </li>
        ))}
      </ul>

      {tab === "report" && (
        <div>
          <div className="row g-2 mb-3">
            <div className="col-auto">
              <select className="form-select" value={month} onChange={(e) => setMonth(e.target.value)}>
                {Array.from({ length: 12 }, (_, i) => <option key={i + 1} value={i + 1}>{i + 1}</option>)}
              </select>
            </div>
            <div className="col-auto">
              <input className="form-control" type="number" style={{ width: 100 }}
                value={year} onChange={(e) => setYear(e.target.value)} />
            </div>
            <div className="col-auto">
              <button className="btn btn-danger" onClick={loadReport}>Load</button>
            </div>
          </div>

          {report && (
            <>
              <h4>{report.summary.title}</h4>
              <p>
                <span className="badge bg-success me-2">{report.summary.attended_classes} attended</span>
                <span className="badge bg-warning text-dark me-2">{report.summary.absent_with_notice} absent w/ notice</span>
                <span className="badge bg-danger me-2">{report.summary.absent_without_notice} absent w/o notice</span>
                <span className="badge bg-secondary">{report.summary.holidays} holidays</span>
              </p>
              <table className="table table-bordered">
                <thead className="table-dark">
                  <tr><th>Date</th><th>Attendance</th><th>Payable Time</th><th>Book</th><th>Class Status</th><th>Teacher's Remarks</th></tr>
                </thead>
                <tbody>
                  {report.rows.map((row) => (
                    <tr key={row.id} style={{ backgroundColor: row.color }}>
                      <td>{row.date}</td>
                      <td>{row.status === "attended" ? "Present" : ""}</td>
                      <td>{row.payable_time_minutes ? `${row.payable_time_minutes} min` : ""}</td>
                      <td>{row.book || ""}</td>
                      <td>{row.status === "attended" ? "" : row.status_label}</td>
                      <td>{row.teacher_remarks || ""}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </>
          )}
        </div>
      )}

      {tab === "payments" && (
        <div>
          <div className="row g-2 mb-3">
            <div className="col-auto">
              <input className="form-control" type="number" style={{ width: 120 }}
                value={year} onChange={(e) => setYear(e.target.value)} />
            </div>
            <div className="col-auto">
              <button className="btn btn-danger" onClick={loadPayments}>Load</button>
            </div>
          </div>

          {payments && (
            <>
              <p>
                {payments.all_settled
                  ? <span className="badge bg-success">All settled</span>
                  : <span className="badge bg-warning text-dark">Not fully settled</span>}
                <span className="ms-3">Total paid: ₩{payments.total_paid.toLocaleString()}</span>
              </p>
              <table className="table table-striped table-bordered">
                <thead className="table-dark">
                  <tr><th>Month</th><th>Date Paid</th><th>From</th><th>To</th><th>Amount (₩)</th><th>Make-up</th></tr>
                </thead>
                <tbody>
                  {payments.rows.map((p) => (
                    <tr key={p.id}>
                      <td>{p.month_name}</td>
                      <td>{p.payment_date || "-"}</td>
                      <td>{p.period_from}</td>
                      <td>{p.period_to}</td>
                      <td>{p.amount ? `₩${p.amount.toLocaleString()}` : "-"}</td>
                      <td>{p.make_up_classes_count}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </>
          )}
        </div>
      )}

      {tab === "ebooks" && (
        <table className="table table-striped table-bordered">
          <thead className="table-dark">
            <tr><th>Name</th><th>Level</th><th>File</th></tr>
          </thead>
          <tbody>
            {ebooks.map((b) => (
              <tr key={b.id}>
                <td>{b.name}</td>
                <td>{b.level}</td>
                <td><a href={b.file_url} target="_blank" rel="noreferrer">Open</a></td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </div>
  );
}