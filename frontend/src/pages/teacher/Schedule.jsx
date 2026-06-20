// src/pages/teacher/Schedule.jsx
// Teacher manages a student's weekly class slots. These drive which days
// become "class days" vs "rest days" when I generate a monthly report.
import { useEffect, useState } from "react";
import api from "../../api/client";
import { useAuth } from "../../context/AuthContext";

const DAYS = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"];

// Fixed 30-minute time slots: 00:00, 00:30, 01:00 ... 23:30
const TIME_SLOTS = Array.from({ length: 48 }, (_, i) => {
  const h = String(Math.floor(i / 2)).padStart(2, "0");
  const m = i % 2 === 0 ? "00" : "30";
  return `${h}:${m}`;
});

export default function Schedule() {
  const { user } = useAuth();                 // I'm the teacher -> use my id
  const [students, setStudents] = useState([]);
  const [studentId, setStudentId] = useState("");
  const [slots, setSlots] = useState([]);
  const [form, setForm] = useState({ day_of_week: "Monday", start_time: "", end_time: "" });
  const [error, setError] = useState("");

  useEffect(() => {
    api.get("/api/students").then((res) => setStudents(res.data));
  }, []);

  async function loadSlots() {
    const res = await api.get("/api/schedules", { params: { student_id: studentId } });
    setSlots(res.data);
  }

  async function addSlot(e) {
    e.preventDefault();
    setError("");
    // End time must be after start time
    if (form.end_time <= form.start_time) {
      setError("End time must be after start time");
      return;
    }
    try {
      await api.post("/api/schedules", {
        teacher_id: user.id,
        student_id: studentId,
        day_of_week: form.day_of_week,
        start_time: form.start_time,
        end_time: form.end_time,
        status: "booked",
      });
      setForm({ day_of_week: "Monday", start_time: "", end_time: "" });
      loadSlots();
    } catch (err) {
      setError(err.response?.data?.detail || "Could not add class");
    }
  }

  async function deleteSlot(id) {
    await api.delete(`/api/schedules/${id}`);
    loadSlots();
  }

  return (
    <div>
      <h1 className="mb-4">Schedule</h1>

      {/* Pick the student */}
      <div className="row g-2 mb-3" style={{ maxWidth: 500 }}>
        <div className="col">
          <select className="form-select" value={studentId}
            onChange={(e) => setStudentId(e.target.value)} data-testid="schedule-student-select">
            <option value="">Select a student...</option>
            {students.map((s) => <option key={s.id} value={s.id}>{s.name}</option>)}
          </select>
        </div>
        <div className="col-auto">
          <button className="btn btn-outline-secondary" disabled={!studentId} onClick={loadSlots}>
            Load
          </button>
        </div>
      </div>

      {/* Add a class slot */}
      {studentId && (
        <form onSubmit={addSlot} className="row g-2 mb-3" style={{ maxWidth: 760 }}>
          <div className="col">
            <select className="form-select" value={form.day_of_week}
              onChange={(e) => setForm({ ...form, day_of_week: e.target.value })}
              data-testid="schedule-day-select">
              {DAYS.map((d) => <option key={d} value={d}>{d}</option>)}
            </select>
          </div>
          <div className="col">
            <select className="form-select" value={form.start_time} required
              onChange={(e) => setForm({ ...form, start_time: e.target.value })}
              data-testid="schedule-start-select">
              <option value="">Start...</option>
              {TIME_SLOTS.map((t) => <option key={t} value={t}>{t}</option>)}
            </select>
          </div>
          <div className="col">
            <select className="form-select" value={form.end_time} required
              onChange={(e) => setForm({ ...form, end_time: e.target.value })}
              data-testid="schedule-end-select">
              <option value="">End...</option>
              {TIME_SLOTS.map((t) => <option key={t} value={t}>{t}</option>)}
            </select>
          </div>
          <div className="col-auto">
            <button className="btn btn-danger" type="submit">Add Class</button>
          </div>
        </form>
      )}
      {error && <p className="text-danger">{error}</p>}

      {/* The student's weekly slots */}
      {slots.length > 0 && (
        <table className="table table-striped table-bordered" style={{ maxWidth: 700 }}>
          <thead className="table-dark">
            <tr><th>Day</th><th>Start</th><th>End</th><th></th></tr>
          </thead>
          <tbody>
            {slots.map((s) => (
              <tr key={s.id}>
                <td>{s.day_of_week}</td>
                <td>{s.start_time}</td>
                <td>{s.end_time}</td>
                <td>
                  <button className="btn btn-sm btn-outline-danger" onClick={() => deleteSlot(s.id)}>
                    Delete
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </div>
  );
}