import { defineConfig } from 'vite';

export default defineConfig({
  base: './',
  publicDir: 'exports/weapons',
  build: { outDir: 'dist' },
});
