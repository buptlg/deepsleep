<template>
  <div class="pile-details-container">
    <div class="header">
      <button class="back-button" @click="goBack">
        <span class="back-icon">←</span>
        返回
      </button>
      <h1>充电桩详情</h1>
    </div>
    
    <div class="loading" v-if="initialLoading">
      <div class="loading-spinner"></div>
      <p>正在加载充电桩详情数据...</p>
    </div>
    
    <div class="pile-info-card" v-else-if="pile">
      <div class="pile-header">
        <h2>{{ pile.name }}</h2>
        <div class="pile-status" :class="{ 'status-active': pile.isActive, 'status-inactive': !pile.isActive }">
          {{ pile.isActive ? '运行中' : '已关闭' }}
        </div>
      </div>
      
      <div class="status-controls">
        <button 
          class="toggle-button" 
          :class="pile.isActive ? 'stop-button' : 'start-button'"
          @click="togglePileStatus">
          {{ pile.isActive ? '关闭充电桩' : '启动充电桩' }}
        </button>
        <button class="refresh-button" @click="refreshAllData">
          <span class="refresh-icon">🔄</span>
          刷新数据
        </button>
      </div>
      
      <div class="info-section">
        <h3>基本信息</h3>
        <div class="info-grid">
          <div class="info-item">
            <div class="info-label">充电桩类型</div>
            <div class="info-value">{{ pileTypeInfo.type }}</div>
          </div>
          <div class="info-item">
            <div class="info-label">功率</div>
            <div class="info-value">{{ pileTypeInfo.power }} kW</div>
          </div>
          <div class="info-item">
            <div class="info-label">运行状态</div>
            <div class="info-value status-text" :class="pile.isActive ? 'text-success' : 'text-danger'">
              {{ pile.isActive ? '正常运行' : '已停止' }}
            </div>
          </div>
          <div class="info-item">
            <div class="info-label">当前排队车辆</div>
            <div class="info-value">{{ pile.queueCount }} 辆</div>
          </div>
        </div>
      </div>
      
      <div class="info-section">
        <h3>累计统计</h3>
        <div class="info-grid">
          <div class="info-item">
            <div class="info-label">累计充电次数</div>
            <div class="info-value">{{ pile.totalCharges }} 次</div>
          </div>
          <div class="info-item">
            <div class="info-label">累计充电时长</div>
            <div class="info-value">{{ pile.totalHours }} 小时</div>
          </div>
          <div class="info-item">
            <div class="info-label">累计充电量</div>
            <div class="info-value">{{ pile.totalEnergy }} 度</div>
          </div>
          <div class="info-item">
            <div class="info-label">累计收入</div>
            <div class="info-value">¥{{ (pile.totalEnergy * 1.0).toFixed(2) }}</div>
          </div>
        </div>
      </div>
      
      <div class="info-section">
        <h3>充电中车辆</h3>
        <div v-if="chargingAreaLoading" class="loading-container">
          <div class="loading-spinner"></div>
          <p>加载充电中车辆数据...</p>
        </div>
        <div class="waiting-cars" v-else-if="chargingCars.length > 0">
          <div class="table-responsive">
            <table class="cars-table">
              <thead>
                <tr>
                  <th>排队号</th>
                  <th>用户ID</th>
                  <th>电池容量</th>
                  <th>请求充电量</th>
                  <th>已充电量</th>
                  <th>充电进度</th>
                  <th>状态</th>
                  <th>充电时长</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="car in chargingCars" :key="car.id">
                  <td>{{ car.queueNumber }}</td>
                  <td>{{ car.userId }}</td>
                  <td>{{ car.batteryCapacity }} 度</td>
                  <td>{{ car.requestedCharge }} 度</td>
                  <td>{{ car.chargedAmount || 0 }} 度</td>
                  <td>
                    <div class="progress-container">
                      <div class="progress-bar">
                        <div class="progress-fill" :style="{ width: `${car.progressPercent || 0}%` }"></div>
                      </div>
                      <span class="progress-text">{{ car.progressPercent || 0 }}%</span>
                    </div>
                  </td>
                  <td><span class="status-charging">{{ car.status }}</span></td>
                  <td>{{ car.queueTime }}</td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>
        <div class="no-cars" v-else>
          当前没有车辆正在充电
        </div>
      </div>
      
      <div class="info-section">
        <h3>充电区等待车辆</h3>
        <div v-if="chargingAreaLoading" class="loading-container">
          <div class="loading-spinner"></div>
          <p>加载充电区等待车辆数据...</p>
        </div>
        <div class="waiting-cars" v-else-if="waitingCars.length > 0">
          <div class="table-responsive">
            <table class="cars-table">
              <thead>
                <tr>
                  <th>排队号</th>
                  <th>用户ID</th>
                  <th>电池容量</th>
                  <th>请求充电量</th>
                  <th>状态</th>
                  <th>等待时长</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="car in waitingCars" :key="car.id">
                  <td>{{ car.queueNumber }}</td>
                  <td>{{ car.userId }}</td>
                  <td>{{ car.batteryCapacity }} 度</td>
                  <td>{{ car.requestedCharge }} 度</td>
                  <td><span class="status-waiting">{{ car.status }}</span></td>
                  <td>{{ car.queueTime }}</td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>
        <div class="no-cars" v-else>
          当前没有车辆在充电区等待
        </div>
      </div>
      
      <div class="info-section">
        <h3>等候区车辆</h3>
        <div v-if="waitingAreaLoading" class="loading-container">
          <div class="loading-spinner"></div>
          <p>加载等候区车辆数据...</p>
        </div>
        <div class="waiting-cars" v-else-if="waitingAreaCars.length > 0">
          <div class="table-responsive">
            <table class="cars-table">
              <thead>
                <tr>
                  <th>排队号</th>
                  <th>用户名</th>
                  <th>充电模式</th>
                  <th>请求充电量</th>
                  <th>排队状态</th>
                  <th>等候时长</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="car in waitingAreaCars" :key="car.id">
                  <td>{{ car.queue_number }}</td>
                  <td>{{ car.user_name }}</td>
                  <td>{{ car.charging_mode === 'fast' ? '快充' : '慢充' }}</td>
                  <td>{{ car.requested_amount }} 度</td>
                  <td><span class="status-waiting-area">{{ car.status }}</span></td>
                  <td>{{ formatQueueTime(car.waiting_time) }}</td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>
        <div class="no-cars" v-else>
          当前没有车辆在等候区等待
        </div>
      </div>
      
      <div class="info-section">
        <h3>使用趋势</h3>
        <div class="chart-tabs">
          <button 
            class="tab-button" 
            :class="{ active: activeTab === 'daily' }"
            @click="activeTab = 'daily'">
            日使用趋势
          </button>
          <button 
            class="tab-button" 
            :class="{ active: activeTab === 'weekly' }"
            @click="activeTab = 'weekly'">
            周使用趋势
          </button>
          <button 
            class="tab-button" 
            :class="{ active: activeTab === 'monthly' }"
            @click="activeTab = 'monthly'">
            月使用趋势
          </button>
        </div>
        
        <div class="chart-placeholder">
          <div class="chart-message">图表数据加载中...</div>
          <div class="chart-hint">此处将显示{{ pile.name }}的{{ getTabText() }}使用数据图表</div>
        </div>
      </div>
    </div>
    
    <div class="loading" v-else-if="!pile && !initialLoading">
      <p>未找到充电桩信息</p>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onBeforeUnmount } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import axios from 'axios'
