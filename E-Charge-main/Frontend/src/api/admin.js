import request from '@/utils/request'

// 获取管理员仪表盘统计数据
export const getAdminStatistics = () => {
  return request({
    url: '/api/admin/statistics',
    method: 'get'
  })
}

// 获取充电桩管理数据
export const getChargingPiles = () => {
  return request({
    url: '/api/admin/piles',
    method: 'get'
  })
}

// 获取充电桩详细信息
export const getPileDetails = (pileId) => {
  return request({
    url: `/api/admin/piles/${pileId}`,
    method: 'get'
  })
}

// 获取充电桩队列信息
export const getPileQueue = (pileId) => {
  return request({
    url: `/api/admin/piles/${pileId}/queue`,
    method: 'get'
  })
}

// 获取等候区等待车辆信息
export const getWaitingArea = () => {
  return request({
    url: '/api/admin/waiting-area',
    method: 'get'
  })
}

// 获取所有等待车辆信息（包括充电中和等待中的车辆）
export const getWaitingVehicles = () => {
  return request({
    url: '/api/charging/admin/waiting-vehicles',
    method: 'get'
  })
}

// 切换充电桩状态
export const togglePileStatus = (pileId) => {
  return request({
    url: `/api/admin/piles/${pileId}/toggle`,
    method: 'post'
  })
}

// 更新充电桩状态
export const updatePileStatus = (pileId, status) => {
  return request({
    url: `/api/admin/piles/${pileId}/status`,
    method: 'put',
    data: { status }
  })
}

// 启动充电桩
export const startChargingPile = (pileId) => {
  return request({
    url: `/api/admin/piles/${pileId}/start`,
    method: 'post'
  })
}

// 获取报表数据
export const getReportData = (params) => {
  return request({
    url: '/api/admin/reports',
    method: 'get',
    params
  })
}

export default {
  getAdminStatistics,
  getChargingPiles,
  getPileDetails,
  getPileQueue,
  getWaitingArea,
  getWaitingVehicles,
  togglePileStatus,
  updatePileStatus,
  startChargingPile,
  getReportData
} 