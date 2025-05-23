<template>
  <div class="charge-request-container">
    <div class="page-header">
      <h1>{{ isEdit ? '修改充电请求' : '充电请求' }}</h1>
      <button class="back-btn" @click="goBack">返回</button>
    </div>
    
    <!-- 预检查结果弹窗 -->
    <el-dialog
      v-model="showPrecheckModal"
      title="充电状态预检查"
      width="80%"
      :before-close="handleClosePrecheck"
    >
      <div class="precheck-modal-content">
        <div class="precheck-status" :class="precheckStatusClass">
          <i class="el-icon-info-filled" v-if="precheckStatus === 'waiting_area'"></i>
          <i class="el-icon-warning-filled" v-if="precheckStatus === 'charging_queue'"></i>
          <i class="el-icon-success-filled" v-if="precheckStatus === 'direct_charging'"></i>
          <span>{{ precheckMessage }}</span>
        </div>
        
        <div class="precheck-details">
          <div class="precheck-item">
            <span class="item-label">预计等待时间：</span>
            <span class="item-value">{{ estimatedWaitTime }}</span>
          </div>
          
          <div class="precheck-explanation">
            <p v-if="precheckStatus === 'direct_charging'">
              当前有空闲充电桩，您的充电请求将立即开始充电。
            </p>
            <p v-if="precheckStatus === 'charging_queue'">
              当前所有充电桩都在使用中，您的请求将进入充电区排队。一旦有充电桩空闲，系统会自动为您安排充电。
            </p>
            <p v-if="precheckStatus === 'waiting_area'">
              当前充电区已满，您的请求将进入等候区等待。系统会按照先到先得的原则为您分配充电桩。
            </p>
          </div>
        </div>
        
        <div class="precheck-actions">
          <el-button @click="confirmChargingRequest" type="primary" size="large">确认提交</el-button>
          <el-button @click="handleClosePrecheck" size="large">取消</el-button>
        </div>
      </div>
    </el-dialog>

    <div class="request-card">
      <div class="card-header">
        <h2>{{ isEdit ? '修改充电请求' : '新建请求' }}</h2>
        <div class="status-info" v-if="requestStatus">
          <span class="status-label">当前状态:</span>
          <span class="status-value" :class="requestStatusClass">{{ requestStatusText }}</span>
        </div>
      </div>

      <form @submit.prevent="submitRequest" class="request-form">
        <div class="form-group" v-if="isEdit && queueNumber">
          <label>当前排队号</label>
          <div class="current-queue-number">{{ queueNumber }}</div>
          <p class="queue-info" v-if="waitingAhead > 0">
            前方等待车辆: {{ waitingAhead }} 辆
          </p>
        </div>

        <div class="form-group">
          <label for="chargeMode">充电模式</label>
          <div class="radio-group">
            <label class="radio-label">
              <input 
                type="radio" 
                id="fast" 
                value="fast" 
                v-model="chargeMode"
                :disabled="!canEditMode"
              />
              <span class="radio-text">快充模式 (30度/小时)</span>
            </label>
            <label class="radio-label">
              <input 
                type="radio" 
                id="slow" 
                value="slow" 
                v-model="chargeMode"
                :disabled="!canEditMode"
              />
              <span class="radio-text">慢充模式 (7度/小时)</span>
            </label>
          </div>
          <p class="mode-warning" v-if="!canEditMode">
            * 已在充电区，不能修改充电模式。您可以取消充电后重新排队。
          </p>
        </div>

        <div class="form-group">
          <label for="chargeAmount">请求充电量 (度)</label>
          <input 
            type="number" 
            id="chargeAmount" 
            v-model="chargeAmount" 
            min="1" 
            max="100"
            :disabled="!canEditAmount"
            class="form-input" 
          />
          <p class="mode-warning" v-if="!canEditAmount">
            * 已在充电区，不能修改充电量。您可以取消充电后重新排队。
          </p>
          <div class="form-info">
            <span>预计充电时间: {{ estimatedTime }}</span>
            <span>预计费用: {{ estimatedCost }}元</span>
          </div>
        </div>

        <div class="buttons-container">
          <button 
            type="submit" 
            class="submit-btn"
            :disabled="isSubmitting || !isRequestValid"
          >
            {{ submitButtonText }}
          </button>
          
          <button 
            type="button" 
            class="cancel-btn"
            v-if="requestStatus"
            @click="cancelRequest"
          >
            取消充电
          </button>
        </div>

        <div v-if="requestError" class="error-message">
          {{ requestError }}
        </div>
      </form>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import * as chargingApi from '@/api/charging'

const router = useRouter()

// 表单数据
const chargeMode = ref('fast')
const chargeAmount = ref(10)
const isSubmitting = ref(false)
const requestError = ref('')
const isEdit = ref(false)
const requestId = ref<number | null>(null)

