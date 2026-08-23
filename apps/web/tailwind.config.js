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
          bg: "#0a0e17",
          panel: "#111827",
          accent: "#22d3ee",
          danger: "#f87171",
          success: "#4ade80",
        },
      },
    },
  },
  plugins: [],
};
