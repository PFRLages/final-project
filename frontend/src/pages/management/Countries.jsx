//  src/pages/management/Countries.jsx
// English Passion — manage the countries used by holiday & student dropdowns.
import { useEffect, useState } from "react";
import api from "../../api/client";

export default function Countries() {
    const [countries, setCountries] = useState([]);
    const [name, setName] = useState("");
    const [error, setError] = useState("");

    const load = async () => {
        try {
            const res = await api.get("/api/countries");
            setCountries(res.data);
            setError("");
        } catch (err) {
            setError(err?.response?.data?.detail || "Failed to load countries");
        }
    };

    useEffect(() => {
        load();
    }, []);

    const handleAdd = async (e) => {
        e.preventDefault();
        try {
            await api.post("/api/countries", { name });
            setName("");
            load();
        } catch (err) {
            setError(err?.response?.data?.detail || "Failed to add country");
        }
    };

    const handleDelete = async (c) => {
        if (!window.confirm(`Delete ${c.name}?`)) return;
        try {
            await api.delete(`/api/countries/${c.id}`);
            load();
        } catch (err) {
            setError(err?.response?.data?.detail || "Failed to delete country");
        }
    };

    return (
        <div data-testid="countries-page">
            <h1 className="h3 mb-3">Countries</h1>
            {error && <div className="alert alert-danger" data-testid="countries-error">{error}</div>}

            <form className="row g-2 mb-4" onSubmit={handleAdd}>
                <div className="col-12 col-md-4">
                    <input
                        className="form-control"
                        placeholder="New country name"
                        required
                        value={name}
                        onChange={(e) => setName(e.target.value)}
                        data-testid="country-name-input"
                    />
                </div>
                <div className="col-12 col-md-2 d-grid">
                    <button className="btn btn-success" type="submit" data-testid="add-country-button">
                        Add
                    </button>
                </div>
            </form>

            <ul className="list-group" style={{ maxWidth: 480 }}>
                {countries.map((c) => (
                    <li
                        key={c.id}
                        className="list-group-item d-flex justify-content-between align-items-center"
                        data-testid={`country-row-${c.id}`}
                    >
                        {c.name}
                        <button
                            className="btn btn-sm btn-outline-danger"
                            onClick={() => handleDelete(c)}
                            data-testid={`delete-country-${c.id}`}
                        >
                            Delete
                        </button>
                    </li>
                ))}
                {countries.length === 0 && (
                    <li className="list-group-item text-muted">No countries yet</li>
                )}
            </ul>
        </div>
    );
}