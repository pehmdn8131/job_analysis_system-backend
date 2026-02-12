<template>
  <div class="login-container">
    <div class="login-box">
      <div class="left-bg">
        <h2>招聘数据<br>分析系统</h2>
        <p>基于 Python + Vue 的全栈实践</p>
      </div>
      <div class="right-from">
        <h3>欢迎登录</h3>
        <el-form :model="form" :rules ref="formRef">

          <el-form-item prop="username">
            <el-input v-model="form.username" placeholder="请输入用户名" prefix-icon="User" />
          </el-form-item>

          <el-form-item prop="password">
            <el-input
                v-model="form.password"
                type="password"
                placeholder="请输入密码"
                prefix-icon="Lock"
                show-password
            />
          </el-form-item>

          <el-button type="primary" class="login-btn" @click="handleLogin" :loading="loading">
            立即登陆
          </el-button>

          <div class="tips">
            <el-link type="primary" @click="$router.push('/register')">没有账号？点此注册</el-link>
          </div>
        </el-form>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive } from 'vue'
import axios from "axios"
import { ElMessage } from 'element-plus'
import { useRouter } from 'vue-router'

const router = useRouter()
const formRef = ref(null)
const loading = ref(false)

const form = reactive({
  username: '',
  password: ''
})

const rules = {
  username: [{ required: true, message: '请输入用户名', trigger: 'blur' }],
  password: [{ required: true, message: '请输入密码', trigger: 'blur'}]
}

// 登陆逻辑
const handleLogin = () => {
  formRef.value.validate(async (valid) => {
    if (!valid) return

    loading.value = true
    try {
      // 发送请求给后端 (Flask)
      const res = await axios.post('http://localhost:5000/api/login', form)

      if (res.data.code === 200){
        ElMessage.success('登陆成功！')
        // 把 Token 存起来，以后要用
        localStorage.setItem('token', res.data.token)
        localStorage.setItem('username', res.data.username)

        //跳转主页
        await router.push('/dashboard')
      } else {
        ElMessage.error(res.data.msg)
      }
    } catch (error) {
      ElMessage.error('服务器连接失败，请检查后端是否启动')
    }finally {
      loading.value = false
    }
  })
}

</script>

<style scoped>
.login-container {
  height: 100vh;
  display: flex;
  justify-content: center;
  align-items: center;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
}
.login-box {
  width: 800px;
  height: 400px;
  background: white;
  border-radius: 12px;
  box-shadow: 0 10px 30px rgba(0,0,0,0.2);
  display: flex;
  overflow: hidden;
}
.left-bg {
  width: 50%;
  background: #409eff;
  display: flex;
  flex-direction: column;
  justify-content: center;
  padding: 40px;
  color: white;
}
.left-bg h2 { font-size: 32px; margin-bottom: 10px }
.right-from{
  width: 50%;
  padding: 40px;
  display: flex;
  flex-direction: column;
  justify-content: center;
}
.login-btn { width: 100%; margin-top: 20px}
.tips { margin-top: 15px; text-align: center}

</style>










































