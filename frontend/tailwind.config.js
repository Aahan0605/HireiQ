/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  darkMode: 'class', // toggle via <html class="dark">
  theme: {
    extend: {
      colors: {
        // Dark mode surfaces
        bg:          '#07070E',
        surface:     '#0D0D1A',
        'surface-2': '#141428',
        'surface-3': '#1C1C35',
        border:      'rgba(255,255,255,0.07)',
        'border-glow':'rgba(255,255,255,0.15)',

        // Accent — switched from violet/purple to emerald/green
        mint:   '#4DFFA4',   // bright green highlight
        violet: '#10b981',   // emerald — replaces purple as primary accent
        rose:   '#FF6B8A',
        amber:  '#FFB347',
        sky:    '#5DB8FF',

        // Dark text
        'text-1': '#EEEEF5',
        'text-2': '#9494B0',
        'text-3': '#4A4A6E',
      },
      fontFamily: {
        sans:    ['"Instrument Sans"', 'sans-serif'],
        display: ['"Bricolage Grotesque"', 'sans-serif'],
        mono:    ['"Geist Mono"', 'monospace'],
      },
      boxShadow: {
        'glow-mint':   '0 0 24px rgba(77, 255, 164, 0.35)',
        'glow-violet': '0 0 60px rgba(16, 185, 129, 0.25)',  // emerald glow
        'glow-rose':   '0 0 24px rgba(255, 107, 138, 0.35)',
      },
      borderRadius: { inherit: 'inherit' },
      keyframes: {
        grain: {
          '0%, 100%': { transform: 'translate(0, 0)' },
          '10%': { transform: 'translate(-2%, -3%)' },
          '20%': { transform: 'translate(3%, 1%)' },
          '30%': { transform: 'translate(-1%, 3%)' },
          '40%': { transform: 'translate(2%, -2%)' },
          '50%': { transform: 'translate(-3%, 2%)' },
          '60%': { transform: 'translate(1%, -1%)' },
          '70%': { transform: 'translate(-2%, 3%)' },
          '80%': { transform: 'translate(3%, -3%)' },
          '90%': { transform: 'translate(-1%, 1%)' },
        },
        float:     { '0%, 100%': { transform: 'translateY(0)' }, '50%': { transform: 'translateY(-20px)' } },
        floatSlow: { '0%, 100%': { transform: 'translateY(0)' }, '50%': { transform: 'translateY(20px)' } },
        shimmer:   { '100%': { backgroundPosition: '-200% center' } },
        pulseGlow: { '0%, 100%': { opacity: 1, filter: 'brightness(1)' }, '50%': { opacity: 0.7, filter: 'brightness(1.5)' } },
        fadeUp:    { '0%': { opacity: 0, transform: 'translateY(28px)' }, '100%': { opacity: 1, transform: 'translateY(0)' } },
        scaleIn:   { '0%': { opacity: 0, transform: 'scale(0.95)' }, '100%': { opacity: 1, transform: 'scale(1)' } },
        blink:     { '0%, 100%': { opacity: 1 }, '50%': { opacity: 0 } },
      },
      animation: {
        grain:          'grain 7s steps(8) infinite',
        float:          'float 6s ease-in-out infinite',
        floatSlow:      'floatSlow 9s ease-in-out infinite reverse',
        'shimmer-text': 'shimmer 2s linear infinite',
        pulseGlow:      'pulseGlow 2s ease-in-out infinite',
        fadeUp:         'fadeUp 0.6s cubic-bezier(0.16, 1, 0.3, 1) forwards',
        scaleIn:        'scaleIn 0.5s cubic-bezier(0.16, 1, 0.3, 1) forwards',
        blink:          'blink 1s step-end infinite',
      },
    },
  },
  plugins: [],
}
