import { Navigate, Outlet } from "react-router";

import { useAuth } from "../../hooks/useAuth";

export default function ProtectedRoute() {
  const {
    token,
    isLoading,
    isAuthenticated,
  } = useAuth();

  if (!token) {
    return <Navigate to="/login" replace />;
  }

  if (isLoading) {
    return (
      <div className="flex min-h-screen items-center justify-center">
        <p className="text-slate-600">
          Loading...
        </p>
      </div>
    );
  }

  if (!isAuthenticated) {
    localStorage.removeItem("access_token");

    return <Navigate to="/login" replace />;
  }

  return <Outlet />;
}