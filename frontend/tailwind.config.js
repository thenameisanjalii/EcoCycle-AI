/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{ts,tsx}'],
  theme: {
    extend: {
      fontFamily: { sans: ['Inter', 'ui-sans-serif', 'system-ui', 'sans-serif'] },
      colors: { ink: '#071a16', leaf: '#22c55e', mint: '#d9f99d', fog: '#f4f8f5' },
      boxShadow: { card: '0 20px 45px rgba(7, 26, 22, .08)' },
    },
  },
  plugins: [],
}
