import {createWebHistory, createRouter} from 'vue-router'

/* layout 布局组件通常包含侧边栏和顶栏 */
const Layout = () => import('@/layout/index.vue')

// 公共路由
export const constantRoutes = [
    {
        path: '/predict',
        component: () => import('@/views/user/login.vue'),
        hidden: true
    },
    {
        path: '/register',
        component: () => import('@/views/user/register.vue'),
        hidden: true
    },
    {
        path: '/404',
        component: () => import('@/views/error/404.vue'),
        hidden: true
    },
    {
        path: '/401',
        component: () => import('@/views/error/401.vue'),
        hidden: true
    },

    // 业务功能路由
    {
        path: '',
        component: Layout,
        redirect: '/dashboard',
        children: [
            {
                path: 'dashboard',
                component: () => import('@/views/Dashboard.vue'),
                name: 'Dashboard',
                meta: {title: '系统概览', icon: 'dashboard', affix: true}
            }
        ]
    },
    {
        path: '/detection',
        component: Layout,
        children: [
            {
                path: 'index',
                component: () => import('@/views/Detection.vue'),
                name: 'Detection',
                meta: {title: '目标检测识别', icon: 'search'}
            }
        ]
    },
    {
        path: '/evaluation',
        component: Layout,
        children: [
            {
                path: 'index',
                component: () => import('@/views/Evaluation.vue'),
                name: 'evaluation',
                meta: {title: '光谱特征库', icon: 'collection'}
            }
        ]
    },
    {
        path: '/spectral',
        component: Layout,
        children: [
            {
                path: 'library',
                component: () => import('@/views/SpectralLib.vue'),
                name: 'SpectralLib',
                meta: {title: '光谱特征库', icon: 'collection'}
            }
        ]
    },
    {
        path: '/rag',
        component: Layout,
        children: [
            {
                path: 'index',
                component: () => import('@/views/RagChat.vue'),
                name: 'RagChat',
                meta: {title: 'Rag', icon: 'collection'}
            }
        ]
    },
    {
        path: '/reports',
        component: Layout,
        children: [
            {
                path: 'index',
                component: () => import('@/views/Reports.vue'),
                name: 'Reports',
                meta: {title: '检测报告管理', icon: 'document'}
            }
        ]
    },

    // 捕获所有未知路由并重定向到 404
    {
        path: "/:pathMatch(.*)*",
        component: () => import('@/views/error/404.vue'),
        hidden: true
    }
]

const router = createRouter({
    history: createWebHistory(),
    routes: constantRoutes,
    scrollBehavior(to, from, savedPosition) {
        if (savedPosition) {
            return savedPosition
        } else {
            return {top: 0}
        }
    },
})

export default router