import { useQuery } from "@tanstack/react-query";

import { getCurrentUser } from "../api/auth";

export function useAuth() {
  const token = localStorage.getItem("access_token");

  const query = useQuery({
    queryKey: ["current-user"],
    queryFn: getCurrentUser,
    enabled: Boolean(token),
    retry: false,
  });

  return {
    token,
    user: query.data,
    isLoading: query.isLoading,
    isAuthenticated: Boolean(token && query.data),
    error: query.error,
  };
}