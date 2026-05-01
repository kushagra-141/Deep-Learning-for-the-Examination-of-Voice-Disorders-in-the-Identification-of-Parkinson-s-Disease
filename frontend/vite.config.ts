import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import path from "path";

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [react()],

  resolve: {
    alias: {
      "@": path.resolve(__dirname, "./src"),
    },
  },

  server: {
    port: 5173,
    proxy: {
      "/api": {
        target: "http://localhost:8000",
        changeOrigin: true,
      },
    },
  },

  build: {
    // Performance budget: initial bundle ≤ 250 KB gzipped (from 00_MASTER_PLAN.md §0.5)
    rollupOptions: {
      output: {
        manualChunks: {
          // Vendor chunk splitting to keep initial bundle small
          "vendor-react": ["react", "react-dom", "react-router-dom"],
          "vendor-query": ["@tanstack/react-query"],
          "vendor-radix": [
            "@radix-ui/react-dialog",
            "@radix-ui/react-tabs",
            "@radix-ui/react-tooltip",
            "@radix-ui/react-select",
          ],
          "vendor-charts": ["recharts"],
        },
      },
    },
    sourcemap: true,
  },

  // Test configuration (Vitest reads from vite.config.ts)
  test: {
    globals: true,
    environment: "jsdom",
    setupFiles: ["./src/test-setup.ts"],
    coverage: {
      reporter: ["text", "json", "html"],
    },
  },
} as Parameters<typeof defineConfig>[0]);
