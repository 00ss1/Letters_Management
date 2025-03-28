import React, { useState } from "react";
import LetterEditor from "./LetterEditor";
import Login from "./login";
import Signup from "./signup"; // Import Signup
import {
  BrowserRouter as Router,
  Route,
  Routes,
  Navigate,
  Link, // Import Link
} from "react-router-dom";

function App() {
  const [username, setUsername] = useState(
    localStorage.getItem("username") || null
  );

  const handleLogin = (username) => {
    setUsername(username);
    localStorage.setItem("username", username);
  };

  const handleLogout = () => {
    setUsername(null);
    localStorage.removeItem("username");
  };

  return (
    <Router>
      <Routes>
        <Route
          path="/login"
          element={
            username ? <Navigate to="/" /> : <Login onLogin={handleLogin} />
          }
        />
        <Route path="/signup" element={<Signup />} /> {/* Signup route */}
        <Route
          path="/"
          element={
            username ? (
              <LetterEditor onLogout={handleLogout} />
            ) : (
              <Navigate to="/login" />
            )
          }
        />
      </Routes>
      {!username && (
        <p>
          <Link to="/signup">Don't have an account? Signup</Link>
        </p>
      )}
    </Router>
  );
}

export default App;
