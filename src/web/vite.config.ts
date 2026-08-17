import { defineConfig } from 'vitest/config'
import react from '@vitejs/plugin-react'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  server: {
    proxy: {
      '/api': {
        target: process.env.VITE_BACKEND_ORIGIN ?? 'http://localhost:8000',
        changeOrigin: true,
      },
      '/agent-api': {
        target: process.env.VITE_AGENT_ORIGIN ?? 'http://localhost:8002',
        changeOrigin: true,
        rewrite: (path) => path.replace(/^\/agent-api/, '/api'),
      },
      '/ag-ui': {
        target: process.env.VITE_AGENT_ORIGIN ?? 'http://localhost:8002',
        changeOrigin: true,
      },
    },
  },
  test: {
    environment: 'jsdom',
    globals: true,
    setupFiles: ['./src/test/setup.ts'],
    css: true,
    env: {
      // 테스트 전용 절대 URL. jsdom/Node의 fetch는 상대 경로를 resolve할
      // origin이 없고, MSW 2.x도 이 환경에서 상대 경로 핸들러를 안정적으로
      // 매칭하지 못해 절대 URL을 사용한다. `.env.test`(git 커밋 대상이 될
      // 수 있는 dotenv 파일) 대신 여기서 직접 주입해 비밀이 없는 값도
      // `.env.*` 커밋 금지 규칙과 무관하게 관리한다.
      VITE_API_BASE_URL: 'http://localhost/api/v1',
    },
  },
})
