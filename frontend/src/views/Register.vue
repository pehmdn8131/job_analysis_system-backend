<template>
  <div class="login-container"> <div class="login-box">
    <div class="left-bg">
      <h2>新用户注册</h2>
      <p>加入我们，开启数据分析之旅</p>
    </div>
    <div class="right-form">
      <h3>创建账号</h3>
      <el-form :model="form" :rules="rules" ref="formRef">

        <el-form-item prop="username">
          <el-input v-model="form.username" placeholder="请输入用户名" prefix-icon="User" />
        </el-form-item>

        <el-form-item prop="password">
          <el-input
              v-model="form.password"
              type="password"
              placeholder="设置密码"
              prefix-icon="Lock"
              show-password
          />
        </el-form-item>

        <el-form-item prop="confirmPassword">
          <el-input
              v-model="form.confirmPassword"
              type="password"
              placeholder="确认密码"
              prefix-icon="Lock"
              show-password
          />
        </el-form-item>

        <el-button type="success" class="login-btn" @click="handleRegister" :loading="loading">
          立即注册
        </el-button>

        <div class="tips">
          <el-link type="info" @click="$router.push('/login')">已有账号？返回登录</el-link>
        </div>
      </el-form>
    </div>
  </div>
  </div>
</template>

<script setup>
  import {ref, reactive} from "vue"
  import axios  from "axios"
  import { ElMessage } from "element-plus"
  import { useRouter } from "vue-router"

  const router = useRouter()
  const formRef = ref(null)
  const loading = ref(false)

  const form = reactive({
    username: '',
    password: '',
    confirmPassword: ''
  })

  // 验证两次密码是否一致
  const validatePass2 = (rule, value, callback) => {
    if (value === '') {
      callback(new Error('请再次输入密码'))
    } else if (value !== form.password) {
      callback(new Error('两次输入密码不一致!'))
    } else {
      callback()
    }
  }

  const rules = {
    username: [{ required : true, message: '请输入用户名', trigger: 'blur'}],
    password: [{ required : true, message: '请输入密码', trigger: 'blur'}],
    confirmPassword: [{ validator: validatePass2, trigger: 'blur'}],
  }

  const handleRegister = () => {
    formRef.value.validate(async (valid) => {
      if (!valid) return

      loading.value = true
      try {
        // 调用后端注册接口
        const res = await axios.post('http://localhost:5000/api/register',{
          username: form.username,
          password: form.password
        })

        if (res.data.code === 200) {
          ElMessage.success('注册成功！即将跳转登陆...')
          //延迟 1 秒跳转，体验更好
          setTimeout(() => {
            router.push('/login')
          }, 1000)
        } else {
          ElMessage.error(res.data.msg)
        }
      } catch (error) {
        ElMessage.error('注册失败，请检查网络')
      } finally {
        loading.value = false
      }
    })
  }
</script>

<style scoped>
/* 直接复用 Login.vue 的样式，保持风格统一 */
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
  background: #67C23A; /* 注册页换个绿色背景，区别一下 */
  display: flex;
  flex-direction: column;
  justify-content: center;
  padding: 40px;
  color: white;
}
.left-bg h2 { font-size: 32px; margin-bottom: 10px; }
.right-form {
  width: 50%;
  padding: 40px;
  display: flex;
  flex-direction: column;
  justify-content: center;
}
.login-btn { width: 100%; margin-top: 20px; }
.tips { margin-top: 15px; text-align: center; }
</style>














































