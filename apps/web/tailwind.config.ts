import type { Config } from 'tailwindcss';

const config: Config = {
  content: ['./src/**/*.{ts,tsx}'],
  theme: {
    extend: {
      colors: {
        ink: '#17201c',
        paper: '#f7f5ef',
        mint: '#cfe7dc',
        moss: '#49695b',
        rust: '#a7583d',
        gold: '#d7a744',
        graphite: '#2d3035',
      },
      boxShadow: {
        soft: '0 16px 45px rgba(23, 32, 28, 0.12)',
      },
    },
  },
  plugins: [],
};

export default config;
