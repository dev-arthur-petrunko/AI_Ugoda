import type { Config } from "tailwindcss";

const config: Config = {
  darkMode: "class",
  content: [
    "./src/pages/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/components/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/app/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      colors: {
        bg: "#090A0C",
        "bg-secondary": "#101216",
        sidebar: "#0C0D10",
        elevated: "#15171B",
        card: "#17191E",
        gold: "#D6B15E",
        "gold-bright": "#F0D48A",
        "gold-muted": "#94763A",
        text: "#F4F1E8",
        "text-secondary": "#A5A7AE",
        border: "rgba(214, 177, 94, 0.18)",
        success: "#4A9E6E",
        warning: "#C9A227",
        error: "#C46A6A",
        info: "#7FA3B8",
      },
      fontFamily: {
        sans: ["var(--font-inter)", "system-ui", "sans-serif"],
      },
      borderRadius: {
        md: "8px",
        lg: "12px",
        full: "9999px",
      },
      animation: {
        "fade-in": "fadeIn 200ms ease-out",
        "slide-up": "slideUp 300ms ease-out",
        "pulse-soft": "pulseSoft 3s ease-in-out infinite",
      },
      keyframes: {
        fadeIn: {
          "0%": { opacity: "0" },
          "100%": { opacity: "1" },
        },
        slideUp: {
          "0%": { opacity: "0", transform: "translateY(8px)" },
          "100%": { opacity: "1", transform: "translateY(0)" },
        },
        pulseSoft: {
          "0%, 100%": { opacity: "0.6" },
          "50%": { opacity: "1" },
        },
      },
    },
  },
  plugins: [],
};

export default config;