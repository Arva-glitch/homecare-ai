/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{js,jsx}'],
  theme: {
    extend: {
      colors: {
        brand: {
          50: '#effaf3', 100: '#d8f3e2', 200: '#b3e6c8', 300: '#81d2a7', 400: '#4fb882',
          500: '#2e9d66', 600: '#207e51', 700: '#1b6543', 800: '#185037', 900: '#14422f',
        },
        charcoal: {
          50: '#f6f7f7', 100: '#e2e5e5', 200: '#c5cbcb', 300: '#a0a9a9', 400: '#7b8686',
          500: '#606b6b', 600: '#4c5555', 700: '#3f4646', 800: '#2b3030', 900: '#1d2121', 950: '#121515',
        },
      },
      fontFamily: { sans: ['Inter', 'ui-sans-serif', 'system-ui', 'Segoe UI', 'Roboto', 'sans-serif'] },
      boxShadow: { card: '0 1px 2px rgba(18,21,21,0.04), 0 4px 16px rgba(18,21,21,0.05)' },
    },
  },
  plugins: [],
}