import * as adminApi from '@/api/admin'

interface ChargingPile {
  id: number;
  name: string;
  isActive: boolean;
  totalCharges: number;
  totalHours: number;
  totalEnergy: number;
  queueCount: number;
  power: number;  // 充电功率
  pile_number: string; // 充电桩编号
}

interface WaitingCar {
  id: number;
  userId: string;
  batteryCapacity: number;
  requestedCharge: number;
  queueTime: string;
  status: string;
  queueNumber: string;
  chargedAmount?: number;
  progressPercent?: number;
}

const router = useRouter()
const route = useRoute()
const pile = ref<ChargingPile | null>(null)
const chargingCars = ref<WaitingCar[]>([])  // 正在充电中的车辆
const waitingCars = ref<WaitingCar[]>([])   // 充电区等待的车辆
const waitingAreaCars = ref<WaitingCar[]>([])
const activeTab = ref('daily')
const loading = ref(true)
const initialLoading = ref(true)  // 新增：初始化加载状态
const chargingAreaLoading = ref(false)  // 充电区数据加载状态
const waitingAreaLoading = ref(false)   // 等候区数据加载状态
const error = ref('')

// 获取充电桩数据
const fetchPileData = async () => {
  try {
    loading.value = true
    const pileId = parseInt(route.params.id as string)
    
    // 从API获取所有充电桩数据
    const response = await adminApi.getAdminStatistics()
    const allPiles = response.chargingPiles || []
    
    // 查找对应ID的充电桩
    pile.value = allPiles.find(p => p.id === pileId) || null
    
    // 如果没有找到，跳转回管理员仪表盘
    if (!pile.value) {
      error.value = '未找到充电桩信息'
      router.push('/admin-dashboard')
    }
    
    // 获取充电桩详情信息
    try {
      const pileDetails = await adminApi.getPileDetails(pileId)
      if (pileDetails && pile.value) {
        // 更新额外的充电桩详情信息
        pile.value = {
          ...pile.value,
          ...pileDetails
        }
      }
    } catch (detailError) {
      console.error('获取充电桩详情失败:', detailError)
    }
    
  } catch (err) {
    console.error('获取充电桩数据失败:', err)
    error.value = '加载充电桩数据失败，请重试'
  } finally {
    loading.value = false
  }
}

