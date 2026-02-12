import { createApp } from 'vue'
// 引入 Element Plus 样式
import ElementPlus from "element-plus";
import 'element-plus/dist/index.css'
// 引入图标
import * as ElementPlusIconsVue from '@element-plus/icons-vue'
// 引入路由
import router from  './router'
import App from "./App.vue";

const app = createApp(App)

// 注册所有图标
for (const [key, component] of Object.entries(ElementPlusIconsVue)){
    app.component(key, component)
}

app.use(ElementPlus)
app.use(router)
app.mount('#app')


