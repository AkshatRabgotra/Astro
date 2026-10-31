/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        melooha: {
          bg: "#080511",
          card: "rgba(22, 16, 40, 0.88)",
          plum: "#B21E68",
          darkplum: "#931B58",
          lightplum: "#F4B8DC",
          gold: "#E5A93C",
        },
      },
      fontFamily: {
        serif: ["'Playfair Display'", "Georgia", "serif"],
        sans: ["'Inter'", "-apple-system", "BlinkMacSystemFont", "sans-serif"],
      },
    },
  },
  plugins: [],
};
