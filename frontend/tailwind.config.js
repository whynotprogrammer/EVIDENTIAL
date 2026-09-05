/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    "./app/**/*.{js,ts,jsx,tsx,mdx}",
    "./components/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      colors: {
        background: "#0b0f19",
        foreground: "#f8fafc",
        card: "#111827",
        "card-foreground": "#f9fafb",
        primary: {
          DEFAULT: "#3b82f6",
          foreground: "#ffffff",
        },
        secondary: {
          DEFAULT: "#1e293b",
          foreground: "#94a3b8",
        },
        border: "#1f2937",
        accent: {
          DEFAULT: "#06b6d4",
          foreground: "#ffffff",
        },
      },
    },
  },
  plugins: [],
}
