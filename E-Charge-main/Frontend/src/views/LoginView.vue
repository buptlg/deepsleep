<template>
  <div class="login-container">
    <div class="login-card">
      <h1 class="title">充电站管理系统</h1>
      
      <!-- 登录成功提示 -->
      <div v-if="loginSuccess" class="success-message">
        登录成功！正在跳转...
      </div>
      
      <div v-if="!loginSuccess">
        <div class="form-group">
          <label for="username">用户名</label>
          <input 
            id="username" 
            v-model="username" 
            type="text" 
            placeholder="请输入用户名"
            @keyup.enter="handleLogin"
          />
        </div>
        <div class="form-group">
          <label for="password">密码</label>
          <input 
            id="password" 
            v-model="password" 
            type="password" 
            placeholder="请输入密码"
            @keyup.enter="handleLogin"
          />
        </div>
        <div class="user-type">
          <label>
            <input 
              type="radio" 
              v-model="userType" 
              value="user" 
              name="userType"
            /> 用户
          </label>
          <label>
            <input 
              type="radio" 
              v-model="userType" 
              value="admin" 
              name="userType"
            /> 管理员
          </label>
        </div>
        <div class="button-group">
          <button 
            class="login-button" 
            @click="handleLogin" 
            :disabled="isLoading"
          >
            {{ isLoading ? '登录中...' : '登录' }}
          </button>
          <button 
            class="register-button" 
            @click="goToRegister" 
            :disabled="isLoading"
          >
            注册账号
          </button>
        </div>
        <div v-if="errorMessage" class="error-message">
          {{ errorMessage }}
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { login } from '@/api/auth'

const router = useRouter()
const username = ref('')
const password = ref('')
const userType = ref('user') // 默认为普通用户
const isLoading = ref(false)
const errorMessage = ref('')
const loginSuccess = ref(false)

const handleLogin = async () => {
  if (!username.value || !password.value) {
    errorMessage.value = '请输入用户名和密码'
    return
  }
  
  try {
    isLoading.value = true
    errorMessage.value = ''
    
    console.log('开始登录，正在发送请求...')
    console.log('用户名:', username.value)
    console.log('用户类型:', userType.value)
    
    // 调用实际登录API
    const response = await login({
      username: username.value,
      password: password.value
    })
    
    console.log('登录API响应:', response)
    
    // 保存token
    if (response && response.access_token) {
      localStorage.setItem('token', response.access_token)
      console.log('保存token成功')
      
      try {
        // 获取用户信息并判断用户类型
        console.log('正在获取用户信息...')
        const userInfo = await getUserInfo()
        console.log('用户信息:', userInfo)
        
        // 检查用户类型是否匹配
        if (userType.value === 'admin' && !userInfo.is_admin) {
          errorMessage.value = '您没有管理员权限'
          return
        }
        
        // 保存用户信息到 localStorage
        localStorage.setItem('currentUser', JSON.stringify({
          username: userInfo.username,
          id: userInfo.id,
          type: userInfo.is_admin ? 'admin' : 'user'
        }))
        
        // 显示登录成功提示
        loginSuccess.value = true
        
        // 延迟跳转，让用户能看到成功提示
        setTimeout(() => {
          // 检查是否有重定向URL
          const redirectUrl = localStorage.getItem('redirectUrl')
          
          if (redirectUrl) {
            console.log('跳转到重定向页面:', redirectUrl)
            localStorage.removeItem('redirectUrl')
            router.push(redirectUrl)
          } else {
          if (userType.value === 'admin') {
            console.log('跳转到管理员页面')
            router.push('/admin-dashboard')
          } else {
            console.log('跳转到用户页面')
            router.push('/user-dashboard')
            }
          }
        }, 1500)
        
      } catch (userInfoError) {
        console.error('获取用户信息失败:', userInfoError)
        errorMessage.value = '获取用户信息失败: ' + (userInfoError.message || '未知错误')
      }
    } else {
      console.error('登录响应中没有token:', response)
      errorMessage.value = '登录失败: 无效的响应'
    }
  } catch (error) {
    console.error('登录错误:', error)
    if (error.response) {
      console.error('错误响应:', error.response.data)
      // 根据后端的详细错误信息显示不同的错误提示
      if (error.response.data?.detail === '账户不存在') {
        errorMessage.value = '无该用户(・ω・、) '
      } else if (error.response.data?.detail === '密码错误') {
        errorMessage.value = '哎呀密码输错了,再试试吧 ( ￣ 3￣)'
      } else {
        errorMessage.value = `登录失败: ${error.response.data?.detail || '请检查用户名和密码'}`
      }
    } else if (error.request) {
      console.error('无响应:', error.request)
      errorMessage.value = '登录失败: 服务器无响应'
    } else {
      console.error('请求错误:', error.message)
      errorMessage.value = '登录失败: ' + error.message
    }
  } finally {
    isLoading.value = false
  }
}

const goToRegister = () => {
  router.push('/register')
}

