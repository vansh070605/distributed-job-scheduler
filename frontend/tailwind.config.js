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
        brand: {
          50: '#f0f7ff',
          100: '#e0efff',
          200: '#b8dbff',
          300: '#7abeff',
          400: '#339eff',
          500: '#007eff',
          600: '#0061cc',
          700: '#004aa3',
          800: '#003e8a',
          900: '#003373',
        }
      }
    },
  },
  plugins: [],
}
