import react from '@vitejs/plugin-react'
import { defineConfig } from 'vite' 

export default defineConfig({
  plugins:[react()],

  server: {
    proxy: {
      '/api': {
        //send API requests to the running FastAPI server.
        target: 'http://127.0.0.1:8000',
      
        //Remove /api because the backend routes don't include that prefix.
        rewrite: (path) => path.replace( /^\/api/, ''),
      },
    },
  }, 
})