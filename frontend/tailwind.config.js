/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  darkMode: "class",
  theme: {
    extend: {
      colors: {
        // VAYORA Brand Palette
        primary: {
          50:  "#f0f4ff",
          100: "#dde8ff",
          200: "#bbd0ff",
          300: "#85adff",
          400: "#4d83ff",
          500: "#1a56db",  // Core brand blue
          600: "#1545c1",
          700: "#1037a0",
          800: "#0d2d82",
          900: "#0a2167",
        },
        accent: {
          50:  "#fff9ed",
          100: "#fef2d5",
          200: "#fde2a1",
          300: "#fbcc62",
          400: "#f9b02a",
          500: "#f79009",  // Amber accent
          600: "#de6b06",
          700: "#b84d09",
          800: "#943c10",
          900: "#793311",
        },
        success: "#10b981",
        warning: "#f59e0b",
        error:   "#ef4444",
        info:    "#3b82f6",
        // Dark mode surfaces
        surface: {
          900: "#0f172a",
          800: "#1e293b",
          700: "#334155",
          600: "#475569",
        },
      },
      fontFamily: {
        sans:  ["Inter", "system-ui", "sans-serif"],
        mono:  ["JetBrains Mono", "monospace"],
      },
      animation: {
        "fade-in":     "fadeIn 0.3s ease-in-out",
        "slide-up":    "slideUp 0.4s ease-out",
        "pulse-slow":  "pulse 3s ease-in-out infinite",
        "spin-slow":   "spin 3s linear infinite",
      },
      keyframes: {
        fadeIn: {
          "0%":   { opacity: "0" },
          "100%": { opacity: "1" },
        },
        slideUp: {
          "0%":   { opacity: "0", transform: "translateY(20px)" },
          "100%": { opacity: "1", transform: "translateY(0)" },
        },
      },
      boxShadow: {
        "glass":  "0 8px 32px 0 rgba(31, 38, 135, 0.37)",
        "glow":   "0 0 20px rgba(26, 86, 219, 0.5)",
        "card":   "0 4px 24px rgba(0, 0, 0, 0.15)",
      },
      backdropBlur: {
        xs: "2px",
      },
    },
  },
  plugins: [],
};
