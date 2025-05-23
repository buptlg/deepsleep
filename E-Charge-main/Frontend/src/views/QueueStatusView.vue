<template>
  <div class="queue-status-container">
    <div class="page-header">
      <h1>排队状态</h1>
      <button class="back-btn" @click="goBack">返回</button>
    </div>

    <div v-if="loading" class="loading-container">
      <div class="loading-spinner"></div>
      <p>加载中...</p>
    </div>

    <div v-else-if="!hasRequest" class="no-data-container">
      <div class="no-data-icon">📋</div>
      <h3>暂无充电请求</h3>
      <p>您还没有提交充电请求，请先提交充电请求。</p>
      <button class="primary-btn" @click="navigateToRequest">提交充电请求</button>
    </div>

    <div v-else class="status-cards">
      <div class="queue-card">
        <div class="card-header">
          <h2>排队信息</h2>
          <div class="refresh-btn" @click="refreshData">
            <span class="refresh-icon">🔄</span>
            <span>刷新</span>
          </div>
        </div>
        
        <div class="status-section">
          <div class="status-item">
            <div class="status-label">充电模式</div>
            <div class="status-value">{{ chargeMode === 'fast' ? '快充模式' : '慢充模式' }}</div>
          </div>
          
          <div class="status-item">
            <div class="status-label">排队号码</div>
            <div class="status-value highlight">{{ queueNumber }}</div>
          </div>
          
          <div class="status-item">
            <div class="status-label">请求充电量</div>
            <div class="status-value">{{ chargeAmount }} 度</div>
          </div>
          
          <div class="status-item">
            <div class="status-label">当前状态</div>
            <div class="status-value" :class="statusClass">{{ statusText }}</div>
          </div>
          
          <div class="status-item" v-if="queuePosition > 0">
            <div class="status-label">排队位置</div>
            <div class="status-value">
              第 {{ queuePosition }} 位
            </div>
          </div>
          
          <div class="status-item" v-if="estimatedWaitTime && status === 'waiting'">
            <div class="status-label">剩余等待时间</div>
            <div class="status-value wait-time">
              {{ estimatedWaitTime }}
            </div>
          </div>
        </div>
        
        <div class="action-section">
          <button 
            class="cancel-btn" 
            @click="cancelRequest"
            :disabled="isSubmitting"
          >
            {{ isSubmitting ? '处理中...' : '取消排队' }}
          </button>
          
          <button 
            class="edit-btn" 
            @click="editRequest"
            :disabled="isSubmitting || !canEdit"
          >
            修改请求
          </button>
        </div>
      </div>

      <div class="queue-info-card">
        <h2>{{ chargeMode === 'fast' ? '快充' : '慢充' }}区状态</h2>
        
        <div class="queue-stats">
          <div class="stats-item">
            <div class="stats-icon waiting-icon"></div>
            <div class="stats-info">
              <div class="stats-value">{{ waitingCount }}</div>
              <div class="stats-label">排队中车辆</div>
            </div>
          </div>
          
          <div class="stats-item">
            <div class="stats-icon charging-icon"></div>
            <div class="stats-info">
              <div class="stats-value">{{ chargingCount }}</div>
              <div class="stats-label">充电中车辆</div>
            </div>
          </div>
        </div>
        
        <div class="charger-status">
          <h3>充电桩状态</h3>
          
          <div class="charger-list">
            <div 
              v-for="charger in chargers" 
              :key="charger.id"
              class="charger-item"
              :class="{ 'charger-busy': !charger.available }"
            >
              <div class="charger-name">{{ charger.name }}</div>
              <div class="charger-availability">
                {{ charger.available ? '可用' : '使用中' }}
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import * as chargingApi from '@/api/charging'
import axios from 'axios'

const router = useRouter()
const loading = ref(true)
const isSubmitting = ref(false)

// 轮询通知相关
const notificationTimer = ref(null)
const notificationInterval = 10000 // 10秒检查一次

// 充电请求数据
const hasRequest = ref(false)
const chargeMode = ref('fast')
const queueNumber = ref('')
const chargeAmount = ref(0)
const status = ref<'waiting' | 'charging' | null>(null)
const waitingStatus = ref<'waiting_area' | 'charging_queue' | null>(null)
const queuePosition = ref(0)
const estimatedWaitTime = ref('')
const requestId = ref<number | null>(null)
const statusMessage = ref('')  // 从后端获取的状态消息

// 排队区统计
const waitingCount = ref(0)
const chargingCount = ref(0)

// 充电桩数据
const chargers = ref([])

