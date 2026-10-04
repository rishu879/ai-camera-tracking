import { defineConfig, loadEnv } from 'vite';

export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, process.cwd(), '');
  const host = env.VITE_HOST || '0.0.0.0';
  const port = parseInt(env.VITE_PORT || '5173', 10);
  const apiUrl = env.VITE_API_URL || 'http://127.0.0.1:8000';

  return {
    root: 'client',
    server: {
      host: host,
      port: port,
      strictPort: false,
      cors: true,
      proxy: {
        '/api': {
          target: apiUrl,
          changeOrigin: true,
          ws: true,
        },
      },
    },
    preview: {
      host: host,
      port: port,
      proxy: {
        '/api': {
          target: apiUrl,
          changeOrigin: true,
        },
      },
    },
    build: {
      outDir: '../dist',
      emptyOutDir: true,
    },
  };
});
