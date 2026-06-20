// src/components/Layout.jsx
import { Link, useNavigate, Outlet, useLocation } from "react-router-dom";
import { useAuth } from "../context/AuthContext";

export default function Layout() {
    const { user, logout } = useAuth();
    const navigate = useNavigate();
    const location = useLocation();

    const handleLogout = () => {
        logout();
        navigate("/login");
    };

    // Menu items per role
    const menus = {
        management: [
            { to: "/management", label: "Dashboard" },
            { to: "/management/students", label: "Students" },
            { to: "/management/teachers", label: "Teachers" },
            { to: "/management/assignments", label: "Assignments" },
            { to: "/management/payments", label: "Payments" },
            { to: "/management/ebooks", label: "eBooks" },
            { to: "/management/holidays", label: "Holidays" },
            { to: "/management/countries", label: "Countries" },
            { to: "/management/users", label: "Users" },
        ],
        teacher: [
            { to: "/teacher", label: "Dashboard" },
            { to: "/teacher/schedule", label: "Schedule" },
            { to: "/teacher/ebooks", label: "eBooks" },
        ],
        student: [{ to: "/student", label: "Dashboard" }],
    };

    const items = menus[user?.role] || [];

    return (
        // vh-100 + w-100 + d-flex = full screen, no overflow gaps
        <div className="vh-100 w-100 d-flex">
            {/* Sidebar */}
            <aside
                className="bg-dark text-white d-flex flex-column flex-shrink-0 p-3"
                style={{ width: "240px" }}
            >
                <h2 className="h5 fw-bold mb-4">English Passion</h2>
                <nav className="nav nav-pills flex-column gap-1">
                    {items.map((item) => (
                        <Link
                            key={item.to}
                            to={item.to}
                            className={
                                "nav-link text-start " +
                                (location.pathname === item.to
                                    ? "active"
                                    : "text-white-50")
                            }
                            data-testid={`nav-${item.label.toLowerCase()}`}
                        >
                            {item.label}
                        </Link>
                    ))}
                </nav>

                <div className="mt-auto pt-3 border-top border-secondary">
                    <Link to="/profile" className="nav-link text-white-50">
                        {user?.name || "Profile"}
                    </Link>
                    <button
                        className="btn btn-outline-light btn-sm w-100 mt-2"
                        onClick={handleLogout}
                        data-testid="logout-button"
                    >
                        Logout
                    </button>
                </div>
            </aside>

            {/* Main content — flex-grow-1 + bg-light fills all remaining width */}
            <main className="flex-grow-1 overflow-auto bg-light">
                <div className="container-fluid p-4">
                    {user?.grace_days_left != null && (
                        <div className="alert alert-warning" data-testid="grace-period-banner">
                            Your account is scheduled for deactivation. You have{" "}
                            <strong>{user.grace_days_left} day{user.grace_days_left === 1 ? "" : "s"}</strong>{" "}
                            of access remaining. Please contact administration.
                        </div>
                    )}
                    <Outlet />
                </div>
            </main>
        </div>
    );
}