// 计算属性
const statusText = computed(() => {
  if (!status.value) return '未知'
  
  // 如果有后端提供的状态消息，优先使用
  if (statusMessage.value) {
    return statusMessage.value
  }
  
  switch (status.value) {
    case 'waiting':
      // 根据充电桩ID判断是等候区等候还是充电区排队
      if (waitingStatus.value === 'charging_queue') {
        return '充电区排队中'
      } else if (waitingStatus.value === 'waiting_area') {
        return '等候区等候中'
      } else {
        return '排队等候中'
      }
    case 'charging': return '充电中'
    default: return '未知'
  }
})

const statusClass = computed(() => {
  if (!status.value) return ''
  switch (status.value) {
    case 'waiting': 
      if (waitingStatus.value === 'charging_queue') {
        return 'status-charging-queue'
      } else if (waitingStatus.value === 'waiting_area') {
        return 'status-waiting-area'
      } else {
        return 'status-waiting'
      }
    case 'charging': return 'status-charging'
    default: return ''
  }
})

const canEdit = computed(() => {
  return status.value === 'waiting'
})

// 加载数据
onMounted(() => {
  fetchData()
  // 开始轮询检查充电通知
  startNotificationPolling()
})

// 组件卸载时清除定时器
onUnmounted(() => {
  stopNotificationPolling()
})

const fetchData = async () => {
  loading.value = true
  
  try {
    // 获取用户当前排队信息
    const userData = await chargingApi.getCurrentQueueStatus()
    if (userData) {
      hasRequest.value = true
      chargeMode.value = userData.charging_mode
      queueNumber.value = userData.queue_number
      chargeAmount.value = userData.requested_amount
      status.value = userData.status
      waitingStatus.value = userData.waiting_status || null
      queuePosition.value = userData.waiting_ahead || 0
      requestId.value = userData.request_id
      
      // 提取后端提供的状态消息
      statusMessage.value = userData.status_message || ''
      
      // 使用后端提供的预计等待时间
      estimatedWaitTime.value = userData.estimated_wait_time || ''
    } else {
      hasRequest.value = false
    }
    
    // 获取排队区统计
    const queueStatus = await chargingApi.getQueueStatus()
    
    if (queueStatus) {
      // 根据充电模式过滤统计数据
      if (chargeMode.value === 'fast') {
        waitingCount.value = queueStatus.fast_waiting || 0
        chargingCount.value = queueStatus.fast_charging || 0
        
        // 构建充电桩数据
        chargers.value = queueStatus.fast_piles?.map(pile => ({
          id: pile.id,
          name: `快充桩 ${pile.number}`,
          available: pile.status === 'available',
          type: 'fast'
        })) || []
      } else {
        waitingCount.value = queueStatus.trickle_waiting || 0
        chargingCount.value = queueStatus.trickle_charging || 0
        
        // 构建充电桩数据
        chargers.value = queueStatus.trickle_piles?.map(pile => ({
          id: pile.id,
          name: `慢充桩 ${pile.number}`,
          available: pile.status === 'available',
          type: 'trickle'
        })) || []
      }
      
      // 当所有充电桩都在使用中且有排队车辆时，显示为"排队中"
      if (status.value === 'waiting') {
        const allBusy = chargers.value.every(charger => !charger.available)
        if (allBusy && waitingCount.value > 0) {
          // 移除直接修改计算属性的代码
          // statusText.value = '排队等候中'
        }
      }
    }
    
    // 获取请求ID，用于取消请求
    const requests = await chargingApi.getUserRequests()
    const activeRequest = requests.find(req => 
      req.status === 'waiting' || req.status === 'charging'
    )
    if (activeRequest) {
      requestId.value = activeRequest.id
    }
    
  } catch (error) {
    console.error('加载排队状态数据失败:', error)
    ElMessage.error('加载排队状态数据失败，请重试')
  } finally {
    loading.value = false
  }
}

const refreshData = () => {
  fetchData()
}

const cancelRequest = async () => {
  if (!requestId.value) return
  
  try {
    const result = await ElMessageBox.confirm(
      '确定要取消当前充电请求吗？',
      '取消确认',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )
    
    if (result === 'confirm') {
    isSubmitting.value = true
    
      // 调用取消API
      await chargingApi.cancelRequest(requestId.value)
    
    hasRequest.value = false
      ElMessage.success('充电请求已取消')
      
      // 重定向到充电请求页面
      router.push('/charge-request')
    }
  } catch (error) {
    console.error('取消请求错误:', error)
    
    if (error !== 'cancel') {  // 不是用户取消对话框
      ElMessage.error('取消请求失败，请稍后重试')
    }
  } finally {
    isSubmitting.value = false
  }
}

