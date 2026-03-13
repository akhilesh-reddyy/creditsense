/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{js,jsx}'],
  theme: {
    extend: {
      fontFamily: {
        display: ['"DM Serif Display"', 'Georgia', 'serif'],
        mono:    ['"JetBrains Mono"', 'monospace'],
        body:    ['"DM Sans"', 'sans-serif'],
      },
      colors: {
        ink:   { DEFAULT: '#0A0A0F', 50: '#F2F2F7', 100: '#E4E4EC', 200: '#C8C8D8', 400: '#8888A4', 600: '#44445A', 800: '#1A1A26', 900: '#0A0A0F' },
        acid:  { DEFAULT: '#B8FF3C', 50: '#F4FFE0', 100: '#E6FF99', 300: '#CCFF66', 400: '#B8FF3C', 500: '#96E620', 700: '#5A9900' },
        risk:  { low: '#22C55E', moderate: '#F59E0B', high: '#EF4444', critical: '#7C3AED' },
      },
      animation: {
        'slide-up':     'slideUp 0.4s cubic-bezier(0.16, 1, 0.3, 1) forwards',
        'fade-in':      'fadeIn 0.3s ease forwards',
        'score-fill':   'scoreFill 1.2s cubic-bezier(0.16, 1, 0.3, 1) forwards',
        'pulse-dot':    'pulseDot 2s ease-in-out infinite',
      },
      keyframes: {
        slideUp:    { from: { opacity: 0, transform: 'translateY(16px)' }, to: { opacity: 1, transform: 'translateY(0)' } },
        fadeIn:     { from: { opacity: 0 }, to: { opacity: 1 } },
        scoreFill:  { from: { strokeDashoffset: 440 }, to: { strokeDashoffset: 'var(--target-offset)' } },
        pulseDot:   { '0%,100%': { opacity: 1 }, '50%': { opacity: 0.4 } },
      },
    },
  },
  plugins: [],
}
