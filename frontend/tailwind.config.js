/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    "./app/**/*.{js,ts,jsx,tsx,mdx}",
    "./components/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      colors: {
        background: "#000000",
        foreground: "#ededed",
        canvas: {
          DEFAULT: "#000000",
          subtle: "#0a0a0a",
          elevated: "#121212",
        },
        ink: "#ededed",
        body: "#a1a1a1",
        mute: "#737373",
        faint: "#404040",
        hairline: {
          DEFAULT: "#262626",
          soft: "#1f1f1f",
          strong: "#333333",
        },
        card: "#0a0a0a",
        "card-foreground": "#ededed",
        border: "#262626",
        primary: {
          DEFAULT: "#ffffff",
          foreground: "#000000",
        },
        secondary: {
          DEFAULT: "#171717",
          foreground: "#ededed",
        },
        accent: {
          DEFAULT: "#0070f3",
          foreground: "#ffffff",
          deep: "#0761d1",
          soft: "rgba(0, 112, 243, 0.12)",
        },
      },
      borderRadius: {
        sm: "6px",
        md: "8px",
        lg: "12px",
        pill: "100px",
      },
    },
  },
  plugins: [],
}