const editRequest = () => {
  router.push('/charge-request')
}

const navigateToRequest = () => {
  router.push('/charge-request')
}

const goBack = () => {
  router.push('/user-dashboard')
}

// 开始轮询检查充电通知
const startNotificationPolling = () => {
  // 先清除可能存在的定时器
  stopNotificationPolling()
  
  // 设置新的定时器
  notificationTimer.value = setInterval(() => {
    checkChargingNotification()
  }, notificationInterval)
}

// 停止轮询
const stopNotificationPolling = () => {
  if (notificationTimer.value) {
    clearInterval(notificationTimer.value)
    notificationTimer.value = null
  }
}

// 检查充电通知
const checkChargingNotification = async () => {
  // 只有当用户在充电区排队时才需要检查
  if (status.value === 'waiting' && waitingStatus.value === 'charging_queue') {
    try {
      const response = await chargingApi.getChargingNotification()
      
      if (response && response.has_available_pile) {
        // 显示通知弹窗
        showChargingAvailableNotification(response)
      }
    } catch (error) {
      console.error('检查充电通知失败:', error)
    }
  }
}

// 显示充电桩可用通知
const showChargingAvailableNotification = (notification) => {
  // 暂停轮询，避免重复弹窗
  stopNotificationPolling()
  
  // 获取充电桩类型描述
  const pileType = notification.pile_info.pile_type === 'fast' ? '快充桩' : '慢充桩'
  
  ElMessageBox.confirm(
    `您排队的${pileType} ${notification.pile_info.pile_number} 已可用，是否开始充电？`,
    '充电桩可用通知',
    {
      confirmButtonText: '立即充电',
      cancelButtonText: '稍后再说',
      type: 'success'
    }
  ).then(async () => {
    try {
      isSubmitting.value = true
      
      // 调用开始充电API
      await chargingApi.startCharging(notification.request_id)
      
      ElMessage.success('充电已开始！')
      
      // 刷新数据
      await fetchData()
      
      // 如果状态已变为充电中，可以选择跳转到充电状态页面
      if (status.value === 'charging') {
        // 由于之前修改过，不再自动跳转，而是提示用户
        ElMessage({
          message: '充电已开始，您可以在此页面查看充电状态',
          type: 'success',
          duration: 5000
        })
      }
    } catch (error) {
      console.error('开始充电失败:', error)
      ElMessage.error(error.response?.data?.detail || '开始充电失败，请稍后再试')
    } finally {
      isSubmitting.value = false
      // 恢复轮询
      startNotificationPolling()
    }
  }).catch(() => {
    // 用户取消，恢复轮询
    ElMessage.info('您可以稍后再开始充电')
    startNotificationPolling()
  })
}
</script>

<style scoped>
.queue-status-container {
  max-width: 1000px;
  margin: 0 auto;
  padding: 20px;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 25px;
}

.page-header h1 {
  font-size: 24px;
  margin: 0;
  color: var(--text-color);
}

.back-btn {
  background-color: transparent;
  border: 1px solid var(--border-color);
  color: var(--light-text);
  padding: 8px 15px;
  border-radius: 4px;
  font-size: 14px;
  cursor: pointer;
  transition: all 0.3s;
}

.back-btn:hover {
  background-color: #f5f5f5;
  color: var(--text-color);
}

.loading-container {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  min-height: 300px;
}

.loading-spinner {
  border: 4px solid rgba(0, 0, 0, 0.1);
  border-radius: 50%;
  border-top: 4px solid var(--primary-color);
  width: 40px;
  height: 40px;
  animation: spin 1s linear infinite;
  margin-bottom: 20px;
}

@keyframes spin {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}

.no-data-container {
  background-color: white;
  border-radius: 10px;
  padding: 40px;
  text-align: center;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.05);
}

.no-data-icon {
  font-size: 48px;
  margin-bottom: 20px;
}

.no-data-container h3 {
  font-size: 20px;
  margin: 0 0 10px 0;
  color: var(--text-color);
}

.no-data-container p {
  color: var(--light-text);
  margin-bottom: 25px;
}

.primary-btn {
  background-color: var(--primary-color);
  color: white;
  border: none;
  padding: 12px 24px;
  border-radius: 6px;
  font-size: 15px;
  cursor: pointer;
  transition: all 0.3s;
}

.primary-btn:hover {
  background-color: var(--primary-dark);
}

.status-cards {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 20px;
}

