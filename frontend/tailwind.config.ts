import type { Config } from 'tailwindcss'

export default {
  content: ['./index.html', './src/**/*.{vue,ts,tsx}'],
  theme: {
    extend: {
      colors: {
        surface: '#0f172a',
        panel: '#111827',
        panelMuted: '#1f2937',
        line: '#243041',
        brand: '#22c55e',
        brandSoft: '#163522',
        danger: '#ef4444',
        warning: '#f59e0b',
        info: '#38bdf8',
      },
      boxShadow: {
        panel: '0 12px 36px rgba(2, 6, 23, 0.25)',
      },
    },
  },
  plugins: [],
} satisfies Config

