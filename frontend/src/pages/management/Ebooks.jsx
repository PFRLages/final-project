// src/pages/management/Ebooks.jsx
import { useEffect, useState } from "react";
import api from "../../api/client";

const API = api.defaults.baseURL;

export default function Ebooks() {
  const [ebooks, setEbooks] = useState([]);
  const [users, setUsers] = useState([]);
  const [levels, setLevels] = useState([]);          // level folder names
  const [form, setForm] = useState({ level: "" });
  const [file, setFile] = useState(null);
  const [error, setError] = useState("");

  const [shareBook, setShareBook] = useState(null);
  const [selectedUser, setSelectedUser] = useState("");
  const [shareSearch, setShareSearch] = useState("");

  const userMap = Object.fromEntries(users.map((u) => [u.id, u]));

  async function load() {
    const res = await api.get("/api/ebooks");
    setEbooks(res.data);
  }
  async function loadUsers() {
    const res = await api.get("/api/users");
    setUsers(res.data.filter((u) => u.role !== "management"));
  }
  async function loadLevels() {
    const res = await api.get("/api/ebooks/levels");
    setLevels(res.data.levels);
  }
  useEffect(() => {
    load();
    loadUsers();
    loadLevels();
  }, []);

  async function handleCreate(e) {
    e.preventDefault();
    setError("");
    try {
      const data = new FormData();
      data.append("level", form.level);
      data.append("file", file);
      await api.post("/api/ebooks/upload", data);
      setForm({ level: "" });
      setFile(null);
      e.target.reset();
      load();
      loadLevels(); // a brand-new level folder may have just been created
    } catch (err) {
      setError(err.response?.data?.detail || "Could not upload eBook");
    }
  }

  async function handleImport() {
    const res = await api.post("/api/ebooks/import-folder");
    alert(`Imported ${res.data.imported} PDF(s) from the uploads folder.`);
    load();
    loadLevels();
  }

  async function handleDelete(id) {
    if (!confirm("Delete this eBook?")) return;
    await api.delete(`/api/ebooks/${id}`);
    if (shareBook?.id === id) setShareBook(null);
    load();
  }

  function openShare(book) {
    setShareBook(book);
    setSelectedUser("");
    setShareSearch("");
  }
  function applyUpdatedBook(updated) {
    setShareBook(updated);
    setEbooks((list) => list.map((b) => (b.id === updated.id ? updated : b)));
  }
  async function handleShare(userId) {
    const res = await api.post(`/api/ebooks/${shareBook.id}/share`, { user_id: userId });
    applyUpdatedBook(res.data);
    setSelectedUser("");
  }
  async function handleUnshare(userId) {
    const res = await api.delete(`/api/ebooks/${shareBook.id}/share/${userId}`);
    applyUpdatedBook(res.data);
  }

  const availableUsers = shareBook
    ? users
      .filter((u) => !shareBook.shared_with.includes(u.id))
      .filter((u) => {
        const q = shareSearch.trim().toLowerCase();
        if (!q) return true;
        return (
          u.name.toLowerCase().includes(q) ||
          u.email.toLowerCase().includes(q) ||
          u.role.toLowerCase().includes(q)
        );
      })
    : [];

  return (
    <div>
      <h1 className="mb-4">eBook Library</h1>

      <form onSubmit={handleCreate} className="row g-2 mb-2">
        <div className="col">
          <input className="form-control" list="level-options" placeholder="Level (pick or type a new one)"
            value={form.level} onChange={(e) => setForm({ ...form, level: e.target.value })}
            required data-testid="ebook-level-input" />
          <datalist id="level-options">
            {levels.map((l) => <option key={l} value={l} />)}
          </datalist>
        </div>
        <div className="col">
          <input className="form-control" type="file" accept=".pdf"
            onChange={(e) => { setFile(e.target.files[0]); loadLevels(); }} required />
        </div>
        <div className="col-auto"><button className="btn btn-danger" type="submit">Upload</button></div>
      </form>

      <button className="btn btn-outline-secondary mb-3" onClick={handleImport}
        data-testid="import-folder-button">
        Import existing PDFs from uploads folder
      </button>
      {error && <p className="text-danger">{error}</p>}

      {/* Share panel */}
      {shareBook && (
        <div className="card card-body mb-3" data-testid="share-panel">
          <div className="d-flex justify-content-between align-items-center mb-2">
            <h5 className="mb-0">Share "{shareBook.name}"</h5>
            <button className="btn-close" onClick={() => setShareBook(null)} data-testid="close-share-panel" />
          </div>

          <strong>Shared with:</strong>
          {shareBook.shared_with.length === 0 && <span className="text-muted ms-2">No one yet</span>}
          <ul className="list-group mt-2 mb-3" style={{ maxWidth: 480 }}>
            {shareBook.shared_with.map((uid) => (
              <li key={uid} className="list-group-item d-flex justify-content-between align-items-center">
                {userMap[uid] ? `${userMap[uid].name} (${userMap[uid].role})` : uid}
                <button className="btn btn-sm btn-outline-danger" onClick={() => handleUnshare(uid)}
                  data-testid={`unshare-${uid}`}>Remove</button>
              </li>
            ))}
          </ul>

          <input className="form-control mb-2" style={{ maxWidth: 480 }}
            placeholder="Search teacher/student by name, email or role..."
            value={shareSearch} onChange={(e) => setShareSearch(e.target.value)}
            data-testid="share-search-input" />

          <div className="row g-2" style={{ maxWidth: 480 }}>
            <div className="col">
              <select className="form-select" value={selectedUser} size={6}
                onChange={(e) => setSelectedUser(e.target.value)} data-testid="share-user-select">
                {availableUsers.length === 0 && <option value="" disabled>No matches</option>}
                {availableUsers.map((u) => (
                  <option key={u.id} value={u.id}>{u.name} — {u.email} ({u.role})</option>
                ))}
              </select>
            </div>
            <div className="col-auto">
              <button className="btn btn-success" disabled={!selectedUser}
                onClick={() => handleShare(selectedUser)} data-testid="add-share-button">Add</button>
            </div>
          </div>
        </div>
      )}

      <table className="table table-striped table-bordered">
        <thead className="table-dark"><tr><th>Name</th><th>Level</th><th>File</th><th>Shared</th><th></th></tr></thead>
        <tbody>
          {ebooks.map((b) => (
            <tr key={b.id}>
              <td>{b.name}</td><td>{b.level || "-"}</td>
              <td><a href={encodeURI(`${API}${b.file_url}`)} target="_blank" rel="noreferrer">Open</a></td>
              <td><span className="badge bg-secondary">{b.shared_with?.length || 0}</span></td>
              <td>
                <button className="btn btn-sm btn-outline-primary me-2"
                  onClick={() => openShare(b)} data-testid={`share-${b.id}`}>Share</button>
                <button className="btn btn-sm btn-outline-danger" onClick={() => handleDelete(b.id)}>Delete</button>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}