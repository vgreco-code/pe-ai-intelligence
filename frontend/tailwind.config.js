/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        navy: '#0D1B3E',
        teal: '#02C39A',
        orange: '#F24E1E',
        blue: '#1ABCFE',
        green: '#0ACF83',
        purple: '#A259FF',
        gold: '#F5A623',
      },
    },
  },
  plugins: [],
}
