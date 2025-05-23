import axios from 'axios'
import { ElMessage } from 'element-plus'
import router from '@/router'

// 创建axios实例
const service = axios.create({
  baseURL: '',  // 使用相对URL，依赖于浏览器的当前路径
  timeout: 10000
})

// 请求拦截器
service.interceptors.request.use(
  config => {
    console.log('发送请求:', config.url, config.method, config.data)
    const token = localStorage.getItem('token')
    if (token) {
      config.headers['Authorization'] = `Bearer ${token}`
    }
    return config
  },
  error => {
    console.error('请求配置错误:', error)
    return Promise.reject(error)
  }
)

// 响应拦截器
service.interceptors.response.use(
  response => {
    console.log('收到响应:', response.config.url, response.status, response.data)
    return response.data
  },
  error => {
    console.error('请求错误:', error)
    if (error.response) {
      console.error('错误响应:', error.response.status, error.response.data)
      switch (error.response.status) {
        case 401:
          // token过期或无效
          console.error('401: 未授权')
          localStorage.removeItem('token')
          router.push('/login')
          break
        case 403:
          console.error('403: 禁止访问')
          break
        case 404:
          console.error('404: 资源不存在')
          break
        case 422:
          console.error('422: 数据验证失败', error.response.data)
          if (error.response.data?.detail) {
            if (Array.isArray(error.response.data.detail)) {
              error.response.data.detail.forEach(item => {
                console.error(`字段 ${item.loc.join('.')} 错误: ${item.msg}`)
              })
            } else {
              console.error(error.response.data.detail)
            }
          }
          break
        case 500:
          console.error('500: 服务器错误')
          break
        default:
          console.error(`${error.response.status}: 未知错误`)
      }
    } else if (error.request) {
      // 请求已发送但没有收到响应
      console.error('网络错误, 未收到响应:', error.request)
    } else {
      // 请求配置时发生错误
      console.error('请求错误:', error.message)
    }
    
    return Promise.reject(error)
  }
)

export default service 