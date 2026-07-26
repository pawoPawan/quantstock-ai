/** @type {import('tailwindcss').Config} */
module.exports = {
  darkMode: "class",
  content: [
    "./pages/**/*.{js,ts,jsx,tsx,mdx}",
    "./components/**/*.{js,ts,jsx,tsx,mdx}",
    "./app/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      colors: {
        // Bloomberg Terminal inspired dark palette
        bg: {
          primary: "#0a0a0a",
          secondary: "#111111",
          card: "#141414",
          elevated: "#1a1a1a",
          hover: "#1e1e1e",
          border: "#242424",
        },
        brand: {
          DEFAULT: "#0074D9",
          light: "#1a8de8",
          dark: "#005bb5",
        },
        bull: {
          DEFAULT: "#00C853",
          light: "#69F0AE",
          muted: "#1a3a27",
        },
        bear: {
          DEFAULT: "#FF3D3D",
          light: "#FF7979",
          muted: "#3a1a1a",
        },
        warn: {
          DEFAULT: "#FFB800",
          light: "#FFD54F",
          muted: "#3a2e00",
        },
        text: {
          primary: "#E5E5E5",
          secondary: "#A0A0A0",
          muted: "#666666",
          inverse: "#0a0a0a",
        },
        accent: {
          blue: "#0074D9",
          purple: "#7B2FBE",
          cyan: "#00BCD4",
          orange: "#FF6B35",
        },
      },
      fontFamily: {
        mono: ["'JetBrains Mono'", "Consolas", "monospace"],
        sans: ["Inter", "system-ui", "sans-serif"],
      },
      animation: {
        "fade-in": "fadeIn 0.3s ease-in-out",
        "slide-up": "slideUp 0.3s ease-out",
        "pulse-green": "pulseGreen 2s infinite",
        "pulse-red": "pulseRed 2s infinite",
        shimmer: "shimmer 1.5s infinite",
      },
      keyframes: {
        fadeIn: { "0%": { opacity: "0" }, "100%": { opacity: "1" } },
        slideUp: { "0%": { opacity: "0", transform: "translateY(10px)" }, "100%": { opacity: "1", transform: "translateY(0)" } },
        pulseGreen: { "0%, 100%": { boxShadow: "0 0 0 0 rgba(0, 200, 83, 0.4)" }, "70%": { boxShadow: "0 0 0 10px rgba(0, 200, 83, 0)" } },
        pulseRed: { "0%, 100%": { boxShadow: "0 0 0 0 rgba(255, 61, 61, 0.4)" }, "70%": { boxShadow: "0 0 0 10px rgba(255, 61, 61, 0)" } },
        shimmer: { "100%": { transform: "translateX(100%)" } },
      },
      backgroundImage: {
        "gradient-radial": "radial-gradient(var(--tw-gradient-stops))",
        "grid-pattern": "linear-gradient(rgba(255,255,255,.03) 1px, transparent 1px), linear-gradient(90deg, rgba(255,255,255,.03) 1px, transparent 1px)",
      },
    },
  },
  plugins: [],
};
