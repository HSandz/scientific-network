/** @type {import('tailwindcss').Config} */
export default {
  darkMode: "class",
  content: ["./index.html", "./src/**/*.{js,ts,jsx,tsx}"],
  theme: {
    extend: {
      fontFamily: {
        sans: ["var(--sans)"],
        serif: ["var(--serif)"],
        // Data is never set in monospace; `font-mono` resolves to the interface face.
        mono: ["var(--sans)"],
      },
      colors: {
        paper: "var(--paper)",
        sunken: "var(--sunken)",
        ground: "var(--ground)",
        surface: "var(--surface)",
        raised: "var(--raised)",
        active: "var(--active)",
        border: "var(--border)",
        rule: "var(--rule)",
        control: "var(--control)",
        ink: "var(--ink)",
        muted: "var(--muted)",
        faint: "var(--faint)",
        decor: "var(--decor)",
        accent: "var(--accent)",
        cool: "var(--cool)",
        heat: "var(--heat)",
        neutral: "var(--neutral)",
        "cool-ink": "var(--cool-ink)",
        "heat-ink": "var(--heat-ink)",
        method: "var(--method)",
        task: "var(--task)",
        dataset: "var(--dataset)",
        org: "var(--org)",
        researcher: "var(--researcher)",
        topic: "var(--topic)",
      },
      borderRadius: {
        sm: "var(--r-sm)",
        md: "var(--r-md)",
        lg: "var(--r-lg)",
      },
    },
  },
  plugins: [],
};
