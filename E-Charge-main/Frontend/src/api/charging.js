import request from '@/utils/request'
// 创建新的充电请求
export const createChargingRequest = (data) => {
  // 标准化充电模式参数
  let chargingMode = 'trickle'
  if (data.chargingMode) {
    // 统一转换为小写再处理
    const mode = data.chargingMode.toLowerCase()
    chargingMode = mode === 'fast' ? 'fast' : 'trickle'
  }
  
  return request({
    url: '/api/charging/requests',
    method: 'post',
    data: {
      vehicle_id: data.vehicleId || 1, // 默认使用ID为1的车辆
      charging_mode: chargingMode,
      requested_amount: data.requestedAmount
    }
  })
}

// 预检查充电请求状态
export const precheckChargingRequest = (data) => {
  // 标准化充电模式参数
  let chargingMode = 'trickle'
  if (data.chargingMode) {
    // 统一转换为小写再处理
    const mode = data.chargingMode.toLowerCase()
    chargingMode = mode === 'fast' ? 'fast' : 'trickle'
  }
  
  return request({
    url: '/api/charging/requests/precheck',
    method: 'post',
    data: {
      vehicle_id: data.vehicleId || 1, // 默认使用ID为1的车辆
      charging_mode: chargingMode,
      requested_amount: data.requestedAmount
    }
  })
}

// 获取用户的充电请求列表
export const getUserRequests = () => {
  return request({
    url: '/api/charging/requests',
    method: 'get'
  })
}

// 获取特定充电请求详情
export const getRequestDetails = (requestId) => {
  return request({
    url: `/api/charging/requests/${requestId}`,
    method: 'get'
  })
}

// 取消充电请求
export const cancelRequest = (requestId) => {
  return request({
    url: `/api/charging/requests/${requestId}/cancel`,
    method: 'post'
  })
}

// 获取排队状态
export const getQueueStatus = () => {
  return request({
    url: '/api/charging/queue/status',
    method: 'get'
  })
}

// 结束充电
export const finishCharging = (requestId) => {
  return request({
    url: `/api/charging/requests/${requestId}/finish`,
    method: 'post'
  })
}

// 获取当前用户的排队状态
export const getCurrentQueueStatus = () => {
  return request({
    url: '/api/charging/queue/status/current',
    method: 'get'
  })
}

// 获取充电桩信息
export const getPiles = () => {
  return request({
    url: '/api/charging/piles',
    method: 'get'
  })
}

// 管理员获取等候车辆信息
export const getWaitingVehicles = () => {
  return request({
    url: '/api/charging/admin/waiting-vehicles',
    method: 'get'
  })
}

// 获取充电通知（检查是否有可用充电桩）
export const getChargingNotification = () => {
  return request({
    url: '/api/charging/user/charging-notification',
    method: 'get'
  })
}

// 开始充电
export const startCharging = (requestId) => {
  return request({
    url: `/api/charging/requests/${requestId}/start-charging`,
    method: 'post'
  })
} 