// 获取等待车辆数据
const fetchWaitingCars = async () => {
  try {
    chargingAreaLoading.value = true
    
    // 从后端API获取充电桩队列数据，直接使用路由参数
    const pileId = parseInt(route.params.id as string)
    const response = await adminApi.getPileQueue(pileId)
    console.log('充电桩车辆API返回数据:', response)
    
    if (response && Array.isArray(response)) {
      // 分离充电中和等待中的车辆
      chargingCars.value = response
        .filter(car => car.status === 'charging' || car.is_charging === true)
        .map(car => ({
          id: car.id || 0,
          userId: car.user_id || car.user_name || '',
          batteryCapacity: car.battery_capacity || 0,
          requestedCharge: car.requested_amount || 0,
          queueTime: formatQueueTime(car.charging_time || car.waiting_time || 0),
          status: '充电中',
          queueNumber: car.queue_number || '',
          chargedAmount: car.charged_amount || 0,
          progressPercent: car.progress_percent || 0
        }));
      
      waitingCars.value = response
        .filter(car => car.status === 'waiting' || (car.is_charging === false && car.status !== 'charging'))
        .map(car => ({
          id: car.id || 0,
          userId: car.user_id || car.user_name || '',
          batteryCapacity: car.battery_capacity || 0,
          requestedCharge: car.requested_amount || 0,
          queueTime: formatQueueTime(car.waiting_time || 0),
          status: '充电区排队中',
          queueNumber: car.queue_number || ''
        }));
      
      console.log('充电中车辆:', chargingCars.value)
      console.log('充电区等待车辆:', waitingCars.value)
    }
  } catch (err) {
    console.error('获取充电区车辆数据失败:', err)
    chargingCars.value = []
    waitingCars.value = []
  } finally {
    chargingAreaLoading.value = false
  }
}