// 获取用户信息
const getUserInfo = async () => {
  try {
    console.log('发送获取用户信息请求...')
    console.log('使用token:', localStorage.getItem('token'))
    
    const response = await fetch('http://localhost:8000/api/users/me', {
      headers: {
        'Authorization': `Bearer ${localStorage.getItem('token')}`
      }
    })
    
    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}))
      console.error('获取用户信息失败:', response.status, errorData)
      throw new Error(`获取用户信息错误: ${response.status} ${JSON.stringify(errorData)}`)
    }
    
    return await response.json()
  } catch (error) {
    console.error('获取用户信息错误:', error)
    throw error
  }
}
</script>

<style scoped>
.login-container {
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: 100vh;
}

.login-card {
  width: 380px;
  padding: 40px;
  background-color: white;
  border-radius: 12px;
  box-shadow: 0 8px 30px rgba(0, 0, 0, 0.15);
  animation: fadeIn 0.5s ease-out;
  position: relative;
  z-index: 10;
  overflow: hidden;
  margin: 20px;
}

.login-card::before {
  content: "";
  position: absolute;
  top: -50px;
  right: -50px;
  width: 100px;
  height: 100px;
  background-color: rgba(76, 175, 80, 0.1);
  border-radius: 50%;
  z-index: -1;
}

.login-card::after {
  content: "";
  position: absolute;
  bottom: -50px;
  left: -50px;
  width: 150px;
  height: 150px;
  background-color: rgba(76, 175, 80, 0.1);
  border-radius: 50%;
  z-index: -1;
}

.success-message {
  text-align: center;
  font-size: 18px;
  color: #4caf50;
  font-weight: 500;
  background-color: rgba(76, 175, 80, 0.1);
  padding: 20px;
  border-radius: 8px;
  margin-bottom: 10px;
  animation: pulse 1.5s infinite;
}

@keyframes pulse {
  0% { opacity: 0.8; }
  50% { opacity: 1; }
  100% { opacity: 0.8; }
}

@keyframes fadeIn {
  from {
    opacity: 0;
    transform: translateY(20px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.title {
  text-align: center;
  margin-bottom: 30px;
  color: #333;
  font-size: 26px;
  font-weight: 600;
  position: relative;
  padding-bottom: 15px;
}

.title::after {
  content: "";
  position: absolute;
  bottom: 0;
  left: 50%;
  transform: translateX(-50%);
  width: 50px;
  height: 3px;
  background-color: var(--primary-color);
  border-radius: 3px;
}

.form-group {
  margin-bottom: 22px;
  position: relative;
}

label {
  display: block;
  margin-bottom: 8px;
  font-size: 14px;
  color: var(--light-text);
  font-weight: 500;
  transition: color 0.3s;
}

.form-group:focus-within label {
  color: var(--primary-color);
}

input[type="text"],
input[type="password"] {
  width: 100%;
  padding: 12px 16px;
  border: 1px solid var(--border-color);
  border-radius: 8px;
  font-size: 15px;
  transition: all 0.3s;
  background-color: #f9f9f9;
}

input[type="text"]:focus,
input[type="password"]:focus {
  border-color: var(--primary-color);
  outline: none;
  background-color: white;
  box-shadow: 0 0 0 3px rgba(76, 175, 80, 0.1);
}

.user-type {
  display: flex;
  gap: 30px;
  margin-bottom: 25px;
  justify-content: center;
}

.user-type label {
  display: flex;
  align-items: center;
  cursor: pointer;
  font-size: 15px;
  font-weight: 500;
  color: var(--text-color);
}

.user-type input {
  margin-right: 8px;
  cursor: pointer;
  accent-color: var(--primary-color);
  width: 18px;
  height: 18px;
}

.button-group {
  display: flex;
  gap: 15px;
  margin-top: 10px;
}

.login-button,
.register-button {
  padding: 14px 0;
  border: none;
  border-radius: 8px;
  font-size: 15px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.3s;
  flex: 1;
  letter-spacing: 0.5px;
}

.login-button {
  background-color: var(--primary-color);
  color: white;
  position: relative;
  overflow: hidden;
}

.login-button::after {
  content: "";
  position: absolute;
  top: 0;
  left: -100%;
  width: 100%;
  height: 100%;
  background: linear-gradient(
    90deg,
    rgba(255, 255, 255, 0) 0%,
    rgba(255, 255, 255, 0.2) 50%,
    rgba(255, 255, 255, 0) 100%
  );
  transition: all 0.3s;
}

.login-button:hover::after {
  left: 100%;
}

.login-button:hover {
  background-color: var(--primary-dark);
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
}

.register-button {
  background-color: #f5f5f5;
  color: #555;
  border: 1px solid #ddd;
}

.register-button:hover {
  background-color: #e8e8e8;
  transform: translateY(-2px);
}

button:disabled {
  opacity: 0.7;
  cursor: not-allowed;
  transform: none !important;
  box-shadow: none !important;
}

.error-message {
  margin-top: 20px;
  color: var(--error-color);
  text-align: center;
  font-size: 14px;
  font-weight: 500;
  padding: 10px;
  background-color: rgba(244, 67, 54, 0.1);
  border-radius: 6px;
  animation: shake 0.5s linear;
}

@keyframes shake {
  0%, 100% { transform: translateX(0); }
  20%, 60% { transform: translateX(-5px); }
  40%, 80% { transform: translateX(5px); }
}

@media (max-width: 480px) {
  .login-card {
    width: 90%;
    padding: 30px 20px;
  }
  
  .button-group {
    flex-direction: column;
  }
}
</style> 