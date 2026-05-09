/** @type {import('tailwindcss').Config} */

export default {
  darkMode: "class",
  content: ["./index.html", "./src/**/*.{js,ts,vue}"],
  theme: {
    container: {
      center: true,
    },
    extend: {
      colors: {
        ink: {
          900: "#FAFAF9",
          950: "#F4F4F5",
        },
        graphite: {
          700: "#E4E4E7",
          800: "#FFFFFF",
          900: "#F4F4F5",
        },
        moon: {
          50: "#18181B",
          100: "#27272A",
        },
        mist: {
          400: "#71717A",
          500: "#A1A1AA",
        },
        electric: {
          400: "#4F46E5",
          500: "#4338CA",
          600: "#3730A3",
        },
        ember: {
          400: "#F97316",
          500: "#EA580C",
        },
        success: "#16A34A",
        warning: "#D97706",
        danger: "#DC2626",
      },
      fontFamily: {
        display: [
          "'Space Grotesk'",
          "'Noto Serif SC'",
          "ui-sans-serif",
          "system-ui",
          "sans-serif",
        ],
        sans: [
          "'IBM Plex Sans'",
          "'PingFang SC'",
          "ui-sans-serif",
          "system-ui",
          "sans-serif",
        ],
      },
      fontSize: {
        h2: ["clamp(2rem, 3.5vw, 2.75rem)", { lineHeight: "1.15", letterSpacing: "-0.02em" }],
        h3: ["clamp(1.5rem, 2.5vw, 2rem)", { lineHeight: "1.2", letterSpacing: "-0.01em" }],
      },
      boxShadow: {
        glow: "0 0 0 1px rgba(79,70,229,0.18), 0 12px 40px -10px rgba(79,70,229,0.30)",
        "glow-sm": "0 0 0 1px rgba(79,70,229,0.14), 0 6px 20px -6px rgba(79,70,229,0.22)",
        ember: "0 0 0 1px rgba(249,115,22,0.20), 0 12px 40px -10px rgba(249,115,22,0.30)",
        soft: "0 1px 2px rgba(15,23,42,0.04), 0 4px 16px -4px rgba(15,23,42,0.08)",
      },
      backgroundImage: {
        "hero-glow":
          "radial-gradient(60% 60% at 50% 0%, rgba(79,70,229,0.10) 0%, rgba(250,250,249,0) 70%)",
      },
      keyframes: {
        "node-pop": {
          "0%": { opacity: "0", transform: "translateY(4px) scale(0.96)" },
          "100%": { opacity: "1", transform: "translateY(0) scale(1)" },
        },
        "pulse-ring": {
          "0%": { boxShadow: "0 0 0 0 rgba(79,70,229,0.45)" },
          "70%": { boxShadow: "0 0 0 12px rgba(79,70,229,0)" },
          "100%": { boxShadow: "0 0 0 0 rgba(79,70,229,0)" },
        },
        "fade-up": {
          "0%": { opacity: "0", transform: "translateY(12px)" },
          "100%": { opacity: "1", transform: "translateY(0)" },
        },
        float: {
          "0%, 100%": { transform: "translateY(0)" },
          "50%": { transform: "translateY(-6px)" },
        },
      },
      animation: {
        "node-pop": "node-pop 320ms ease-out both",
        "pulse-ring": "pulse-ring 1.8s ease-out infinite",
        "fade-up": "fade-up 600ms ease-out both",
        float: "float 5s ease-in-out infinite",
      },
    },
  },
  plugins: [],
};
