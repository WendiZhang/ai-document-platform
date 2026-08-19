import { useState } from "react";
import { Link, useNavigate } from "react-router";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { Eye, EyeOff } from "lucide-react";

import { loginUser } from "../api/auth";

export default function LoginPage() {
  const navigate = useNavigate();
  const queryClient = useQueryClient();

  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [showPassword, setShowPassword] =
    useState(false);

  const mutation = useMutation({
    mutationFn: loginUser,

    onSuccess: async (data) => {
      localStorage.setItem(
        "access_token",
        data.access_token,
      );

      await queryClient.invalidateQueries({
        queryKey: ["current-user"],
      });

      navigate("/dashboard");
    },
  });

  function handleSubmit(
    event: React.FormEvent<HTMLFormElement>,
  ) {
    event.preventDefault();

    mutation.mutate({
      email,
      password,
    });
  }

  return (
    <main className="relative flex min-h-screen items-center justify-center overflow-hidden bg-slate-950 px-6 py-12">
      <div className="pointer-events-none absolute -left-32 -top-32 h-96 w-96 rounded-full bg-blue-600/30 blur-3xl" />
      <div className="pointer-events-none absolute -bottom-40 -right-20 h-[28rem] w-[28rem] rounded-full bg-indigo-500/25 blur-3xl" />

      <div className="relative w-full max-w-md rounded-[2rem] border border-white/15 bg-white/[0.97] p-8 shadow-2xl shadow-black/30 sm:p-10">
        <p className="text-sm font-semibold uppercase tracking-[0.18em] text-blue-600">
          AI Document Platform
        </p>

        <h1 className="mt-4 text-3xl font-semibold text-slate-900">
          Welcome back
        </h1>

        <p className="mt-2 text-slate-600">
          Sign in to access your documents.
        </p>

        <form
          onSubmit={handleSubmit}
          className="mt-8 space-y-5"
        >
          <div>
            <label
              htmlFor="email"
              className="mb-2 block text-sm font-medium text-slate-700"
            >
              Email
            </label>

            <input
              id="email"
              type="email"
              value={email}
              onChange={(event) =>
                setEmail(event.target.value)
              }
              required
              className="w-full rounded-xl border border-slate-200 bg-slate-50/70 px-4 py-3 outline-none transition placeholder:text-slate-400 hover:border-slate-300 focus:border-blue-500 focus:bg-white focus:ring-4 focus:ring-blue-100"
            />
          </div>

          <div>
            <label
              htmlFor="password"
              className="mb-2 block text-sm font-medium text-slate-700"
            >
              Password
            </label>

            <div className="relative">
              <input
                id="password"
                type={showPassword ? "text" : "password"}
                value={password}
                onChange={(event) =>
                  setPassword(event.target.value)
                }
                required
                className="w-full rounded-xl border border-slate-200 bg-slate-50/70 px-4 py-3 pr-12 outline-none transition placeholder:text-slate-400 hover:border-slate-300 focus:border-blue-500 focus:bg-white focus:ring-4 focus:ring-blue-100"
              />

              <button
                type="button"
                onClick={() =>
                  setShowPassword((visible) => !visible)
                }
                aria-label={
                  showPassword
                    ? "Hide password"
                    : "Show password"
                }
                title={
                  showPassword
                    ? "Hide password"
                    : "Show password"
                }
                className="absolute inset-y-0 right-0 flex w-12 items-center justify-center rounded-r-xl text-slate-500 outline-none transition hover:text-blue-600 focus:outline-none focus:ring-0"
              >
                {showPassword ? (
                  <EyeOff size={19} />
                ) : (
                  <Eye size={19} />
                )}
              </button>
            </div>
          </div>

          {mutation.isError && (
            <p className="rounded-xl bg-red-50 px-4 py-3 text-sm text-red-700">
              Login failed. Please check your email and password.
            </p>
          )}

          <button
            type="submit"
            disabled={mutation.isPending}
            className="w-full rounded-xl bg-blue-600 !text-white px-4 py-3 font-semibold shadow-sm shadow-blue-200 transition hover:bg-blue-700 focus:outline-none focus:ring-4 focus:ring-blue-100 disabled:cursor-not-allowed disabled:opacity-60"
          >
            {mutation.isPending
              ? "Signing in..."
              : "Sign in"}
          </button>
        </form>

        <p className="mt-6 text-center text-sm text-slate-600">
          Don&apos;t have an account?{" "}
          <Link
            to="/register"
            className="font-medium text-blue-600 hover:text-blue-700"
          >
            Create one
          </Link>
        </p>
      </div>
    </main>
  );
}
