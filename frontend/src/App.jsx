import { useState, useEffect } from "react";

function App() {
  const [students, setStudents] = useState([]);
  const [name, setName] = useState("");
  const [country, setCountry] = useState("");

  // reusable function to load students
  const loadStudents = () => {
    fetch("http://127.0.0.1:8000/students").then((response) => response.json()).then((data) => setStudents(data));
  };

  useEffect(() => {
    loadStudents();
  }, []);

  // runs when form is submitted
  const handleSubmit = (event) => {
    event.preventDefault(); // stop page reload
    fetch("http://127.0.0.1:8000/students", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ name: name, country: country }),
    }).then((response) => response.json()).then(() => {
      loadStudents(); // refresh list of students
      setName("");    // clear inputs
      setCountry("");
    });
  };

  return (
    < div >
      <h1>Students</h1>
      <form onSubmit={handleSubmit}>
        <input placeholder="Name" value={name} onChange={(e) => setName(e.target.value)}/>
        <input placeholder="Country" value={country} onChange={(e) => setCountry(e.target.value)}/>
        <button type="submit">Add Student</button>
      </form>
      <ul>
        {students.map((student) => (
          <li key={student.id}>
            {student.name} - {student.country}
          </li>
        ))}
      </ul>
    </div >
  );
}

export default App;

