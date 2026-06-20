// src/pages/management/Overview.jsx
import { useEffect, useState } from "react";
import api from "../../api/client";

export default function Overview() {
  const [counts, setCounts] = useState({ students: 0, ebooks: 0, holidays: 0 });

  useEffect(() => {
    async function load() {
      const [students, ebooks, holidays] = await Promise.all([
        api.get("/api/students"),
        api.get("/api/ebooks"),
        api.get("/api/holidays"),
      ]);
      setCounts({
        students: students.data.length,
        ebooks: ebooks.data.length,
        holidays: holidays.data.length,
      });
    }
    load();
  }, []);

  return (
    <div>
      <h1 className="mb-4">Management Overview</h1>
      <div className="row g-3">
        {[
          { label: "Students", value: counts.students },
          { label: "eBooks", value: counts.ebooks },
          { label: "Holidays", value: counts.holidays },
        ].map((c) => (
          <div className="col-md-4" key={c.label}>
            <div className="card text-center shadow-sm">
              <div className="card-body">
                <h2 className="text-danger">{c.value}</h2>
                <p className="text-muted mb-0">{c.label}</p>
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}