// src/pages/teacher/TeacherDashboard.jsx
// Teacher view: pick a student, generate their monthly report, then edit
// each row (status, payable time, book, remarks). Country is now auto-derived
// (Philippines + the student's own country), so no country field here.
import { useEffect, useState } from "react";
import api from "../../api/client";

const STATUS_OPTIONS = [
  { key: "attended", label: "Present" },
  { key: "vacation", label: "student vacation" },
  { key: "makeup", label: "supplementary class" },
  { key: "holiday", label: "holiday" },
  { key: "rest_day", label: "rest day" },
  { key: "technical", label: "technical concern" },
  { key: "no_class", label: "pre-scheduled class" },
  { key: "absent_notice", label: "absence with prior notice" },
  { key: "absent_late", label: "late notification of absence" },
  { key: "absent_no_notice", label: "no-notice absence" },
  { key: "teacher_absent", label: "teacher unavailability" },
];

export default function TeacherDashboard() {
  const [students, setStudents] = useState([]);
  const [studentId, setStudentId] = useState("");
  const [month, setMonth] = useState(1);
  const [year, setYear] = useState(2026);
  const [report, setReport] = useState(null);

  useEffect(() => {
    api.get("/api/students").then((res) => setStudents(res.data));
  }, []);

  async function fetchReport() {
    const res = await api.get("/api/attendance/report", {
      params: { student_id: studentId, month, year },
    });
    setReport(res.data);
  }

  // Build the month skeleton — backend auto-derives the holidays by country.
  async function generate() {
    await api.post("/api/attendance/generate", {
      student_id: studentId, month: Number(month), year: Number(year),
    });
    fetchReport();
  }

  function editRow(id, field, value) {
    setReport((r) => ({
      ...r,
      rows: r.rows.map((row) => (row.id === id ? { ...row, [field]: value } : row)),
    }));
  }

  async function saveRow(row) {
    await api.put(`/api/attendance/${row.id}`, {
      status: row.status,
      payable_time_minutes: row.payable_time_minutes,
      book: row.book,
      teacher_remarks: row.teacher_remarks,
    });
    fetchReport();
  }

  return (
    <div>
      <h1 className="mb-4">Monthly Report</h1>

      {/* Controls */}
      <div className="row g-2 mb-3">
        <div className="col-md-4">
          <select className="form-select" value={studentId}
            onChange={(e) => setStudentId(e.target.value)} data-testid="report-student-select">
            <option value="">Select a student...</option>
            {students.map((s) => (
              <option key={s.id} value={s.id}>{s.name}</option>
            ))}
          </select>
        </div>
        <div className="col-auto">
          <select className="form-select" value={month}
            onChange={(e) => setMonth(e.target.value)} data-testid="report-month-select">
            {Array.from({ length: 12 }, (_, i) => (
              <option key={i + 1} value={i + 1}>{i + 1}</option>
            ))}
          </select>
        </div>
        <div className="col-auto">
          <input className="form-control" type="number" style={{ width: 100 }}
            value={year} onChange={(e) => setYear(e.target.value)} data-testid="report-year-input" />
        </div>
        <div className="col-auto">
          <button className="btn btn-danger" disabled={!studentId} onClick={generate} data-testid="report-generate-button">
            Generate
          </button>
          <button className="btn btn-outline-secondary ms-2" disabled={!studentId} onClick={fetchReport} data-testid="report-load-button">
            Load
          </button>
        </div>
      </div>

      {report && (
        <>
          <h4>{report.summary.title}</h4>
          <p>
            <span className="badge bg-success me-2">{report.summary.attended_classes} attended</span>
            <span className="badge bg-warning text-dark me-2">{report.summary.absent_with_notice} absent w/ notice (max 5)</span>
            <span className="badge bg-danger me-2">{report.summary.absent_without_notice} absent w/o notice</span>
            <span className="badge bg-secondary">{report.summary.holidays} holidays</span>
          </p>

          <table className="table table-bordered align-middle">
            <thead className="table-dark">
              <tr>
                <th>Date</th><th>Day</th><th>Status</th>
                <th>Payable</th><th>Book</th><th>Teacher Remarks</th><th></th>
              </tr>
            </thead>
            <tbody>
              {report.rows.map((row) => (
                <tr key={row.id} style={{ backgroundColor: row.color }}>
                  <td>{row.date}</td>
                  <td>{row.day_of_week}</td>
                  <td>
                    <select className="form-select form-select-sm" value={row.status}
                      onChange={(e) => editRow(row.id, "status", e.target.value)}>
                      {STATUS_OPTIONS.map((o) => (
                        <option key={o.key} value={o.key}>{o.label}</option>
                      ))}
                    </select>
                  </td>
                  <td style={{ width: 110 }}>
                    <select className="form-select form-select-sm"
                      value={row.payable_time_minutes ?? ""}
                      onChange={(e) => editRow(row.id, "payable_time_minutes",
                        e.target.value === "" ? null : Number(e.target.value))}>
                      <option value="">blank</option>
                      <option value={25}>25 min</option>
                      <option value={50}>50 min</option>
                    </select>
                  </td>
                  <td>
                    <input className="form-control form-control-sm"
                      value={row.book ?? ""}
                      onChange={(e) => editRow(row.id, "book", e.target.value)} />
                  </td>
                  <td>
                    <input className="form-control form-control-sm"
                      value={row.teacher_remarks ?? ""}
                      onChange={(e) => editRow(row.id, "teacher_remarks", e.target.value)} />
                  </td>
                  <td>
                    <button className="btn btn-sm btn-primary" onClick={() => saveRow(row)}>
                      Save
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </>
      )}
    </div>
  );
}