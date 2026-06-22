/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  darkMode: 'class',
  theme: {
    extend: {
      colors: {
        background: "#0A0F1E",
        surface: "#0A0F1E",
        "surface-container": "#111827",
        "surface-container-low": "#111827",
        "surface-container-high": "#25293a",
        "surface-container-highest": "#111827",
        "surface-container-lowest": "#090e1c",
        "surface-bright": "#343949",
        "surface-dim": "#0A0F1E",
        "surface-variant": "#2f3445",
        primary: "#10b981",
        "primary-container": "#059669",
        "on-primary": "#003824",
        secondary: "#b9c8de",
        "secondary-container": "#39485a",
        "on-secondary": "#233143",
        tertiary: "#ffb95f",
        "tertiary-container": "#e29100",
        "on-tertiary": "#472a00",
        error: "#ffb4ab",
        "error-container": "#93000a",
        "on-error": "#690005",
        "on-surface": "#dee1f7",
        "on-surface-variant": "#bbcabf",
        outline: "#86948a",
        "outline-variant": "#3c4a42",
      },
      borderRadius: {
        DEFAULT: "0.125rem",
        lg: "0.25rem",
        xl: "0.5rem",
        full: "0.75rem",
      },
      fontFamily: {
        headline: ["Space Grotesk", "sans-serif"],
        body: ["Space Grotesk", "sans-serif"],
        label: ["Space Grotesk", "sans-serif"],
        data: ["IBM Plex Mono", "monospace"],
      },
      backgroundImage: {
        'grid-mesh': 'linear-gradient(to right, rgba(134, 148, 138, 0.05) 1px, transparent 1px), linear-gradient(to bottom, rgba(134, 148, 138, 0.05) 1px, transparent 1px)',
      },
      backgroundSize: {
        'grid-mesh': '40px 40px',
      },
    },
  },
  plugins: [],
}
