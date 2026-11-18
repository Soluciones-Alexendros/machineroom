import { defineConfig } from "astro/config";
import tailwindcss from "@tailwindcss/vite";

export default defineConfig({
  trailingSlash: "always",
  site: "https://machineroom.alexendros.dev",
  output: "static",
  build: {
    inlineStylesheets: "never",
  },
  vite: {
    plugins: [tailwindcss()],
    build: { cssMinify: true, cssCodeSplit: false },
  },
});
