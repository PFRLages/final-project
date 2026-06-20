// src/pages/teacher/Ebooks.jsx
// Teacher's read-only view of the eBooks shared with them.
import { useEffect, useState } from "react";
import api from "../../api/client";

const API = api.defaults.baseURL;

export default function TeacherEbooks() {
  const [ebooks, setEbooks] = useState([]);

  useEffect(() => {
    api.get("/api/ebooks").then((res) => setEbooks(res.data));
  }, []);

  return (
    <div>
      <h1 className="mb-4">eBook Library</h1>
      {ebooks.length === 0 && (
        <p className="text-muted">No eBooks have been shared with you yet.</p>
      )}
      {ebooks.length > 0 && (
        <table className="table table-striped table-bordered" style={{ maxWidth: 700 }}>
          <thead className="table-dark"><tr><th>Name</th><th>Level</th><th>File</th></tr></thead>
          <tbody>
            {ebooks.map((b) => (
              <tr key={b.id}>
                <td>{b.name}</td>
                <td>{b.level}</td>
                <td><a href={encodeURI(`${API}${b.file_url}`)} target="_blank" rel="noreferrer">Open</a></td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </div>
  );
}