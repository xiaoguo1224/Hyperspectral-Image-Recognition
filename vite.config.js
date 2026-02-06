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
                [env.VITE_APP_BASE_API]: {
                    target: env.VITE_APP_API_URL,
                    changeOrigin: true,
                    // 路径重写
                    rewrite: (path) => path.replace(new RegExp('^' + env.VITE_APP_BASE_API), ''),

                    // === 核心调试代码：打印代理日志 ===
                    configure: (proxy, options) => {
                        // 1. 监听代理发出的请求 (Proxy Request)
                        proxy.on('proxyReq', (proxyReq, req, res) => {
                            // 获取完整的重写后的 URL
                            const realUrl = options.target + proxyReq.path;

                            console.log('\n--------- 代理请求调试 ---------');
                            console.log(`1. 前端请求: ${req.url}`);
                            console.log(`2. 代理转发: ${realUrl}`);
                            console.log(`3. 请求方法: ${req.method}`);
                            // 如果想看 Header，可以解开下面这行
                            // console.log('Header:', proxyReq.getHeaders());
                        });

                        // 2. 监听代理收到的响应 (Proxy Response)
                        proxy.on('proxyRes', (proxyRes, req, res) => {
                            console.log(`4. 后端响应: Status ${proxyRes.statusCode}`);
                            console.log('------------------------------\n');
                        });

                        // 3. 监听代理错误
                        proxy.on('error', (err, req, res) => {
                            console.error('!!! 代理发生错误 !!!', err);
                        });
                    }
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