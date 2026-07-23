import type { Config } from "tailwindcss";

// Dark-first design tokens via CSS variables (see src/index.css):
// semantic colors swap per theme without touching components.
export default {
  darkMode: "class",
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        border: "hsl(var(--border))",
        input: "hsl(var(--input))",
        ring: "hsl(var(--ring))",
        background: "hsl(var(--background))",
        foreground: "hsl(var(--foreground))",
        card: { DEFAULT: "hsl(var(--card))", foreground: "hsl(var(--card-foreground))" },
        muted: { DEFAULT: "hsl(var(--muted))", foreground: "hsl(var(--muted-foreground))" },
        primary: { DEFAULT: "hsl(var(--primary))", foreground: "hsl(var(--primary-foreground))" },
        secondary: { DEFAULT: "hsl(var(--secondary))", foreground: "hsl(var(--secondary-foreground))" },
        success: "hsl(var(--success))",
        warning: "hsl(var(--warning))",
        destructive: "hsl(var(--destructive))",
      },
      borderRadius: { xl: "1rem", "2xl": "1.25rem" },
      fontFamily: {
        sans: ["Inter", "system-ui", "-apple-system", "Segoe UI", "Roboto", "sans-serif"],
        mono: ["ui-monospace", "SFMono-Regular", "Menlo", "monospace"],
      },
      keyframes: {
        "fade-up": { from: { opacity: "0", transform: "translateY(8px)" }, to: { opacity: "1", transform: "none" } },
        "fade-in": { from: { opacity: "0" }, to: { opacity: "1" } },
        "fade-out": { from: { opacity: "1" }, to: { opacity: "0" } },
        // Dialog keyframes keep the centering translate inside the animation so
        // Radix's enter/exit presence works without tailwindcss-animate.
        "dialog-in": {
          from: { opacity: "0", transform: "translate(-50%,-48%) scale(.97)" },
          to: { opacity: "1", transform: "translate(-50%,-50%) scale(1)" },
        },
        "dialog-out": {
          from: { opacity: "1", transform: "translate(-50%,-50%) scale(1)" },
          to: { opacity: "0", transform: "translate(-50%,-48%) scale(.97)" },
        },
        pulse: { "0%,100%": { opacity: "1" }, "50%": { opacity: ".4" } },
      },
      animation: {
        "fade-up": "fade-up .35s ease-out both",
        "fade-in": "fade-in .15s ease-out both",
        "fade-out": "fade-out .12s ease-in both",
        "dialog-in": "dialog-in .18s ease-out both",
        "dialog-out": "dialog-out .12s ease-in both",
      },
    },
  },
  plugins: [],
} satisfies Config;