// 获取等候区等待车辆数据
const fetchWaitingAreaCars = async () => {
  try {
    waitingAreaLoading.value = true
    
    // 从后端API获取等候区等待车辆数据
    const response = await adminApi.getWaitingArea()
    console.log('等候区车辆API返回数据:', response)
    
    if (response && Array.isArray(response)) {
      waitingAreaCars.value = response.map(car => ({
        ...car,
        status: '等候区等候中'
      }))
    }
  } catch (err) {
    console.error('获取等候区等待车辆数据失败:', err)
    waitingAreaCars.value = []
  } finally {
    waitingAreaLoading.value = false
  }
}

// 格式化排队时间（小时转为更友好的显示）
const formatQueueTime = (hours: number) => {
  if (hours < 0.0166) { // 小于1分钟
    return '刚刚加入'
  } else if (hours < 1) {
    const minutes = Math.floor(hours * 60)
    return `${minutes}分钟`
  } else {
    const h = Math.floor(hours)
    const m = Math.floor((hours - h) * 60)
    return `${h}小时${m > 0 ? `${m}分钟` : ''}`
  }
}

// 手动刷新所有数据
const refreshAllData = async () => {
  await Promise.all([
    fetchPileData(),
    fetchWaitingCars(),
    fetchWaitingAreaCars()
  ])
}

// 切换充电桩状态
const togglePileStatus = async () => {
  if (!pile.value) return
  
  try {
    // 调用后端API切换充电桩状态
    await adminApi.togglePileStatus(pile.value.id)
    
    // 更新本地状态
    pile.value.isActive = !pile.value.isActive
    
    // 重新获取最新数据
    await fetchPileData()
  } catch (err) {
    console.error('切换充电桩状态失败:', err)
    alert('操作失败，请稍后重试')
  }
}

// 返回上一页
const goBack = () => {
  router.push('/admin-dashboard')
}

// 获取选项卡文本
const getTabText = () => {
  switch (activeTab.value) {
    case 'daily': return '日'
    case 'weekly': return '周'
    case 'monthly': return '月'
    default: return '日'
  }
}

// 获取充电桩类型和功率
const pileTypeInfo = computed(() => {
  if (!pile.value) return { type: '', power: 0 }
  
  // 根据充电桩名称或类型判断
  const isFastCharging = pile.value.name.includes('快充')
  
  return {
    type: isFastCharging ? '快速充电桩' : '慢速充电桩',
    power: isFastCharging ? 30 : 7 // 默认功率，如果API提供则使用API值
  }
})

// 定时刷新数据
let refreshInterval: number | null = null

onMounted(async () => {
  try {
    initialLoading.value = true
    
    // 先获取充电桩基础数据
    await fetchPileData()
    
    // 充电桩数据加载完成后，再获取车辆数据
    await Promise.all([
      fetchWaitingCars(),
      fetchWaitingAreaCars()
    ])
  } catch (error) {
    console.error('初始化数据加载失败:', error)
  } finally {
    initialLoading.value = false
  }
  
  // 设置定时刷新 - 每15秒刷新一次实时数据，提高实时性
  refreshInterval = window.setInterval(async () => {
    try {
      // 只刷新车辆数据，减少不必要的请求
      await fetchWaitingCars()
      await fetchWaitingAreaCars()
      // 每分钟刷新一次充电桩基础数据
      if (Date.now() % 60000 < 15000) {
        await fetchPileData()
      }
    } catch (error) {
      console.error('定时刷新数据失败:', error)
    }
  }, 15000) as unknown as number
})

// 组件卸载时清除定时器
onBeforeUnmount(() => {
  if (refreshInterval !== null) {
    clearInterval(refreshInterval)
  }
})
</script>

<style scoped>
:root {
  --admin-primary-color: #1976d2;
  --admin-primary-light: rgba(25, 118, 210, 0.1);
  --admin-primary-dark: #1565c0;
  --card-shadow: 0 4px 15px rgba(0, 0, 0, 0.05);
  --card-hover-shadow: 0 8px 25px rgba(0, 0, 0, 0.1);
  --transition-time: 0.3s;
  --green-color: #4caf50;
  --red-color: #f44336;
  --orange-color: #ff9800;
  --blue-color: #2196f3;
  --light-text: #757575;
  --text-color: #333333;
  --border-color: #e0e0e0;
}