// 实际状态数据，从API获取
const requestStatus = ref<null | 'waiting' | 'charging' | null>(null)
const queueNumber = ref<null | string>(null)
const waitingAhead = ref(0)

// 权限控制
const canEditMode = computed(() => !requestStatus.value || requestStatus.value === 'waiting')
const canEditAmount = computed(() => !requestStatus.value || requestStatus.value === 'waiting')

// 加载用户当前充电请求数据
onMounted(async () => {
  try {
    // 使用统一的数据加载方法
    await loadCurrentRequest()
  } catch (error) {
    console.error('获取充电请求失败', error)
    if (error.response?.status === 401) {
      // 存储当前页面URL，以便登录后可以返回
      localStorage.setItem('redirectUrl', router.currentRoute.value.fullPath)
      
      // 显示登录提示
      ElMessageBox.confirm(
        '您需要登录才能查看或创建充电请求',
        '未登录',
        {
          confirmButtonText: '立即登录',
          cancelButtonText: '取消',
          type: 'warning'
        }
      ).then(() => {
        router.push('/login')
      }).catch(() => {
        router.push('/user-dashboard')
      })
    }
  }
  
  // 检查是否有临时保存的数据（从登录页返回）
  const savedMode = localStorage.getItem('tempChargeMode')
  const savedAmount = localStorage.getItem('tempChargeAmount')
  
  if (savedMode) {
    chargeMode.value = savedMode
    localStorage.removeItem('tempChargeMode')
  }
  
  if (savedAmount) {
    chargeAmount.value = Number(savedAmount)
    localStorage.removeItem('tempChargeAmount')
  }
})

// 状态展示
const requestStatusText = computed(() => {
  if (!requestStatus.value) return ''
  
  switch (requestStatus.value) {
    case 'waiting': 
      return `排队中 (号码: ${queueNumber.value}${waitingAhead.value > 0 ? `, 前方 ${waitingAhead.value} 辆车等待` : ''})`
    case 'charging': 
      return '充电中'
    default: 
      return ''
  }
})

const requestStatusClass = computed(() => {
  if (!requestStatus.value) return ''
  switch (requestStatus.value) {
    case 'waiting': return 'status-waiting'
    case 'charging': return 'status-charging'
    default: return ''
  }
})

// 计算属性
const estimatedTime = computed(() => {
  const amount = Number(chargeAmount.value)
  if (isNaN(amount) || amount <= 0) return '0小时0分钟'
  
  const hourRate = chargeMode.value === 'fast' ? 30 : 7
  const hours = amount / hourRate
  
  const fullHours = Math.floor(hours)
  const minutes = Math.round((hours - fullHours) * 60)
  
  return `${fullHours}小时${minutes}分钟`
})

const estimatedCost = computed(() => {
  const amount = Number(chargeAmount.value)
  if (isNaN(amount) || amount <= 0) return '0.00'
  
  // 简化的费用计算，实际应用中应考虑峰谷时段
  const electricityRate = 0.7 // 简化为平均电价
  const serviceRate = 0.8
  
  const totalCost = amount * (electricityRate + serviceRate)
  return totalCost.toFixed(2)
})

const submitButtonText = computed(() => {
  if (isSubmitting.value) return '提交中...'
  return isEdit.value ? '修改请求' : '提交请求'
})

const isRequestValid = computed(() => {
  const amount = Number(chargeAmount.value)
  return !isNaN(amount) && amount > 0 && amount <= 100
})

// 提交充电请求
// 预检查状态
const precheckStatus = ref(null)
const precheckMessage = ref('')
const estimatedWaitTime = ref('')
const showPrecheckModal = ref(false)

// 预检查充电请求
const precheckRequest = async () => {
  if (!isRequestValid.value) return
  
  try {
    isSubmitting.value = true
    requestError.value = ''
    
    const requestData = {
      chargingMode: chargeMode.value,
      requestedAmount: Number(chargeAmount.value)
    }
    
    console.log("预检查充电请求数据:", requestData)
    
    // 发送预检查请求
    const response = await chargingApi.precheckChargingRequest(requestData)
    
    if (response) {
      if (response.can_create) {
        precheckStatus.value = response.status
        precheckMessage.value = response.message
        estimatedWaitTime.value = response.estimated_wait
        
        // 显示预检查结果弹窗
        showPrecheckModal.value = true
      } else {
        // 不能创建请求的情况
        precheckStatus.value = response.status
        requestError.value = response.message
        
        if (response.status === 'has_active_request') {
          // 已有请求，自动加载它
          await loadCurrentRequest()
        }
      }
    }
  } catch (error) {
    // 处理错误
    const errorMessage = error.response?.data?.detail || '预检查失败，请重试'
    requestError.value = errorMessage
    ElMessage.error(errorMessage)
  } finally {
    isSubmitting.value = false
  }
}

