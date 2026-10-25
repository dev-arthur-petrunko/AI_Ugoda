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
        // Black · Coffee · Gold палитра (ТЗ v2, розділ 7.1)
        obsidian: "#080605",     // основний фон
        espresso: "#14100C",     // фон секцій
        coffee: "#241912",       // карточки
        mocha: "#3A2A1E",        // карточки на hover, розділювачі
        crema: "#6B4E37",        // вторичні акценти, рамки
        cream: "#EFE6D6",        // основний текст
        "cream-muted": "#A89983", // вторичний текст
        gold: "#C9A24B",         // основний акцент, кнопки
        "gold-bright": "#E8C871", // блики, hover
        "gold-deep": "#8F6F2B",  // тіні та градієнти
        "risk-low": "#7FA67A",   // риск низький (приглушений зелений)
        "risk-mid": "#E0A23B",   // риск середній
        "risk-high": "#C4574A",  // риск високий (кирбиновий червоний)
        bg: "#080605",
        "bg-secondary": "#14100C",
        sidebar: "#0C0D10",
        elevated: "#241912",
        card: "#241912",
        text: "#EFE6D6",
        "text-secondary": "#A89983",
        border: "rgba(201, 162, 75, 0.18)",
        success: "#7FA67A",
        warning: "#E0A23B",
        error: "#C4574A",
        info: "#6B4E37",
      },
      fontFamily: {
        sans: ["var(--font-inter)", "system-ui", "sans-serif"],
        serif: ["var(--font-playfair)", "Playfair Display", "serif"],
        display: ["var(--font-playfair)", "Playfair Display", "serif"],
        "source-serif": ["var(--font-source-serif)", "Source Serif 4", "serif"],
        mono: ["var(--font-jetbrains-mono)", "JetBrains Mono", "monospace"],
      },
      borderRadius: {
        md: "8px",
        lg: "12px",
        xl: "16px",
        full: "9999px",
      },
      animation: {
        "fade-in": "fadeIn 200ms ease-out",
        "slide-up": "slideUp 300ms ease-out",
        "pulse-soft": "pulseSoft 3s ease-in-out infinite",
        "logo-draw": "draw 1.2s ease-out forwards",
        "logo-pop": "pop 0.5s ease-out forwards",
        "logo-stamp": "stamp 0.6s cubic-bezier(0.2, 1.4, 0.4, 1) 1.4s forwards",
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
        draw: {
          "0%": { strokeDasharray: "1", strokeDashoffset: "1" },
          "100%": { strokeDashoffset: "0" },
        },
        pop: {
          "0%": { transform: "scale(0)" },
          "100%": { transform: "scale(1)" },
        },
        stamp: {
          "0%": { transform: "scale(0) rotate(-90deg)" },
          "100%": { transform: "scale(1) rotate(0)" },
        },
        shimmer: {
          "0%": { backgroundPosition: "200% 0" },
          "100%": { backgroundPosition: "-200% 0" },
        },
      },
    },
  },
  plugins: [],
};

export default config;