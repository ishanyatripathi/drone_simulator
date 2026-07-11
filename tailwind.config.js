/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{ts,tsx}'],
  theme: {
    extend: {
      colors: {
        aeris: {
          bg: '#05070C',
          panel: '#0B1018',
          border: 'rgba(148, 197, 227, 0.12)',
          cyan: '#00D9FF',
          cyanDim: '#0891A8',
          amber: '#FFB020',
          red: '#FF3B3B',
          green: '#00FF9C',
          text: '#DCE8F0',
          textDim: '#6B8299',
        },
      },
      fontFamily: {
        display: ['"Rajdhani"', 'sans-serif'],
        body: ['"Inter"', 'sans-serif'],
        mono: ['"JetBrains Mono"', 'monospace'],
      },
      backdropBlur: {
        xs: '2px',
      },
      boxShadow: {
        glow: '0 0 20px rgba(0, 217, 255, 0.35)',
        glowAmber: '0 0 20px rgba(255, 176, 32, 0.35)',
        glowRed: '0 0 20px rgba(255, 59, 59, 0.45)',
      },
      animation: {
        'pulse-slow': 'pulse 3s cubic-bezier(0.4, 0, 0.6, 1) infinite',
        scan: 'scan 3s linear infinite',
      },
      keyframes: {
        scan: {
          '0%': { transform: 'translateY(-100%)' },
          '100%': { transform: 'translateY(100%)' },
        },
      },
    },
  },
  plugins: [],
};
