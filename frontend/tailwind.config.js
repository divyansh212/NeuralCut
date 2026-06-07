/** @type {import('tailwindcss').Config} */
module.exports = {
  content: ["./app/**/*.{ts,tsx}", "./lib/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        ink: "#050507",
        panel: "#0c0c10",
        line: "#1c1c22",
        gold: { DEFAULT: "#d8b886", hi: "#f0dcb0", dim: "#8a7150" },
        silver: "#cfd2d8",
      },
      fontFamily: {
        serif: ["Georgia", "Times New Roman", "serif"],
        mono: ["Courier New", "ui-monospace", "monospace"],
      },
      keyframes: {
        rise: { "0%": { opacity: "0", transform: "translateY(14px)" }, "100%": { opacity: "1", transform: "none" } },
        pulse2: { "0%,100%": { transform: "scale(1)", opacity: "1" }, "50%": { transform: "scale(1.4)", opacity: ".6" } },
      },
      animation: { rise: "rise .7s cubic-bezier(.2,.7,.2,1) both", pulse2: "pulse2 1.1s ease-in-out infinite" },
    },
  },
  plugins: [],
};
