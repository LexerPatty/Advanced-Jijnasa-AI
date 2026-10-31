
import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { useAuth } from "../context/AuthContext";
import {
  Activity,
  ScanLine,
  Mail,
  LockKeyhole,
  Eye,
  EyeOff,
  ArrowRight,
  Sparkles,
  ShieldCheck,
  LoaderCircle,
  BrainCircuit,
  FileSearch,
} from "lucide-react";

export default function Login() {
  const { login } = useAuth();
  const navigate = useNavigate();

  const [form, setForm] = useState({
    email: "",
    password: "",
  });

  const [error, setError] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [showPassword, setShowPassword] = useState(false);

  const handleChange = (e) => {
    setForm({ ...form, [e.target.name]: e.target.value });
    if (error) setError("");
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError("");
    setSubmitting(true);

    try {
      await login(form.email, form.password);
      navigate("/dashboard");
    } catch (err) {
      const detail = err.response?.data?.detail;
      setError(
        typeof detail === "string" ? detail : "Login failed. Please try again."
      );
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <main className="relative min-h-screen overflow-x-hidden bg-gradient-to-br from-slate-50 via-white to-blue-50 text-slate-900 lg:h-screen lg:overflow-hidden">
      {/* Background decoration */}
      <div className="pointer-events-none absolute inset-0 overflow-hidden">
        <div className="absolute -left-40 -top-40 h-96 w-96 rounded-full bg-blue-200/40 blur-[110px]" />
        <div className="absolute -bottom-40 -right-40 h-96 w-96 rounded-full bg-indigo-200/40 blur-[110px]" />
        <div className="absolute right-0 top-0 h-64 w-64 rounded-full bg-sky-100/60 blur-[90px]" />
      </div>

      <div className="relative mx-auto grid min-h-screen w-full max-w-[1600px] grid-cols-1 gap-6 px-5 py-6 sm:px-8 lg:h-screen lg:min-h-0 lg:grid-cols-[1.05fr_0.95fr] lg:gap-8 lg:px-10 lg:py-5 xl:gap-12 xl:px-14">
        {/* LEFT SIDE: Branding and animated video */}
        <section className="flex min-w-0 flex-col justify-center lg:min-h-0">
        </section>

        {/* RIGHT SIDE: Login form */}
        <section className="flex min-w-0 items-center justify-center lg:min-h-0">
          <div className="w-full max-w-lg rounded-3xl border border-white bg-white/90 p-6 shadow-xl shadow-slate-200/70 backdrop-blur-xl sm:p-8 lg:max-h-[calc(100vh-2.5rem)] lg:overflow-y-auto lg:p-7 xl:p-9">
            {/* Form heading */}
            <div className="mb-6">
              {/* <div className="mb-3 inline-flex items-center gap-2 rounded-full border border-blue-100 bg-blue-50 px-3 py-1.5 text-xs font-semibold text-blue-700">
                <Sparkles size={14} />
                Welcome back
              </div> */}

              <h2 className="text-3xl font-extrabold tracking-tight text-slate-900 sm:text-4xl">
                Sign in
                <span className="ml-2 bg-gradient-to-r from-blue-600 via-indigo-600 to-sky-500 bg-clip-text text-transparent">
                  Account
                </span>
              </h2>

              <p className="mt-2 text-sm leading-6 text-slate-500">
                Enter your credentials to access your workspace.
              </p>
            </div>

            {/* Error message */}
            {error && (
              <div
                role="alert"
                className="mb-4 flex items-start gap-3 rounded-xl border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700"
              >
                <span className="mt-0.5 font-bold">!</span>
                <p>{error}</p>
              </div>
            )}

            {/* Login form */}
            <form onSubmit={handleSubmit} className="space-y-4">
              {/* Email */}
              <div>
                <label
                  htmlFor="email"
                  className="mb-1.5 block text-sm font-semibold text-slate-700"
                >
                  Email address
                </label>

                <div className="group flex items-center rounded-xl border border-slate-200 bg-slate-50/80 transition focus-within:border-blue-400 focus-within:bg-white focus-within:ring-4 focus-within:ring-blue-500/10">
                  <Mail
                    size={18}
                    className="ml-3.5 shrink-0 text-slate-400 transition group-focus-within:text-blue-600"
                  />

                 <input
                    id="email"
                    name="email"
                    type="email"
                    placeholder="you@example.com"
                    autoComplete="off"
                    value={form.email}
                    onChange={handleChange}
                    required
                    disabled={submitting}
                    className="w-full bg-transparent px-3 py-3 text-sm text-slate-900 outline-none ring-0 focus:outline-none focus:ring-0 focus-visible:outline-none placeholder:text-slate-400 disabled:opacity-60"                    />
                </div>
              </div>

              {/* Password */}
              <div>
                <label
                  htmlFor="password"
                  className="mb-1.5 block text-sm font-semibold text-slate-700"
                >
                  Password
                </label>

                <div className="group flex items-center rounded-xl border border-slate-200 bg-slate-50/80 transition focus-within:border-blue-400 focus-within:bg-white focus-within:ring-4 focus-within:ring-blue-500/10">
                  <LockKeyhole
                    size={18}
                    className="ml-3.5 shrink-0 text-slate-400 transition group-focus-within:text-blue-600"
                  />

                  <input
                    id="password"
                    name="password"
                    type={showPassword ? "text" : "password"}
                    placeholder="Enter your password"
                    autoComplete="new-password"
                    value={form.password}
                    onChange={handleChange}
                    required
                    disabled={submitting}
                    className="w-full min-w-0 bg-transparent px-3 py-3 text-sm text-slate-900 outline-none ring-0 focus:outline-none focus:ring-0 focus-visible:outline-none placeholder:text-slate-400 disabled:opacity-60"                    />

                  <button
                    type="button"
                    onClick={() => setShowPassword(!showPassword)}
                    aria-label={showPassword ? "Hide password" : "Show password"}
                    aria-pressed={showPassword}
                    className="mr-2.5 rounded-lg p-1.5 text-slate-400 transition hover:bg-slate-100 hover:text-slate-700 focus:outline-none focus:ring-2 focus:ring-blue-400/50"
                  >
                    {showPassword ? (
                      <EyeOff size={18} />
                    ) : (
                      <Eye size={18} />
                    )}
                  </button>
                </div>
              </div>

              {/* Submit */}
              <button
                type="submit"
                disabled={submitting}
                className="group flex w-full items-center justify-center gap-2 rounded-xl bg-gradient-to-r from-blue-600 to-indigo-600 px-4 py-3 text-sm font-semibold text-white shadow-lg shadow-blue-600/20 transition duration-300 hover:from-blue-500 hover:to-indigo-500 hover:shadow-blue-500/30 focus:outline-none focus:ring-4 focus:ring-blue-500/20 disabled:cursor-not-allowed disabled:opacity-60"
              >
                {submitting ? (
                  <>
                    <LoaderCircle size={18} className="animate-spin" />
                    Signing in...
                  </>
                ) : (
                  <>
                    Sign in to your account
                    <ArrowRight
                      size={18}
                      className="transition-transform group-hover:translate-x-1"
                    />
                  </>
                )}
              </button>
            </form>

            {/* Register link */}
            <div className="mt-5 text-center text-sm text-slate-500">
              Don't have an account?{" "}
              <Link
                to="/register"
                className="font-semibold text-blue-600 transition hover:text-indigo-700"
              >
                Create account
              </Link>
            </div>

            {/* Security note */}
            {/* <div className="mt-4 flex items-center justify-center gap-2 border-t border-slate-100 pt-4 text-xs text-slate-500">
              <ShieldCheck size={15} className="shrink-0 text-emerald-600" />
              Secure access to your personal workspace
            </div> */}
          </div>
        </section>
      </div>
    </main>
  );
}
