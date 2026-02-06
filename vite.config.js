import {fileURLToPath, URL} from 'node:url'

// 1. 引入 loadEnv
import {defineConfig, loadEnv} from 'vite'
import vue from '@vitejs/plugin-vue'
import vueDevTools from 'vite-plugin-vue-devtools'

// https://vite.dev/config/
// 2. 将配置改为函数形式，解构出 mode (development/production)
export default defineConfig(({mode}) => {
    // 3. 手动加载环境变量
    // process.cwd() 是项目根目录
    // '' 表示加载所有类型的环境变量 (默认只会加载 VITE_ 开头的，传空字符串可加载所有)
    const env = loadEnv(mode, process.cwd(), '')

    return {
        plugins: [
            vue(),
            vueDevTools(),
        ],
        server: {
            proxy: {
                // 4. 使用加载到的 env 对象来访问变量
                [env.VITE_APP_BASE_API]: {
                    // target: env.VITE_APP_API_URL,
                    target: 'localhost:8080',
                    changeOrigin: true,
                    logLevel: 'debug',
                    // 5. 注意：Vite 的代理配置使用 'rewrite' 函数，而不是 webpack 的 'pathRewrite' 对象
                    rewrite: (path) => path.replace(new RegExp('^' + env.VITE_APP_BASE_API), '')
                }
            }
        },
        resolve: {
            alias: {
                '@': fileURLToPath(new URL('./src', import.meta.url))
            },
        },
    }
})