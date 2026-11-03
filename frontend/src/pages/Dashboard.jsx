
import { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { useAuth } from "../context/AuthContext";

import {
  LogOut,
  ArrowUpRight,
  Sparkles,
  FileText,
  FileSpreadsheet,
  Presentation,
  Image,
  Archive,
  FileImage,
  FileType,
  FileCode,
  Scissors,
  Layers,
  Trash2,
  Copy,
  RotateCw,
  ScanLine,
  Minimize2,
  Combine,
  Languages,
  MessageCircleQuestion,
  AlignLeft,
  Table,
  GitCompareArrows,
  LockKeyhole,
  UnlockKeyhole,
  WandSparkles,
  Zap,
  ShieldCheck,
  FileCode2,
} from "lucide-react";

import logo from "../assets/logo_icon.png";

import docsBucket from "../assets/docs_bucket.png";

// --------------------------------------------------
// CATEGORY FILTERS
// --------------------------------------------------

const categories = [
  { id: "all", label: "All Tools", emoji: "🌈" },
  { id: "convert", label: "Convert PDF", emoji: "🔄" },
  { id: "optimize", label: "Optimize PDF", emoji: "⚡" },
  { id: "organize", label: "Organize PDF", emoji: "📚" },
  { id: "intelligence", label: "PDF Intelligence", emoji: "🤖" },
  { id: "security", label: "PDF Security", emoji: "🔐" },
];

// --------------------------------------------------
// PDF TOOLS
// --------------------------------------------------

const sections = [
  {
    id: "convert",
    title: "Convert PDF",
    subtitle: "Turn your files into different formats!",
    emoji: "🔄",
    description: "Convert documents into PDF and vice versa.",
    theme: "from-blue-500 to-cyan-400",
    light: "bg-blue-50",
    tools: [
      {
        title: "PDF to Word",
        description: "Convert PDF files into editable DOC/DOCX documents.",
        icon: FileText,
        emoji: "📝",
        color: "bg-blue-100 text-blue-600",
        route: "/pdf-tools/pdf-to-word",
      },
      {
        title: "PDF to Excel",
        description: "Convert PDF documents into XLS/XLSX spreadsheets.",
        icon: FileSpreadsheet,
        emoji: "📊",
        color: "bg-green-100 text-green-600",
        route: "/pdf-tools/pdf-to-excel",
      },
      {
        title: "PDF to PowerPoint",
        description: "Transform PDF pages into PPT/PPTX presentations.",
        icon: Presentation,
        emoji: "🎨",
        color: "bg-orange-100 text-orange-600",
        route: "/pdf-tools/pdf-to-powerpoint",
      },
      {
        title: "PDF to JPG",
        description: "Convert PDF pages into high-quality images.",
        icon: Image,
        emoji: "🖼️",
        color: "bg-pink-100 text-pink-600",
        route: "/pdf-tools/pdf-to-jpg",
      },
      {
        title: "PDF to PDF/A",
        description: "Convert PDFs into archival PDF/A format.",
        icon: Archive,
        emoji: "📦",
        color: "bg-purple-100 text-purple-600",
        route: "/pdf-tools/pdf-to-pdfa",
      },
      {
        title: "Word to PDF",
        description: "Convert Word documents into PDF files.",
        icon: FileType,
        emoji: "📃",
        color: "bg-sky-100 text-sky-600",
        route: "/pdf-tools/word-to-pdf",
      },
      {
        title: "Excel to PDF",
        description: "Convert Excel spreadsheets into PDF files.",
        icon: FileSpreadsheet,
        emoji: "📈",
        color: "bg-emerald-100 text-emerald-600",
        route: "/pdf-tools/excel-to-pdf",
      },
      {
        title: "PowerPoint to PDF",
        description: "Convert presentations into PDF documents.",
        icon: Presentation,
        emoji: "📽️",
        color: "bg-amber-100 text-amber-600",
        route: "/pdf-tools/powerpoint-to-pdf",
      },
      {
        title: "JPG to PDF",
        description: "Combine images and convert them into PDF.",
        icon: FileImage,
        emoji: "📸",
        color: "bg-rose-100 text-rose-600",
        route: "/pdf-tools/jpg-to-pdf",
      },
      {
        title: "HTML to PDF",
        description: "Convert HTML files and webpages into PDF.",
        icon: FileCode,
        emoji: "🌐",
        color: "bg-indigo-100 text-indigo-600",
        route: "/pdf-tools/html-to-pdf",
      },
    ],
  },

  {
    id: "optimize",
    title: "Optimize PDF",
    subtitle: "Make your PDFs smaller and smarter!",
    emoji: "⚡",
    description: "Improve PDF quality and reduce file size.",
    theme: "from-amber-500 to-orange-400",
    light: "bg-amber-50",
    tools: [
      {
        title: "Compress PDF",
        description: "Reduce PDF file size without unnecessary quality loss.",
        icon: Minimize2,
        emoji: "🗜️",
        color: "bg-orange-100 text-orange-600",
        route: "/pdf-tools/compress-pdf",
      },
    ],
  },

  {
    id: "organize",
    title: "Organize PDF",
    subtitle: "Keep all your PDF pages neat and tidy!",
    emoji: "📚",
    description: "Manage, rearrange and organize your PDF documents.",
    theme: "from-violet-500 to-purple-400",
    light: "bg-violet-50",
    tools: [
      {
        title: "Merge PDF",
        description: "Combine multiple PDF documents into one file.",
        icon: Combine,
        emoji: "🧩",
        color: "bg-violet-100 text-violet-600",
        route: "/pdf-tools/merge-pdf",
      },
      {
        title: "Split PDF",
        description: "Split a PDF into multiple smaller documents.",
        icon: Scissors,
        emoji: "✂️",
        color: "bg-pink-100 text-pink-600",
        route: "/pdf-tools/split-pdf",
      },
      {
        title: "Organize PDF",
        description: "Rearrange and manage your PDF pages easily.",
        icon: Layers,
        emoji: "📑",
        color: "bg-indigo-100 text-indigo-600",
        route: "/pdf-tools/organize-pdf",
      },
      {
        title: "Remove Pages",
        description: "Delete unwanted pages from your PDF.",
        icon: Trash2,
        emoji: "🗑️",
        color: "bg-rose-100 text-rose-600",
        route: "/pdf-tools/remove-pages",
      },
      {
        title: "Extract Pages",
        description: "Extract selected pages into a new PDF.",
        icon: Copy,
        emoji: "📋",
        color: "bg-cyan-100 text-cyan-600",
        route: "/pdf-tools/extract-pages",
      },
      {
        title: "Rotate PDF",
        description: "Rotate PDF pages to the correct orientation.",
        icon: RotateCw,
        emoji: "🔃",
        color: "bg-amber-100 text-amber-600",
        route: "/pdf-tools/rotate-pdf",
      },
      {
        title: "Scan to PDF",
        description: "Convert scanned documents and images into PDFs.",
        icon: ScanLine,
        emoji: "📷",
        color: "bg-teal-100 text-teal-600",
        route: "/pdf-tools/scan-to-pdf",
      },
    ],
  },

  {
    id: "intelligence",
    title: "PDF Intelligence",
    subtitle: "Let AI do the reading and thinking! 🤖",
    emoji: "🧠",
    description: "Understand, analyze and interact with your documents using AI.",
    theme: "from-fuchsia-500 to-pink-400",
    light: "bg-fuchsia-50",
    tools: [
      {
        title: "AI Summarizer",
        description: "Generate smart and meaningful PDF summaries.",
        icon: WandSparkles,
        emoji: "✨",
        color: "bg-fuchsia-100 text-fuchsia-600",
        route: "/pdf-tools/ai-summarizer",
      },
      {
        title: "Translate PDF",
        description: "Translate PDF content into different languages.",
        icon: Languages,
        emoji: "🌍",
        color: "bg-blue-100 text-blue-600",
        route: "/pdf-tools/translate-pdf",
      },
      {
        title: "PDF Question & Answer",
        description: "Ask questions and get answers from your PDFs.",
        icon: MessageCircleQuestion,
        emoji: "💬",
        color: "bg-emerald-100 text-emerald-600",
        route: "/pdf-tools/pdf-question-answer",
      },
      {
        title: "PDF to Markdown",
        description: "Extract PDF content into Markdown format.",
        icon: FileCode2,
        emoji: "📝",
        color: "bg-slate-100 text-slate-700",
        route: "/pdf-tools/pdf-to-markdown",
      },
      {
        title: "Extract PDF Text",
        description: "Extract readable text from PDF documents.",
        icon: AlignLeft,
        emoji: "📖",
        color: "bg-sky-100 text-sky-600",
        route: "/pdf-tools/extract-pdf-text",
      },
      {
        title: "Extract PDF Tables",
        description: "Extract tables and export them into Excel or CSV.",
        icon: Table,
        emoji: "📊",
        color: "bg-green-100 text-green-600",
        route: "/pdf-tools/extract-pdf-tables",
      },
      {
        title: "Compare PDF",
        description: "Compare documents and identify their differences.",
        icon: GitCompareArrows,
        emoji: "🔍",
        color: "bg-purple-100 text-purple-600",
        route: "/pdf-tools/compare-pdf",
      },
    ],
  },

  {
    id: "security",
    title: "PDF Security",
    subtitle: "Your documents deserve super protection! 🛡️",
    emoji: "🔐",
    description: "Protect your PDF documents and control access.",
    theme: "from-emerald-500 to-teal-400",
    light: "bg-emerald-50",
    tools: [
      {
        title: "Protect PDF",
        description: "Add password protection to secure your PDF files.",
        icon: LockKeyhole,
        emoji: "🔒",
        color: "bg-emerald-100 text-emerald-600",
        route: "/pdf-tools/protect-pdf",
      },
      {
        title: "Unlock PDF",
        description: "Remove password protection from authorized PDF files.",
        icon: UnlockKeyhole,
        emoji: "🔓",
        color: "bg-yellow-100 text-yellow-600",
        route: "/pdf-tools/unlock-pdf",
      },
    ],
  },
];

// --------------------------------------------------
// MAIN DASHBOARD
// --------------------------------------------------

export default function Dashboard() {
  const { user, logout } = useAuth();
  const navigate = useNavigate();

  const [activeCategory, setActiveCategory] = useState("all");
  const [loadingTool, setLoadingTool] = useState(null);

  // Cleanup navigation timer if the dashboard unmounts.
  const [navigationTimer, setNavigationTimer] = useState(null);

  useEffect(() => {
    return () => {
      if (navigationTimer) {
        clearTimeout(navigationTimer);
      }
    };
  }, [navigationTimer]);

  // --------------------------------------------------
  // TOOL CLICK WITH SPIRAL LOADING
  // --------------------------------------------------

  const handleToolClick = (tool) => {
    if (loadingTool) return;

    setLoadingTool(tool);

    const timer = setTimeout(() => {
      navigate(tool.route);
    }, 1800);

    setNavigationTimer(timer);
  };

  // --------------------------------------------------
  // LOGOUT
  // --------------------------------------------------

  const handleLogout = () => {
    if (navigationTimer) {
      clearTimeout(navigationTimer);
    }

    logout();
    navigate("/login");
  };

  // --------------------------------------------------
  // CATEGORY FILTER
  // --------------------------------------------------

  const visibleSections =
    activeCategory === "all"
      ? sections
      : sections.filter((section) => section.id === activeCategory);

  const totalTools = sections.reduce(
    (total, section) => total + section.tools.length,
    0
  );

  // --------------------------------------------------
  // LOADING SCREEN
  // --------------------------------------------------

  if (loadingTool) {
    return (
      <main className="fixed inset-0 z-[9999] flex min-h-screen items-center justify-center overflow-hidden bg-[#f8faff] text-slate-900">

        {/* Background decorations */}

        <div className="pointer-events-none absolute inset-0 overflow-hidden">
          <div className="absolute -right-40 -top-40 h-96 w-96 rounded-full bg-blue-200/40 blur-3xl" />
          <div className="absolute -bottom-40 -left-40 h-96 w-96 rounded-full bg-purple-200/40 blur-3xl" />
          <div className="absolute left-1/2 top-1/2 h-96 w-96 -translate-x-1/2 -translate-y-1/2 rounded-full bg-pink-100/30 blur-3xl" />
        </div>

        {/* Loading Content */}

        <div className="relative z-10 flex flex-col items-center px-6 text-center">

          {/* Spiral Animation */}

          <div className="relative flex h-48 w-48 items-center justify-center sm:h-56 sm:w-56">

            {/* Outer glow */}

            <div className="absolute inset-0 animate-pulse rounded-full bg-blue-400/10 blur-2xl" />

            {/* Rotating spiral SVG */}

            <svg
              viewBox="0 0 200 200"
              className="absolute inset-0 h-full w-full animate-[spiralRotate_2.5s_linear_infinite]"
              fill="none"
            >
              <defs>
                <linearGradient
                  id="spiralGradient"
                  x1="0"
                  y1="0"
                  x2="200"
                  y2="200"
                  gradientUnits="userSpaceOnUse"
                >
                  <stop offset="0%" stopColor="#60A5FA" />
                  <stop offset="35%" stopColor="#6366F1" />
                  <stop offset="70%" stopColor="#A855F7" />
                  <stop offset="100%" stopColor="#EC4899" />
                </linearGradient>
              </defs>

              {/* Spiral path */}

              <path
                d="M100 100
                   C100 92 108 92 108 100
                   C108 116 84 116 84 100
                   C84 76 124 76 124 100
                   C124 132 68 132 68 100
                   C68 60 140 60 140 100
                   C140 148 52 148 52 100
                   C52 44 156 44 156 100
                   C156 164 36 164 36 100
                   C36 28 172 28 172 100
                   C172 180 20 180 20 100"
                stroke="url(#spiralGradient)"
                strokeWidth="4"
                strokeLinecap="round"
                strokeLinejoin="round"
              />

              {/* Circular orbit */}

              <circle
                cx="100"
                cy="100"
                r="88"
                stroke="#CBD5E1"
                strokeWidth="1"
                strokeDasharray="4 8"
                opacity="0.5"
              />
            </svg>

            {/* Center Logo */}

            <div className="relative flex h-20 w-20 items-center justify-center overflow-hidden rounded-2xl sm:h-20 sm:w-20">

              <img
                src={logo}
                alt="NothiLipi AI"
                className="h-full w-full object-contain p-3"
              />

            </div>

            {/* Orbiting dot */}

            <div className="absolute inset-0 animate-[orbit_2s_linear_infinite]">
              <div className="absolute left-1/2 top-0 h-4 w-4 -translate-x-1/2 rounded-full border-2 border-white bg-blue-600 shadow-lg shadow-blue-300" />
            </div>

          </div>

          {/* Loading Text */}

          <div className="mt-8">

            <div className="mb-3 inline-flex items-center gap-2 rounded-full border border-indigo-100 bg-white/80 px-4 py-2 text-xs font-bold tracking-widest text-indigo-600 shadow-sm backdrop-blur-sm">

              <Sparkles size={14} className="animate-pulse" />

              NOTHILIPI.AI

            </div>

            <h2 className="special_heading text-2xl font-extrabold tracking-tight text-slate-800 sm:text-3xl">

              Opening {loadingTool.title}

            </h2>

            <p className="mt-3 text-sm font-medium tracking-wide text-slate-500">

              Preparing your workspace...

            </p>

          </div>

          {/* Loading Dots */}

          <div className="mt-6 flex items-center gap-2">

            <span className="h-2 w-2 animate-[loadingDot_1s_ease-in-out_infinite] rounded-full bg-blue-500" />

            <span className="h-2 w-2 animate-[loadingDot_1s_ease-in-out_0.2s_infinite] rounded-full bg-indigo-500" />

            <span className="h-2 w-2 animate-[loadingDot_1s_ease-in-out_0.4s_infinite] rounded-full bg-purple-500" />

          </div>

        </div>

        {/* Loading Screen Animations */}

        <style>{`
          @keyframes spiralRotate {
            from {
              transform: rotate(0deg);
            }
            to {
              transform: rotate(360deg);
            }
          }

          @keyframes orbit {
            from {
              transform: rotate(0deg);
            }
            to {
              transform: rotate(360deg);
            }
          }

          @keyframes loadingDot {
            0%, 100% {
              transform: translateY(0);
              opacity: 0.4;
            }
            50% {
              transform: translateY(-6px);
              opacity: 1;
            }
          }
        `}</style>

      </main>
    );
  }

  // --------------------------------------------------
  // DASHBOARD UI
  // --------------------------------------------------

  return (
    <main className="relative min-h-screen overflow-hidden bg-[#f8faff] text-slate-900">

      {/* Background decorations */}

      <div className="pointer-events-none fixed inset-0 overflow-hidden">
        <div className="absolute -right-40 -top-40 h-96 w-96 rounded-full bg-blue-200/30 blur-3xl" />
        <div className="absolute -bottom-40 -left-40 h-96 w-96 rounded-full bg-purple-200/30 blur-3xl" />
        <div className="absolute left-1/2 top-1/2 h-96 w-96 -translate-x-1/2 -translate-y-1/2 rounded-full bg-pink-100/20 blur-3xl" />
      </div>

      <div className="relative mx-auto max-w-[1800px] px-5 py-6 sm:px-8 lg:px-10">

        {/* HEADER */}

        <header className="mb-10 flex items-center justify-between gap-4">

          <div className="flex items-center gap-3">

            <div className="flex h-12 w-12 items-center justify-center overflow-hidden rounded-2xl bg-white shadow-md">
              <img
                src={logo}
                alt="PDF Workspace Logo"
                className="h-full w-full object-contain"
              />
            </div>

            <div>
              <h1 className="text-xl font-extrabold tracking-tight sm:text-2xl">
                Nothi<span className="text-blue-600">Lipi.AI</span>
              </h1>

              <p className="hidden text-[10px] font-semibold tracking-[0.18em] text-slate-400 sm:block">
                YOUR SMART PDF WORKSPACE
              </p>
            </div>

          </div>

          <div className="flex items-center gap-3">

            <div className="hidden text-right sm:block">
              <p className="text-[10px] font-semibold uppercase tracking-widest text-slate-400">
                Welcome back
              </p>

              <p className="mt-1 max-w-40 truncate text-sm font-bold tracking-wider text-slate-700">
                {user?.name || "User"}
              </p>
            </div>

            <div
              className="flex h-10 w-10 items-center justify-center rounded-full border border-blue-100 bg-blue-50 text-sm font-bold text-blue-700 sm:hidden"
              title={user?.name || "User"}
            >
              {(user?.name || "U").charAt(0).toUpperCase()}
            </div>

            <button
              onClick={handleLogout}
              title="Logout"
              className="flex cursor-pointer items-center gap-2 rounded-xl border border-slate-200 bg-white px-3 py-2.5 text-sm font-semibold text-slate-600 shadow-sm transition-all duration-200 hover:-translate-y-1 hover:border-red-200 hover:bg-red-50 hover:text-red-600 sm:px-4"
            >
              <LogOut size={17} />
              <span className="hidden sm:block">Logout</span>
            </button>

          </div>

        </header>






        

        {/* HERO SECTION............................................... */}

        
{/* HERO SECTION */}

<section className="relative mb-10 mt-4 min-h-[60px] rounded-[28px] bg-gradient-to-r from-blue-50 via-indigo-300 to-violet-600 p-7 text-white shadow-xl shadow-blue-200/40 sm:mt-8 sm:min-h-[60px] sm:p-10 lg:mt-10 lg:min-h-[60px]">

  {/* Background Decorations (clipped inside the card only) */}

  <div className="pointer-events-none absolute inset-0 overflow-hidden rounded-[28px]">
    <div className="absolute -right-10 -top-16 text-[180px] opacity-10">
      📄
    </div>

    <div className="absolute bottom-0 right-48 text-6xl opacity-20">
      ✨
    </div>

    <div className="absolute right-[35%] top-10 h-64 w-64 rounded-full bg-white/5 blur-3xl" />
  </div>

  {/* Hero Text Content */}

  <div className="relative z-10 max-w-2xl lg:max-w-[58%]">

    {/* Badge */}

    <div className="mb-4 inline-flex items-center gap-2 rounded-full border border-white/20 bg-white/15 px-4 py-2 text-xs font-bold tracking-wider backdrop-blur-sm">
      <Sparkles size={15} />
      YOUR ALL-IN-ONE PDF PLAYGROUND
    </div>

    {/* Greeting */}

    <h2 className="special_heading text-4xl font-bold tracking-tight sm:text-5xl lg:text-6xl">
      Hello, {((user?.name || "there").split(" ")[0])}! 👋
    </h2>

    {/* Description */}

    <p className="mt-4 max-w-xl text-sm leading-7 tracking-[0.03em] text-blue-50 sm:text-base">
      Ready to make your documents smarter? Convert, organize,
      protect and explore your PDFs with powerful AI tools.
    </p>

    {/* Features */}

    <div className="mt-6 flex flex-wrap items-center gap-3">

      <div className="flex items-center gap-2 rounded-xl bg-white/15 px-4 py-2.5 backdrop-blur-sm">
        <FileText size={17} />
        <span className="text-sm font-semibold">{totalTools} PDF Tools</span>
      </div>

      <div className="flex items-center gap-2 rounded-xl bg-white/15 px-4 py-2.5 backdrop-blur-sm">
        <Zap size={17} />
        <span className="text-sm font-semibold">AI Powered</span>
      </div>

      <div className="flex items-center gap-2 rounded-xl bg-white/15 px-4 py-2.5 backdrop-blur-sm">
        <ShieldCheck size={17} />
        <span className="text-sm font-semibold">Secure Workspace</span>
      </div>

    </div>

  </div>

  {/* DOCS BUCKET IMAGE (bigger, overflowing the top of the hero) */}

  <div className="pointer-events-none absolute -bottom-20 right-0 z-20 sm:right-2 lg:right-8">

    <img
      src={docsBucket}
      alt="Docs Bucket - PDF document workspace"
      className="h-[400px] w-[400px] object-contain drop-shadow-2xl sm:h-[460px] sm:w-[460px] lg:h-[620px] lg:w-[620px] xl:h-[680px] xl:w-[680px]"
    />

  </div>

</section>













        {/* CATEGORY FILTER */}

        <section className="mb-10">

          <div className="mb-5 flex items-center justify-between gap-3">

            <div>
              <h3 className="special_heading text-xl font-bold tracking-tight text-slate-800 sm:text-2xl">
                Explore PDF Tools
              </h3>

              <p className="mt-1 text-xs text-slate-500 sm:text-sm">
                Pick your favourite category and start exploring!
              </p>
            </div>

            <span className="hidden rounded-full bg-blue-50 px-3 py-1.5 font-mono text-xs font-bold text-blue-600 sm:block">
              {activeCategory === "all"
                ? `${totalTools} TOOLS`
                : `${visibleSections[0]?.tools.length || 0} TOOLS`}
            </span>

          </div>

          {/* Animated filter buttons */}

          <div className="flex flex-wrap gap-3">

            {categories.map((category) => {

              const isActive = activeCategory === category.id;

              return (
                <button
                  key={category.id}
                  onClick={() => setActiveCategory(category.id)}
                  className={`group flex cursor-pointer items-center gap-2 rounded-2xl border px-4 py-3 text-sm font-bold transition-all duration-300 hover:-translate-y-1 ${
                    isActive
                      ? "border-blue-600 bg-blue-600 text-white shadow-lg shadow-blue-200"
                      : "border-slate-200 bg-white text-slate-600 shadow-sm hover:border-blue-200 hover:bg-blue-50 hover:text-blue-700"
                  }`}
                >
                  <span className="text-lg transition-transform duration-300 group-hover:scale-125">
                    {category.emoji}
                  </span>

                  {category.label}

                  {isActive && (
                    <span className="ml-1 h-1.5 w-1.5 animate-pulse rounded-full bg-white" />
                  )}
                </button>
              );
            })}

          </div>

        </section>

        {/* PDF TOOL SECTIONS */}

        <div className="space-y-12">

          {visibleSections.map((section, sectionIndex) => (

            <section
              key={section.id}
              id={section.id}
              className="scroll-mt-8 animate-[fadeInUp_0.5s_ease-out_both]"
              style={{
                animationDelay: `${sectionIndex * 100}ms`,
              }}
            >

              {/* SECTION HEADER */}

              <div className="mb-6 flex items-center justify-between gap-4">

                <div className="flex items-center gap-3">

                  <div
                    className={`flex h-12 w-12 shrink-0 items-center justify-center rounded-2xl bg-gradient-to-br ${section.theme} text-2xl text-white shadow-lg`}
                  >
                    {section.emoji}
                  </div>

                  <div>

                    <h3 className="special_heading text-xl font-bold tracking-tight text-slate-800 sm:text-2xl">
                      {section.title}
                    </h3>

                    <p className="mt-1 text-xs text-slate-500 sm:text-sm">
                      {section.subtitle}
                    </p>

                  </div>

                </div>

                <span className="hidden rounded-full border border-slate-200 bg-white px-3 py-1.5 font-mono text-xs font-semibold text-slate-500 sm:block">
                  {String(section.tools.length).padStart(2, "0")} TOOLS
                </span>

              </div>

              {/* TOOL CARDS */}

              <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-5">

                {section.tools.map((tool, index) => {

                  const Icon = tool.icon;

                  return (
                    <button
                      key={tool.title}
                      type="button"
                      onClick={() => handleToolClick(tool)}
                      style={{
                        animationDelay: `${index * 65}ms`,
                      }}
                      className="group relative flex min-h-[230px] cursor-pointer flex-col overflow-hidden rounded-3xl border border-slate-200/80 bg-white p-5 text-left shadow-sm transition-all duration-300 hover:-translate-y-2 hover:border-blue-200 hover:shadow-xl hover:shadow-blue-100/60 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-blue-500 motion-safe:animate-[fadeInUp_0.5s_ease-out_both]"
                    >

                      {/* Decorative background */}

                      <div className="pointer-events-none absolute -right-8 -top-8 h-28 w-28 rounded-full bg-blue-50 opacity-70 transition-all duration-500 group-hover:scale-150 group-hover:bg-indigo-50" />

                      <div className="pointer-events-none absolute bottom-0 right-3 text-5xl opacity-[0.04] transition-all duration-300 group-hover:rotate-12 group-hover:scale-125">
                        {tool.emoji}
                      </div>

                      {/* Icon and emoji */}

                      <div className="relative flex w-full items-start justify-between">

                        <div
                          className={`flex h-12 w-12 items-center justify-center rounded-2xl ${tool.color} shadow-sm transition-all duration-300 group-hover:rotate-[-8deg] group-hover:scale-110`}
                        >
                          <Icon size={24} strokeWidth={1.9} />
                        </div>

                        <span className="text-2xl transition-transform duration-300 group-hover:scale-125 group-hover:-rotate-12">
                          {tool.emoji}
                        </span>

                      </div>

                      {/* Card content */}

                      <div className="relative mt-5 flex-1">

                        <h4 className="special_heading text-lg font-bold tracking-tight text-slate-800">
                          {tool.title}
                        </h4>

                        <p className="mt-2 text-xs leading-5 text-slate-500 sm:text-[13px]">
                          {tool.description}
                        </p>

                      </div>

                      {/* Card footer */}

                      <div className="relative mt-5 flex items-center justify-between border-t border-slate-100 pt-3">

                        <span className="text-xs font-bold tracking-wide text-slate-500 transition-colors group-hover:text-blue-600">
                          Try Now
                        </span>

                        <span className="flex h-8 w-8 items-center justify-center rounded-full bg-slate-50 text-slate-500 transition-all duration-300 group-hover:translate-x-1 group-hover:bg-blue-600 group-hover:text-white">
                          <ArrowUpRight size={17} />
                        </span>

                      </div>

                    </button>
                  );

                })}

              </div>

            </section>

          ))}

        </div>

        {/* FOOTER */}

        <footer className="mt-10 flex flex-col gap-2 border-t border-slate-200/80 pt-5 text-xs text-slate-400 sm:flex-row sm:items-center sm:justify-between">

          <p>NothiLipi.AI · Smart PDF Workspace</p>

          <p className="font-mono">
            AI DOCUMENT WORKSPACE / v1.0
          </p>

        </footer>

      </div>

      {/* DASHBOARD ANIMATIONS */}

      <style>{`
        @keyframes fadeInUp {
          from {
            opacity: 0;
            transform: translateY(18px);
          }
          to {
            opacity: 1;
            transform: translateY(0);
          }
        }

        html {
          scroll-behavior: smooth;
        }
      `}</style>

    </main>
  );
}
