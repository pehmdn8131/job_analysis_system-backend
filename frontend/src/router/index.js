import { createRouter, createWebHistory } from 'vue-router'

const Login = () => import('../views/Login.vue')
const Register = () => import('../views/Register.vue')
// 引入布局和页面
const Layout = () => import('../layout/Layout.vue')
const Dashboard = () => import('../views/Dashboard.vue')

const routes = [
    { path: '/', redirect: '/login' },
    { path: '/login', name: 'Login', component: Login },
    { path: '/register', name: 'Register', component: Register },

    // 主布局路由
    {
        path: '/dashboard',
        component: Layout, // 先加载 Layout 框架
        redirect: '/dashboard/index',
        children: [
            {
                path: '', // 默认子路由
                name: 'Dashboard',
                component: Dashboard // 再把 Dashboard 塞进 Layout 的中间
            }
        ]
    },
    // 预留给明天的推荐页路由
    {
        path: '/recommend',
        component: Layout,
        children: [
            {
                path: '',
                component: () => import('../views/Recommend.vue') // 明天再创建这个文件
            }
        ]
    }
]

const router = createRouter({
    history: createWebHistory(),
    routes
})

// 【路由守卫】防止没登录直接输入网址访问后台
router.beforeEach((to, from, next) => {
    const token = localStorage.getItem('token')
    // 如果要去非登录页，且没有 token，强制踢回登录页
    if (to.path !== '/login' && to.path !== '/register' && !token) {
        next('/login')
    } else {
        next()
    }
})

export default router