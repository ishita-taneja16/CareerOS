/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        background: "#0b0f19",
        card: "#151d30",
        border: "#232e48",
        primary: "#6366f1",
        primaryHover: "#4f46e5",
        textPrimary: "#f3f4f6",
        textSecondary: "#9ca3af",
      },
      fontFamily: {
        sans: ["Inter", "sans-serif"],
      },
    },
  },
  plugins: [],
}