// 预检查状态样式
const precheckStatusClass = computed(() => {
  if (!precheckStatus.value) return ''
  
  switch (precheckStatus.value) {
    case 'direct_charging': return 'status-success'
    case 'charging_queue': return 'status-warning'
    case 'waiting_area': return 'status-info'
    default: return ''
  }
})

// 关闭预检查弹窗
const handleClosePrecheck = () => {
  showPrecheckModal.value = false
  isSubmitting.value = false
}

// 确认提交充电请求
const confirmChargingRequest = async () => {
  showPrecheckModal.value = false
  
  try {
    isSubmitting.value = true
    
    const requestData = {
      vehicleId: 1, // 默认使用第一个车辆
      chargingMode: chargeMode.value,
      requestedAmount: Number(chargeAmount.value)
    }
    
    // 提交充电请求
    const response = await chargingApi.createChargingRequest(requestData)
    
    if (response) {
      // 显示成功消息
      ElMessage.success(`充电请求已提交! 排队号: ${response.queue_number}`)
      
      // 等待一下让后端状态稳定，然后重新获取最新状态
      setTimeout(async () => {
        try {
          // 重新获取最新的用户请求状态
          await loadCurrentRequest()
          
          // 根据重新获取的实际状态进行跳转
          if (requestStatus.value === 'charging') {
            // 如果确实开始充电了，跳转到充电状态页面
            router.push('/charging-status')
          } else if (requestStatus.value === 'waiting') {
            // 如果需要排队，跳转到排队状态页面
            router.push('/queue-status')
          } else {
            // 其他状态，保持在当前页面
            console.log('未知状态:', requestStatus.value)
          }
        } catch (error) {
          console.error('重新获取状态失败:', error)
          // 如果获取状态失败，默认跳转到排队状态页面
          router.push('/queue-status')
        }
      }, 1000) // 1秒后跳转，让后端状态稳定
    }
  } catch (error) {
    // 处理错误
    const errorMessage = error.response?.data?.detail || '提交请求失败，请重试'
    requestError.value = errorMessage
    ElMessage.error(errorMessage)
  } finally {
    isSubmitting.value = false
  }
}

const submitRequest = async () => {
  if (!isRequestValid.value) return
  
  try {
    // 执行预检查
    await precheckRequest()
  } catch (error) {
    const errorMessage = error.response?.data?.detail || '预检查失败，请重试'
    requestError.value = errorMessage
    ElMessage.error(errorMessage)
  }
}

// 添加一个方法来加载当前请求信息
const loadCurrentRequest = async () => {
  try {
    console.log('正在重新获取用户请求状态...')
    const requests = await chargingApi.getUserRequests()
    console.log('获取到的请求列表:', requests)
    
    const activeRequest = requests.find(req => 
      req.status === 'waiting' || req.status === 'charging'
    )
    
    console.log('找到的活跃请求:', activeRequest)
    
    if (activeRequest) {
      isEdit.value = true
      requestId.value = activeRequest.id
      requestStatus.value = activeRequest.status
      queueNumber.value = activeRequest.queue_number
      chargeMode.value = activeRequest.charging_mode === 'fast' ? 'fast' : 'slow'
      chargeAmount.value = activeRequest.requested_amount
      waitingAhead.value = activeRequest.waiting_ahead || 0
      
      console.log('已更新前端状态:', {
        requestStatus: requestStatus.value,
        queueNumber: queueNumber.value,
        charging_mode: activeRequest.charging_mode
      })
    } else {
      // 没有活跃请求，重置状态
      isEdit.value = false
      requestId.value = null
      requestStatus.value = null
      queueNumber.value = null
      waitingAhead.value = 0
      
      console.log('没有找到活跃请求，已重置状态')
    }
  } catch (error) {
    console.error('获取充电请求失败', error)
    throw error // 重新抛出错误，让调用者处理
  }
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
    
      await chargingApi.cancelRequest(requestId.value)
    
    requestStatus.value = null
    queueNumber.value = null
      requestId.value = null
    isEdit.value = false
      waitingAhead.value = 0
    
      ElMessage.success('充电请求已取消')
    }
  } catch (error) {
    console.error('取消请求错误:', error)
    
    if (error !== 'cancel') {  // 不是用户取消对话框
      requestError.value = '取消请求失败，请稍后重试'
      ElMessage.error(requestError.value)
    }
  } finally {
    isSubmitting.value = false
  }
}

const goBack = () => {
  router.push('/user-dashboard')
}
</script>

<style scoped>
.charge-request-container {
  max-width: 800px;
  margin: 0 auto;
  padding: 20px;
}

/* 预检查弹窗样式 */
.precheck-modal-content {
  padding: 20px 0;
}

.precheck-status {
  display: flex;
  align-items: center;
  padding: 15px;
  border-radius: 8px;
  margin-bottom: 20px;
  font-weight: 500;
  font-size: 16px;
}

