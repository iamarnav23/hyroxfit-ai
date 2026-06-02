/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    "./pages/**/*.{js,jsx}",
    "./components/**/*.{js,jsx}",
  ],
  theme: {
    extend: {
      colors: {
        carbon: "#030303",
        charcoal: "#0c0a08",
        steel: "#18110c",
        volt: "#ff5a1f",
        electric: "#ffb000",
        ember: "#ff2f00",
      },
      boxShadow: {
        glow: "0 0 38px rgba(255, 90, 31, 0.28)",
      },
    },
  },
  plugins: [],
};
