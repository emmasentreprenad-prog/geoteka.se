import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// Built output is committed into ../trav so it can be served as a static
// subpath of geoteka.se without any build step on the hosting side.
export default defineConfig({
  base: '/trav/',
  plugins: [react()],
  build: {
    outDir: '../trav',
    emptyOutDir: true,
  },
})
