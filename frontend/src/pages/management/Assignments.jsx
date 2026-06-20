// src/pages/management/Assignments.jsx
import { useEffect, useState } from "react";
import api from "../../api/client";

export default function Assignments() {
    const [teachers, setTeachers] = useState([]);
    const [students, setStudents] = useState([]);
    const [teacherId, setTeacherId] = useState("");
    const [studentId, setStudentId] = useState("");
    const [rows, setRows] = useState([]);
    const [error, setError] = useState("");

    useEffect(() => {
        api.get("/api/teachers").then((r) => setTeachers(r.data));
        api.get("/api/students").then((r) => setStudents(r.data));
    }, []);

    async function loadRows() {
        const res = await api.get("/api/assignments", { params: { teacher_id: teacherId } });
        setRows(res.data);
    }

    async function assign() {
        setError("");
        try {
            await api.post("/api/assignments", { teacher_id: teacherId, student_id: studentId });
            setStudentId("");
            loadRows();
        } catch (err) { setError(err.response?.data?.detail || "Could not assign"); }
    }

    async function remove(id) {
        await api.delete(`/api/assignments/${id}`);
        loadRows();
    }

    const studentName = (id) => students.find((s) => s.id === id)?.name || id;

    return (
        <div>
            <h1 className="mb-4">Assign Students to Teachers</h1>
            <div className="row g-2 mb-3" style={{ maxWidth: 700 }}>
                <div className="col">
                    <select className="form-select" value={teacherId}
                        onChange={(e) => { setTeacherId(e.target.value); setRows([]); }}>
                        <option value="">Select teacher...</option>
                        {teachers.map((t) => <option key={t.id} value={t.id}>{t.name}</option>)}
                    </select>
                </div>
                <div className="col-auto">
                    <button className="btn btn-outline-secondary" disabled={!teacherId} onClick={loadRows}>Load</button>
                </div>
            </div>

            {teacherId && (
                <div className="row g-2 mb-3" style={{ maxWidth: 700 }}>
                    <div className="col">
                        <select className="form-select" value={studentId} onChange={(e) => setStudentId(e.target.value)}>
                            <option value="">Select student...</option>
                            {students.map((s) => <option key={s.id} value={s.id}>{s.name}</option>)}
                        </select>
                    </div>
                    <div className="col-auto">
                        <button className="btn btn-danger" disabled={!studentId} onClick={assign}>Assign</button>
                    </div>
                </div>
            )}
            {error && <p className="text-danger">{error}</p>}

            <table className="table table-striped table-bordered" style={{ maxWidth: 700 }}>
                <thead className="table-dark"><tr><th>Assigned Student</th><th></th></tr></thead>
                <tbody>
                    {rows.map((r) => (
                        <tr key={r.id}>
                            <td>{studentName(r.student_id)}</td>
                            <td><button className="btn btn-sm btn-outline-danger" onClick={() => remove(r.id)}>Remove</button></td>
                        </tr>
                    ))}
                </tbody>
            </table>
        </div>
    );
}