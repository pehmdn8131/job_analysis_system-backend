<template>
  <div class="common-layout">
    <el-container class="layout-container">

      <!-- 左侧栏 -->
      <el-aside width="200px" class="aside">
        <div class="logo">
          <el-icon><DataLine /></el-icon>
          <span>招聘分析系统</span>
        </div>

        <el-menu
            router
            default-active="/dashboard"
            background-color="#304156"
            text-color="#fff"
            active-text-color="#ffd04b"
        >
          <el-menu-item index="/dashboard">
            <el-icon><Odometer /></el-icon>
            <span>数据大屏</span>
          </el-menu-item>

          <el-menu-item index="/recommend">
            <el-icon><Star /></el-icon>
            <span>职位推荐</span>
          </el-menu-item>
        </el-menu>
      </el-aside>

      <!-- 右侧整体 -->
      <el-container>

        <!-- 顶部 -->
        <el-header class="header">
          <div>欢迎回来，{{ username }}</div>
          <el-button type="danger" size="small" @click="handleLogout">
            退出登录
          </el-button>
        </el-header>

        <!-- 主体 -->
        <el-main class="main-content">
          <router-view />
        </el-main>

      </el-container>
    </el-container>
  </div>
</template>

<script setup>
import { DataLine, Odometer, Star } from "@element-plus/icons-vue"
import { useRouter } from "vue-router"
import { ElMessage } from "element-plus"
import { ref } from "vue"

const router = useRouter()
const username = ref(localStorage.getItem("username") || "同学")

const handleLogout = () => {
  localStorage.clear()
  ElMessage.success("已安全退出")
  router.push("/login")
}
</script>

<style scoped>
.layout-container { height: 100vh; }
.aside { background-color: #304156; color: white; }
.logo {
  height: 60px;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 10px;
  font-size: 18px;
  font-weight: bold;
  background-color: #2b3649;
}
.header {
  background: #fff;
  border-bottom: 1px solid #dcdfe6;
  display: flex;
  justify-content: space-between;
  align-items: center;
}
.main-content {
  background-color: #f0f2f5;
  padding: 20px;
}
</style>