/* 全局背景 */
body {
  margin: 0;
  padding: 0;
  background-color: #f9fafc;
}

html, body {
  height: 100%;
  width: 100%;
  overflow-x: hidden;
}

.pile-details-container {
  max-width: 1200px;
  margin: 0 auto;
  padding: 2rem;
  min-height: 100vh;
}

.header {
  display: flex;
  align-items: center;
  margin-bottom: 2rem;
  position: relative;
}

.back-button {
  display: flex;
  align-items: center;
  background: none;
  border: none;
  color: var(--admin-primary-color);
  font-size: 1rem;
  padding: 0.5rem 1rem;
  cursor: pointer;
  transition: all 0.3s;
  position: absolute;
  left: 0;
}

.back-icon {
  margin-right: 0.5rem;
  font-size: 1.2rem;
}

.back-button:hover {
  background-color: var(--admin-primary-light);
  border-radius: 4px;
}

.header h1 {
  flex-grow: 1;
  text-align: center;
  margin: 0;
  font-size: 1.8rem;
  color: var(--text-color);
}

.pile-info-card {
  background-color: white;
  border-radius: 1rem;
  padding: 2rem;
  box-shadow: var(--card-shadow);
  margin-bottom: 2rem;
  animation: fadeIn 0.5s ease-out;
}

.pile-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 1.5rem;
  padding-bottom: 1rem;
  border-bottom: 1px solid var(--border-color);
}

.pile-header h2 {
  font-size: 1.5rem;
  margin: 0;
  color: var(--text-color);
}

.pile-status {
  padding: 0.5rem 1rem;
  border-radius: 50px;
  font-size: 0.9rem;
  font-weight: 500;
}

.status-active {
  background-color: rgba(76, 175, 80, 0.1);
  color: var(--green-color);
}

.status-inactive {
  background-color: rgba(244, 67, 54, 0.1);
  color: var(--red-color);
}

.status-controls {
  display: flex;
  justify-content: flex-end;
  margin-bottom: 2rem;
}

.toggle-button {
  padding: 0.8rem 1.5rem;
  border-radius: 0.5rem;
  font-size: 1rem;
  font-weight: 500;
  cursor: pointer;
  transition: all var(--transition-time);
  border: none;
}

.start-button {
  background-color: var(--green-color);
  color: white;
}

.start-button:hover {
  background-color: #43a047;
}

.stop-button {
  background-color: var(--red-color);
  color: white;
}

.stop-button:hover {
  background-color: #e53935;
}

.refresh-button {
  padding: 0.8rem 1.5rem;
  border-radius: 0.5rem;
  font-size: 1rem;
  font-weight: 500;
  cursor: pointer;
  transition: all var(--transition-time);
  border: none;
  background-color: var(--admin-primary-color);
  color: white;
  margin-left: 1rem;
}

.refresh-button:hover {
  background-color: var(--admin-primary-dark);
}

.info-section {
  margin-bottom: 2rem;
  padding: 0 0 1rem 0;
}

.info-section h3 {
  font-size: 1.2rem;
  margin: 0 0 1rem 0;
  color: var(--text-color);
  position: relative;
  padding-left: 1rem;
}

.info-section h3::before {
  content: "";
  position: absolute;
  left: 0;
  top: 0.2rem;
  height: 1em;
  width: 4px;
  background-color: var(--admin-primary-color);
  border-radius: 2px;
}

.info-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(250px, 1fr));
  gap: 1.5rem;
}

.info-item {
  padding: 1rem;
  background-color: rgba(0, 0, 0, 0.02);
  border-radius: 0.5rem;
}

.info-label {
  font-size: 0.9rem;
  color: var(--light-text);
  margin-bottom: 0.5rem;
}

.info-value {
  font-size: 1.1rem;
  font-weight: 600;
  color: var(--text-color);
}

.text-success {
  color: var(--green-color);
}

.text-danger {
  color: var(--red-color);
}