.precheck-status i {
  margin-right: 10px;
  font-size: 24px;
}

.status-success {
  background-color: #f0f9eb;
  color: #67c23a;
  border: 1px solid #e1f3d8;
}

.status-warning {
  background-color: #fdf6ec;
  color: #e6a23c;
  border: 1px solid #faecd8;
}

.status-info {
  background-color: #f4f4f5;
  color: #909399;
  border: 1px solid #e9e9eb;
}

.precheck-details {
  margin-bottom: 25px;
}

.precheck-item {
  margin-bottom: 15px;
  display: flex;
  align-items: center;
}

.item-label {
  font-weight: 500;
  width: 150px;
  color: var(--text-color);
}

.item-value {
  font-weight: 600;
  color: var(--primary-color);
}

.precheck-explanation {
  background-color: #f8f9fa;
  padding: 15px;
  border-radius: 8px;
  margin-top: 15px;
}

.precheck-explanation p {
  margin: 0;
  line-height: 1.6;
  color: var(--text-color);
}

.precheck-actions {
  display: flex;
  justify-content: center;
  gap: 20px;
  margin-top: 30px;
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

.request-card {
  background-color: white;
  border-radius: 12px;
  box-shadow: 0 4px 15px rgba(0, 0, 0, 0.05);
  overflow: hidden;
}

.card-header {
  background-color: #f8f9fa;
  padding: 20px;
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

.status-info {
  display: flex;
  align-items: center;
  gap: 8px;
}

.status-label {
  font-size: 14px;
  color: var(--light-text);
}

.status-value {
  font-size: 14px;
  font-weight: 500;
  padding: 4px 8px;
  border-radius: 4px;
}

.status-waiting {
  background-color: #fff3cd;
  color: #856404;
}

.status-charging {
  background-color: #d4edda;
  color: #155724;
}

.request-form {
  padding: 25px;
}

.form-group {
  margin-bottom: 25px;
}

.form-group label {
  display: block;
  margin-bottom: 8px;
  font-size: 14px;
  color: var(--text-color);
  font-weight: 500;
}

.current-queue-number {
  font-size: 24px;
  font-weight: 600;
  color: var(--primary-color);
  padding: 8px 16px;
  background-color: rgba(76, 175, 80, 0.1);
  border-radius: 6px;
  display: inline-block;
  margin-bottom: 6px;
}

.queue-info {
  font-size: 14px;
  color: var(--light-text);
  margin-top: 5px;
}

.radio-group {
  display: flex;
  gap: 20px;
  margin-bottom: 10px;
}

.radio-label {
  display: flex;
  align-items: center;
  cursor: pointer;
}

.radio-label input {
  margin-right: 8px;
}

.radio-label input:disabled + .radio-text {
  color: var(--light-text);
  opacity: 0.6;
}

.form-input {
  width: 100%;
  padding: 12px;
  border: 1px solid var(--border-color);
  border-radius: 6px;
  font-size: 15px;
}

.form-input:focus {
  outline: none;
  border-color: var(--primary-color);
  box-shadow: 0 0 0 3px rgba(76, 175, 80, 0.1);
}

.form-input:disabled {
  background-color: #f5f5f5;
  cursor: not-allowed;
}

.form-info {
  display: flex;
  justify-content: space-between;
  margin-top: 15px;
  font-size: 14px;
  color: var(--light-text);
}

.mode-warning {
  color: var(--warning-color);
  font-size: 13px;
  margin-top: 8px;
}

.buttons-container {
  display: flex;
  gap: 15px;
  margin-top: 30px;
}

.submit-btn {
  background-color: var(--primary-color);
  color: white;
  border: none;
  padding: 12px 20px;
  border-radius: 6px;
  font-size: 15px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.3s;
  flex: 1;
}

.submit-btn:hover:not(:disabled) {
  background-color: var(--primary-dark);
}

.submit-btn:disabled {
  opacity: 0.7;
  cursor: not-allowed;
}

.cancel-btn {
  background-color: #f8f9fa;
  color: var(--text-color);
  border: 1px solid var(--border-color);
  padding: 12px 20px;
  border-radius: 6px;
  font-size: 15px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.3s;
}

.cancel-btn:hover {
  background-color: #e9ecef;
}

.error-message {
  margin-top: 20px;
  color: var(--error-color);
  padding: 10px;
  background-color: rgba(244, 67, 54, 0.1);
  border-radius: 6px;
  font-size: 14px;
}

@media (max-width: 600px) {
  .card-header {
    flex-direction: column;
    align-items: flex-start;
    gap: 10px;
  }
  
  .radio-group {
    flex-direction: column;
    gap: 10px;
  }
  
  .form-info {
    flex-direction: column;
    gap: 8px;
  }
}
</style> 