.queue-card, .queue-info-card {
  background-color: white;
  border-radius: 10px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.05);
  overflow: hidden;
}

.queue-card {
  display: flex;
  flex-direction: column;
}

.card-header {
  background-color: #f8f9fa;
  padding: 15px 20px;
  border-bottom: 1px solid var(--border-color);
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.card-header h2 {
  margin: 0;
  font-size: 18px;
  color: var(--text-color);
}

.refresh-btn {
  display: flex;
  align-items: center;
  gap: 5px;
  cursor: pointer;
  color: var(--light-text);
  font-size: 14px;
  transition: color 0.3s;
}

.refresh-btn:hover {
  color: var(--primary-color);
}

.refresh-icon {
  font-size: 16px;
}

.status-section {
  padding: 20px;
  flex: 1;
}

.status-item {
  margin-bottom: 18px;
  display: flex;
  align-items: center;
}

.status-item:last-child {
  margin-bottom: 0;
}

.status-label {
  width: 100px;
  font-size: 14px;
  color: var(--light-text);
}

.status-value {
  font-size: 15px;
  font-weight: 500;
  color: var(--text-color);
}

.status-value.highlight {
  font-size: 18px;
  color: var(--primary-color);
  font-weight: 600;
}

.status-value.wait-time {
  font-size: 16px;
  color: #ff9800;
  font-weight: 600;
  display: flex;
  align-items: center;
}

.status-value.wait-time::before {
  content: "⏱️";
  margin-right: 6px;
  font-size: 18px;
}

.status-waiting, .status-waiting-area, .status-charging-queue, .status-charging {
  padding: 4px 8px;
  border-radius: 4px;
  display: inline-block;
}

.status-waiting {
  background-color: #fff3cd;
  color: #856404;
}

.status-waiting-area {
  background-color: #ffe8b3;
  color: #805700;
}

.status-charging-queue {
  background-color: #fff9c2;
  color: #6d5a00;
}

.status-charging {
  background-color: #d4edda;
  color: #155724;
}

.action-section {
  padding: 20px;
  border-top: 1px solid var(--border-color);
  display: flex;
  gap: 15px;
}

.cancel-btn, .edit-btn {
  flex: 1;
  padding: 10px 15px;
  border-radius: 6px;
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.3s;
}

.cancel-btn {
  background-color: #f8d7da;
  color: #721c24;
  border: 1px solid #f5c6cb;
}

.cancel-btn:hover:not(:disabled) {
  background-color: #f1c1c6;
}

.edit-btn {
  background-color: #e2f3f5;
  color: #0c5460;
  border: 1px solid #bee5eb;
}

.edit-btn:hover:not(:disabled) {
  background-color: #d1ecef;
}

.cancel-btn:disabled, .edit-btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.queue-info-card {
  padding: 20px;
}

.queue-info-card h2 {
  margin: 0 0 20px 0;
  font-size: 18px;
  color: var(--text-color);
}

.queue-stats {
  display: flex;
  gap: 20px;
  margin-bottom: 30px;
}

.stats-item {
  background-color: #f8f9fa;
  border-radius: 8px;
  padding: 15px;
  flex: 1;
  display: flex;
  align-items: center;
  gap: 15px;
}

.stats-icon {
  width: 40px;
  height: 40px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.waiting-icon::before {
  content: "🕒";
  font-size: 20px;
}

.charging-icon::before {
  content: "⚡";
  font-size: 20px;
}

.stats-info {
  flex: 1;
}

.stats-value {
  font-size: 24px;
  font-weight: 600;
  color: var(--text-color);
}

.stats-label {
  font-size: 13px;
  color: var(--light-text);
}

.charger-status h3 {
  font-size: 16px;
  margin: 0 0 15px 0;
  color: var(--text-color);
}

.charger-list {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(120px, 1fr));
  gap: 10px;
}

.charger-item {
  background-color: #e8f5e9;
  border-radius: 6px;
  padding: 12px;
  text-align: center;
}

.charger-busy {
  background-color: #f8f9fa;
}

.charger-name {
  font-weight: 500;
  margin-bottom: 5px;
  font-size: 14px;
}

.charger-availability {
  font-size: 12px;
  color: var(--primary-color);
}

.charger-busy .charger-availability {
  color: var(--light-text);
}

@media (max-width: 768px) {
  .status-cards {
    grid-template-columns: 1fr;
  }
  
  .status-item {
    flex-direction: column;
    align-items: flex-start;
    gap: 5px;
  }
  
  .status-label {
    width: 100%;
  }
  
  .queue-stats {
    flex-direction: column;
  }
}
</style> 