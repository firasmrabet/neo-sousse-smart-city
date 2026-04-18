/** @type {import('tailwindcss').Config} */
import pluginAnimate from 'tailwindcss-animate'

export default {
  darkMode: ['class'],
  content: [
    './index.html',
    './src/**/*.{js,ts,jsx,tsx,html}'
  ],
  theme: {
    extend: {},
  },
  plugins: [
    pluginAnimate
  ],
}
