/** @type {import('tailwindcss').Config} */
module.exports = {
  content: ['./src/**/*.{js,jsx}', './public/index.html'],
  theme: {
    extend: {
      colors: {
        brand: {
          DEFAULT: '#4a90e2',
          dark: '#357abd',
        },
        navy: '#2c3e50',
      },
    },
  },
  plugins: [],
};
