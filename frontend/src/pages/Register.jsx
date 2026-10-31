
import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { useAuth } from "../context/AuthContext";
import {
  ScanLine,
  UserRound,
  Mail,
  LockKeyhole,
  Eye,
  EyeOff,
  ArrowRight,
  ShieldCheck,
  LoaderCircle,
  CheckCircle2,
  Activity,
  BrainCircuit,
  FileSearch,
  Sparkles,
} from "lucide-react";

export default function Register() {
  const { register } = useAuth();
  const navigate = useNavigate();

  const [form, setForm] = useState({
    name: "",
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
      await register(form.name, form.email, form.password);
      navigate("/dashboard");
    } catch (err) {
      const detail = err.response?.data?.detail;

      setError(
        typeof detail === "string"
          ? detail
          : "Registration failed. Please check your details and try again."
      );
    } finally {
      setSubmitting(false);
    }
  };

  const passwordChecks = [
    {
      label: "At least 8 characters",
      valid: form.password.length >= 8,
    },
  ];

  return (
    <main className="relative min-h-screen overflow-x-hidden bg-gradient-to-br from-slate-50 via-white to-blue-50 text-slate-900 lg:h-screen lg:overflow-hidden">
      {/* Background decoration */}
      <div className="pointer-events-none absolute inset-0 overflow-hidden">
        <div className="absolute -left-40 -top-40 h-96 w-96 rounded-full bg-blue-200/40 blur-[110px]" />
        <div className="absolute -bottom-40 -right-40 h-96 w-96 rounded-full bg-indigo-200/40 blur-[110px]" />
        <div className="absolute right-0 top-0 h-64 w-64 rounded-full bg-sky-100/60 blur-[90px]" />
      </div>

      <div className="relative mx-auto grid min-h-screen w-full max-w-[1600px] grid-cols-1 gap-6 px-5 py-6 sm:px-8 lg:h-screen lg:min-h-0 lg:grid-cols-[1.05fr_0.95fr] lg:gap-8 lg:px-10 lg:py-5 xl:gap-12 xl:px-14">
        {/* LEFT SIDE: Brand and animated video */}
        <section className="flex min-w-0 flex-col justify-center lg:min-h-0">
        </section>

 

        {/* RIGHT SIDE: Registration form */}
        <section className="flex min-w-0 items-center justify-center lg:min-h-0">
          <div className="w-full max-w-lg rounded-3xl border border-white bg-white/90 p-6 shadow-xl shadow-slate-200/70 backdrop-blur-xl sm:p-8 lg:max-h-[calc(100vh-2.5rem)] lg:overflow-y-auto lg:p-7 xl:p-9">
            {/* Form heading */}
            <div className="mb-5">
              {/* <div className="mb-3 inline-flex items-center gap-2 rounded-full border border-blue-100 bg-blue-50 px-3 py-1.5 text-xs font-semibold text-blue-700">
                <Sparkles size={14} />
                Get started with Scanalyze
              </div> */}

              <h2 className="text-3xl font-extrabold tracking-tight text-slate-900 sm:text-4xl">
                Create your
                <span className="ml-2 bg-gradient-to-r from-blue-600 via-indigo-600 to-sky-500 bg-clip-text text-transparent">
                  Account
                </span>
              </h2>

              <p className="mt-2 text-sm text-slate-500">
                Set up your account to get started.
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

            {/* Registration form */}
            <form onSubmit={handleSubmit} className="space-y-4">
              {/* Full name */}
              <div>
                <label
                  htmlFor="name"
                  className="mb-1.5 block text-sm font-semibold text-slate-700"
                >
                  Full name
                </label>

                <div className="group flex items-center rounded-xl border border-slate-200 bg-slate-50/80 transition focus-within:border-slate-300 focus-within:bg-white focus-within:ring-0">
                  <UserRound
                    size={18}
                    className="ml-3.5 shrink-0 text-slate-400 group-focus-within:text-blue-600"
                  />

                  <input
                    id="name"
                    name="name"
                    type="text"
                    placeholder="Enter your full name"
                    autoComplete="name"
                    value={form.name}
                    onChange={handleChange}
                    required
                    disabled={submitting}
                    className="w-full bg-transparent px-3 py-3 text-sm text-slate-900 outline-none ring-0 focus:outline-none focus:ring-0 focus-visible:outline-none placeholder:text-slate-400 disabled:opacity-60"
                  />
                </div>
              </div>

              {/* Email */}
              <div>
                <label
                  htmlFor="email"
                  className="mb-1.5 block text-sm font-semibold text-slate-700"
                >
                  Email address
                </label>

                <div className="group flex items-center rounded-xl border border-slate-200 bg-slate-50/80 transition focus-within:border-slate-300 focus-within:bg-white focus-within:ring-0">
                  <Mail
                    size={18}
                    className="ml-3.5 shrink-0 text-slate-400 group-focus-within:text-blue-600"
                  />

                  <input
                    id="email"
                    name="email"
                    type="email"
                    placeholder="you@example.com"
                    autoComplete="email"
                    value={form.email}
                    onChange={handleChange}
                    required
                    disabled={submitting}
                    className="w-full bg-transparent px-3 py-3 text-sm text-slate-900 outline-none ring-0 focus:outline-none focus:ring-0 focus-visible:outline-none placeholder:text-slate-400 disabled:opacity-60"
                  />
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
                    className="ml-3.5 shrink-0 text-slate-400 group-focus-within:text-blue-600"
                  />

                  <input
                    id="password"
                    name="password"
                    type={showPassword ? "text" : "password"}
                    placeholder="Create a strong password"
                    autoComplete="new-password"
                    value={form.password}
                    onChange={handleChange}
                    minLength={8}
                    required
                    disabled={submitting}
                    className="w-full min-w-0 bg-transparent px-3 py-3 text-sm text-slate-900 outline-none ring-0 focus:outline-none focus:ring-0 focus-visible:outline-none placeholder:text-slate-400 disabled:opacity-60"
                  />

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

                {/* Password validation hint */}
                <div className="mt-2 flex flex-wrap items-center gap-2">
                  {passwordChecks.map((check) => (
                    <span
                      key={check.label}
                      className={`inline-flex items-center gap-1.5 rounded-lg border px-2.5 py-1 text-xs transition ${
                        check.valid
                          ? "border-emerald-200 bg-emerald-50 text-emerald-700"
                          : "border-slate-200 bg-slate-50 text-slate-500"
                      }`}
                    >
                      <CheckCircle2 size={13} />
                      {check.label}
                    </span>
                  ))}
                </div>
              </div>

              {/* Submit button */}
              <button
                type="submit"
                disabled={submitting}
                className="group flex w-full items-center justify-center gap-2 rounded-xl bg-gradient-to-r from-blue-600 to-indigo-600 px-4 py-3 text-sm font-semibold text-white shadow-lg shadow-blue-600/20 transition duration-300 hover:from-blue-500 hover:to-indigo-500 hover:shadow-blue-500/30 focus:outline-none focus:ring-4 focus:ring-blue-500/20 disabled:cursor-not-allowed disabled:opacity-60"
              >
                {submitting ? (
                  <>
                    <LoaderCircle size={18} className="animate-spin" />
                    Creating account...
                  </>
                ) : (
                  <>
                    Create your account
                    <ArrowRight
                      size={18}
                      className="transition-transform group-hover:translate-x-1"
                    />
                  </>
                )}
              </button>
            </form>

            {/* Login link */}
            <div className="mt-5 text-center text-sm text-slate-500">
              Already have an account?{" "}
              <Link
                to="/login"
                className="font-semibold text-blue-600 transition hover:text-indigo-700"
              >
                Sign in
              </Link>
            </div>

            {/* Security note */}
            {/* <div className="mt-4 flex items-center justify-center gap-2 border-t border-slate-100 pt-4 text-xs text-slate-500">
              <ShieldCheck size={15} className="shrink-0 text-emerald-600" />
              Your account details are handled securely
            </div> */}
          </div>
        </section>
      </div>
    </main>
  );
}
