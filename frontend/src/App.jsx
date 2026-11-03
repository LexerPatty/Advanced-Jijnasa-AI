
import { BrowserRouter, Navigate, Route, Routes } from "react-router-dom";

import { AuthProvider, useAuth } from "./context/AuthContext";

import ProtectedRoute from "./components/ProtectedRoute";

import Login from "./pages/Login";
import Register from "./pages/Register";
import Dashboard from "./pages/Dashboard";

import PdfToolRoutes from "./routes/PdfToolRoutes";

// --------------------------------------------------
// PUBLIC ROUTE
// Logged-in users shouldn't see login/register
// --------------------------------------------------

function PublicRoute({ children }) {
  const { user, loading } = useAuth();

  if (loading) {
    return null;
  }

  return user ? <Navigate to="/dashboard" replace /> : children;
}

// --------------------------------------------------
// MAIN APP
// --------------------------------------------------

export default function App() {
  return (
    <AuthProvider>
      <BrowserRouter>
        <Routes>

          {/* Login */}
          <Route
            path="/login"
            element={
              <PublicRoute>
                <Login />
              </PublicRoute>
            }
          />

          {/* Register */}
          <Route
            path="/register"
            element={
              <PublicRoute>
                <Register />
              </PublicRoute>
            }
          />

          {/* Protected Dashboard */}
          <Route
            path="/dashboard"
            element={
              <ProtectedRoute>
                <Dashboard />
              </ProtectedRoute>
            }
          />

          {/* Protected PDF Tools */}
          <Route
            path="/pdf-tools/*"
            element={
              <ProtectedRoute>
                <PdfToolRoutes />
              </ProtectedRoute>
            }
          />

          {/* Default Route */}
          <Route
            path="/"
            element={<Navigate to="/dashboard" replace />}
          />

          {/* Unknown Routes */}
          <Route
            path="*"
            element={<Navigate to="/dashboard" replace />}
          />

        </Routes>
      </BrowserRouter>
    </AuthProvider>
  );
}
