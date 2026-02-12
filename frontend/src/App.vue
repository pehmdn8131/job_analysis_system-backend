<template>
  <router-view />

  <transition name="slide-up">
    <div v-if="spiderStatus.is_running || showResult" class="global-spider-monitor">
      <div class="monitor-content">
        <div class="status-left">
          <el-icon v-if="spiderStatus.is_running" class="spinner is-loading"><Loading /></el-icon>
          <el-icon v-else class="success-icon"><CircleCheckFilled /></el-icon>
          <span class="status-title">
            {{ spiderStatus.is_running ? '数据采集引擎运行中...' : '采集任务已完成' }}
          </span>
        </div>

        <div class="status-center">
          <span class="log-text">{{ spiderStatus.log }}</span>
        </div>

        <div class="status-right">
          <span class="count-badge">已入库: {{ spiderStatus.total_added }}</span>
          <el-icon v-if="!spiderStatus.is_running" class="close-btn" @click="closeMonitor"><Close /></el-icon>
        </div>
      </div>
    </div>
  </transition>
</template>

<script setup>
import { ref, reactive, onMounted, onUnmounted } from 'vue'
import axios from 'axios'
import { Loading, CircleCheckFilled, Close } from '@element-plus/icons-vue'

// 全局状态定义
const spiderStatus = reactive({
  is_running: false,
  total_added: 0,
  log: '',
})
const showResult = ref(false)
let timer = null

const closeMonitor = () => {
  showResult.value = false
}

// 全局轮询器：每秒检查一次后端状态
const checkStatus = async () => {
  try {
    const res = await axios.get('http://127.0.0.1:5000/api/spider/status')
    if (res.data.code === 200) {
      const newData = res.data.data

      // 如果正在运行，强制显示
      if (newData.is_running) {
        showResult.value = true
      }

      // 状态同步
      spiderStatus.is_running = newData.is_running
      spiderStatus.total_added = newData.total_added
      spiderStatus.log = newData.log

      // 如果任务刚结束且面板还开着，保持显示直到用户关闭(或你可以加个定时关闭)
    }
  } catch (e) {
    // 忽略网络错误，避免控制台刷屏
  }
}

onMounted(() => {
  // 启动全局心跳
  timer = setInterval(checkStatus, 1000)
})

onUnmounted(() => {
  if (timer) clearInterval(timer)
})
</script>

<style scoped>
/* ==========================================
   全局悬浮窗样式 (深色磨砂风格)
   ========================================== */
.global-spider-monitor {
  position: fixed;
  bottom: 30px;
  left: calc(50% + 110px);

  transform: translateX(-50%);
  z-index: 9999;
  display: flex;
  justify-content: center;
  pointer-events: none;
}

.monitor-content {
  background: rgba(30, 30, 30, 0.9); /* 深色背景 */
  backdrop-filter: blur(10px);        /* 磨砂效果 */
  color: #fff;
  padding: 12px 25px;
  border-radius: 50px;
  box-shadow: 0 10px 30px rgba(0,0,0,0.3);
  display: flex;
  align-items: center;
  gap: 20px;
  min-width: 450px;
  max-width: 800px;
  pointer-events: auto; /* 内容区域可点击 */
  border: 1px solid rgba(255,255,255,0.1);
}

/* 左侧 */
.status-left {
  display: flex;
  align-items: center;
  gap: 10px;
  font-weight: bold;
  color: #409eff;
  white-space: nowrap;
}

.spinner {
  font-size: 18px;
  animation: spin 1s linear infinite;
}
.success-icon {
  font-size: 18px;
  color: #67C23A;
}

/* 中间日志 */
.status-center {
  flex: 1;
  text-align: center;
  font-size: 13px;
  color: #ddd;
  overflow: hidden;
  white-space: nowrap;
  text-overflow: ellipsis;
  max-width: 400px;
}

/* 右侧数据 */
.status-right {
  display: flex;
  align-items: center;
  gap: 10px;
}

.count-badge {
  background: #67c23a;
  color: white;
  padding: 2px 10px;
  border-radius: 12px;
  font-size: 12px;
  font-weight: bold;
  white-space: nowrap;
}

.close-btn {
  cursor: pointer;
  margin-left: 5px;
  font-size: 16px;
  color: #909399;
  transition: color 0.3s;
}
.close-btn:hover { color: #f56c6c; }

/* 动画定义 */
@keyframes spin {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}

.slide-up-enter-active,
.slide-up-leave-active {
  transition: all 0.4s cubic-bezier(0.16, 1, 0.3, 1);
}

.slide-up-enter-from,
.slide-up-leave-to {
  transform: translate(-50%, 80px); /* 向下位移隐藏 */
  opacity: 0;
}
</style>