.status-charging {
  background-color: #d4edda;
  color: #155724;
  padding: 4px 8px;
  border-radius: 4px;
  font-size: 0.9rem;
}

.status-waiting {
  background-color: #fff3cd;
  color: #856404;
  padding: 4px 8px;
  border-radius: 4px;
  font-size: 0.9rem;
}

.status-waiting-area {
  background-color: #ffe8b3;
  color: #805700;
  padding: 4px 8px;
  border-radius: 4px;
  font-size: 0.9rem;
}

.waiting-cars {
  margin-top: 1rem;
}

.no-cars {
  padding: 2rem;
  text-align: center;
  background-color: rgba(0, 0, 0, 0.02);
  border-radius: 0.5rem;
  color: var(--light-text);
}

.table-responsive {
  overflow-x: auto;
  background-color: rgba(0, 0, 0, 0.02);
  border-radius: 0.5rem;
}

.cars-table {
  width: 100%;
  border-collapse: collapse;
}

.cars-table th {
  text-align: left;
  padding: 1rem;
  font-size: 0.9rem;
  font-weight: 600;
  color: var(--text-color);
  border-bottom: 1px solid var(--border-color);
}

.cars-table td {
  padding: 1rem;
  border-bottom: 1px solid var(--border-color);
  font-size: 0.9rem;
  color: var(--text-color);
}

.cars-table tr:last-child td {
  border-bottom: none;
}

.progress-container {
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.progress-bar {
  width: 80px;
  height: 8px;
  background-color: #e0e0e0;
  border-radius: 4px;
  overflow: hidden;
}

.progress-fill {
  height: 100%;
  background-color: var(--green-color);
  border-radius: 4px;
  transition: width 0.3s ease;
}

.progress-text {
  font-size: 0.8rem;
  color: var(--text-color);
  font-weight: 500;
  min-width: 35px;
}

.chart-tabs {
  display: flex;
  border-bottom: 1px solid var(--border-color);
  margin-bottom: 1.5rem;
}

.tab-button {
  padding: 0.8rem 1.5rem;
  background: none;
  border: none;
  border-bottom: 2px solid transparent;
  font-size: 0.9rem;
  color: var(--light-text);
  cursor: pointer;
  transition: all 0.3s;
}

.tab-button.active {
  border-bottom-color: var(--admin-primary-color);
  color: var(--admin-primary-color);
  font-weight: 500;
}

.chart-placeholder {
  height: 300px;
  display: flex;
  flex-direction: column;
  justify-content: center;
  align-items: center;
  background-color: rgba(0, 0, 0, 0.02);
  border-radius: 0.5rem;
}

.chart-message {
  font-size: 1.2rem;
  color: var(--light-text);
  margin-bottom: 1rem;
}

.chart-hint {
  font-size: 0.9rem;
  color: var(--light-text);
  opacity: 0.7;
}

.loading {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  text-align: center;
  font-size: 1.2rem;
  color: var(--light-text);
  padding: 5rem 0;
  min-height: 300px;
}

.loading .loading-spinner {
  border: 4px solid rgba(0, 0, 0, 0.1);
  border-radius: 50%;
  border-top: 4px solid var(--admin-primary-color);
  width: 40px;
  height: 40px;
  animation: spin 1s linear infinite;
  margin-bottom: 20px;
}

.loading p {
  margin: 0;
  font-size: 1rem;
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

@media (max-width: 768px) {
  .pile-details-container {
    padding: 1.5rem;
  }
  
  .pile-info-card {
    padding: 1.5rem;
  }
  
  .header {
    margin-bottom: 1.5rem;
  }
  
  .back-button {
    position: relative;
    padding-left: 0;
  }
  
  .header h1 {
    font-size: 1.5rem;
  }
  
  .info-grid {
    grid-template-columns: 1fr;
  }
}

.loading-container {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 2rem;
  background-color: rgba(0, 0, 0, 0.02);
  border-radius: 0.5rem;
}

@keyframes spin {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}
</style> 