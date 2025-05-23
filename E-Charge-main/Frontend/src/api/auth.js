import request from '@/utils/request'

export const login = (data) => {
  const formData = new FormData()
  formData.append('username', data.username)
  formData.append('password', data.password)
  
  return request({
    url: '/api/token',
    method: 'post',
    data: formData,
    headers: {
      'Content-Type': 'multipart/form-data'
    }
  })
}

export const register = (data) => {
  return request({
    url: '/api/users/register',
    method: 'post',
    data
  })
}

export const getUserInfo = () => {
  return request({
    url: '/api/users/me',
    method: 'get'
  })
} 