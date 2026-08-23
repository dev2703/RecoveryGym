/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    "./app/**/*.{js,ts,jsx,tsx}",
    "./components/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        gym: {
          bg: "#18181b",
          surface: "#1f1f23",
          panel: "#27272a",
          panelHover: "#3f3f46",
          border: "#3f3f46",
          accent: "#FEF08A",
          accentHover: "#FDE047",
          accentMuted: "#854d0e",
          muted: "#a1a1aa",
          danger: "#f87171",
          success: "#4ade80",
          purple: "#a78bfa",
          cyan: "#22d3ee",
        },
      },
      fontFamily: {
        sans: ["var(--font-inter)", "system-ui", "sans-serif"],
      },
      boxShadow: {
        glow: "0 0 40px -8px rgba(254, 240, 138, 0.25)",
        card: "0 4px 24px -4px rgba(0, 0, 0, 0.4)",
      },
      animation: {
        "fade-up": "fadeUp 0.5s ease-out forwards",
        float: "float 6s ease-in-out infinite",
        marquee: "marquee 40s linear infinite",
      },
      keyframes: {
        fadeUp: {
          "0%": { opacity: "0", transform: "translateY(16px)" },
          "100%": { opacity: "1", transform: "translateY(0)" },
        },
        float: {
          "0%, 100%": { transform: "translateY(0)" },
          "50%": { transform: "translateY(-8px)" },
        },
        marquee: {
          "0%": { transform: "translateX(0)" },
          "100%": { transform: "translateX(-50%)" },
        },
      },
    },
  },
  plugins: [],
};
