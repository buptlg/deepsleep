<template>
  <div class="admin-dashboard-container">
    <!-- 顶部信息栏 -->
    <div class="dashboard-header">
      <div class="header-left">
        <h1>管理员控制台</h1>
        <div class="greeting">欢迎回来，<span class="user-highlight">{{ username }}</span></div>
      </div>
      <div class="user-info">
        <div class="user-avatar">{{ username.charAt(0).toUpperCase() }}</div>
        <button class="logout-btn" @click="logout">
          <span class="logout-icon">⟲</span>
          退出登录
        </button>
      </div>
    </div>
    
    <!-- 核心指标卡片 -->
    <div class="dashboard-stats">
      <div class="stat-card">
        <div class="stat-icon pile-icon"></div>
        <div class="stat-content">
          <div class="stat-value">{{ activePiles }}/{{ totalPiles }}</div>
          <div class="stat-label">运行中充电桩</div>
        </div>
      </div>
      
      <div class="stat-card">
        <div class="stat-icon queue-icon"></div>
        <div class="stat-content">
          <div class="stat-value">{{ totalQueuedCars }}</div>
          <div class="stat-label">排队车辆总数</div>
        </div>
      </div>
      
      <div class="stat-card">
        <div class="stat-icon revenue-icon"></div>
        <div class="stat-content">
          <div class="stat-value">¥{{ totalRevenue }}</div>
          <div class="stat-label">今日总收入</div>
        </div>
      </div>
    </div>

    <!-- 主要内容区 -->
    <div class="dashboard-main">
      <!-- 左侧列 -->
      <div class="dashboard-column">
        <!-- 充电桩管理 -->
        <div class="dashboard-section">
          <div class="section-title">
            <h2>充电桩管理</h2>
            <div class="subtitle">查看和控制充电桩状态</div>
          </div>

          <div class="pile-management">
            <div class="pile-card" 
              v-for="pile in chargingPiles" 
              :key="pile.id"
              :class="{ 'status-active': pile.isActive, 'status-inactive': !pile.isActive }">
              <div class="pile-header">
                <h3>{{ pile.name }}</h3>
                <div class="pile-status" :class="{
                  'status-active': pile.isActive && !pile.isOccupied,
                  'status-occupied': pile.isOccupied,
                  'status-inactive': !pile.isActive
                }">
                  <span class="status-icon">
                    {{ pile.isActive ? (pile.isOccupied ? '🔴' : '🟢') : '⚫' }}
                  </span>
                  {{ pile.statusText || (pile.isActive ? (pile.isOccupied ? '正在使用' : '空闲可用') : '已关闭') }}
                </div>
              </div>
              
              <!-- 队列信息 -->
              <div v-if="pile.queueCount > 0" class="pile-queue-info">
                <div class="queue-indicator">
                  <span class="queue-icon">👥</span>
                  <span class="queue-text">{{ pile.queueCount }}辆车排队等候</span>
                </div>
              </div>
              
              <div class="pile-stats">
                <div class="pile-stat">
                  <div class="stat-label">充电次数</div>
                  <div class="stat-value">{{ pile.totalCharges }}</div>
                </div>
                <div class="pile-stat">
                  <div class="stat-label">充电时长</div>
                  <div class="stat-value">{{ pile.totalHours }}h</div>
                </div>
                <div class="pile-stat">
                  <div class="stat-label">充电量</div>
                  <div class="stat-value">{{ pile.totalEnergy }}度</div>
                </div>
              </div>
              
              <div class="pile-footer">
                <!-- 根据充电桩状态显示不同的操作按钮 -->
                <div v-if="!pile.isActive" class="pile-actions">
                  <button 
                    class="toggle-button start-button"
                    @click="togglePileStatus(pile.id)">
                    启动充电桩
                  </button>
                </div>
                
                <div v-else-if="pile.isOccupied" class="pile-actions">
                  <button 
                    class="toggle-button disabled-button"
                    disabled
                    title="充电桩正在使用中，无法关闭">
                    充电中，无法关闭
                  </button>
                </div>
                
                <div v-else class="pile-actions">
                  <button 
                    class="toggle-button stop-button"
                    @click="togglePileStatus(pile.id)">
                    关闭充电桩
                  </button>
                </div>
                
                <button class="view-button" @click="viewPileDetails(pile.id)">查看详情</button>
              </div>
            </div>
          </div>
        </div>
      </div>
      
      <!-- 右侧列 -->
      <div class="dashboard-column">
        <!-- 正在充电车辆信息 -->
        <div class="dashboard-section">
          <div class="section-title">
            <h2>正在充电车辆信息</h2>
            <div class="subtitle">查看当前正在充电的车辆详情</div>
            <button class="refresh-btn" @click="fetchChargingVehicles">
              <span class="refresh-icon">🔄</span> 刷新
            </button>
          </div>

          <div class="waiting-queue">
            <div v-if="loadingVehicles" class="loading-info">
              <div class="loading-spinner"></div>
              <p>加载等候车辆信息...</p>
            </div>
            
            <div v-else-if="waitingVehicles.length === 0" class="no-data-info">
              <p>当前没有等候车辆</p>
            </div>
            
            <div v-else class="table-responsive">
              <table class="queue-table">
                <thead>
                  <tr>
                    <th>排队号</th>
                    <th>用户名</th>
                    <th>充电模式</th>
                    <th>请求量(度)</th>
                    <th>状态</th>
                    <th>等待/充电时长</th>
                    <th v-if="hasChargingVehicles">进度</th>
                  </tr>
                </thead>
                <tbody>
                  <tr v-for="vehicle in waitingVehicles" :key="vehicle.queue_number">
                    <td>{{ vehicle.queue_number }}</td>
                    <td>{{ vehicle.user_name }}</td>
                    <td>{{ vehicle.charging_mode === 'FAST' ? '快充' : '慢充' }}</td>
                    <td>{{ vehicle.requested_amount }}</td>
                    <td>
                      <span 
                        class="status-tag" 
                        :class="{
                          'status-charging': vehicle.status === '充电中',
                          'status-waiting': vehicle.status === '充电区排队中',
                          'status-waiting-area': vehicle.status === '等候区等候中'
                        }"
                      >
                        {{ vehicle.status }}
                        <span v-if="vehicle.status === '充电中' && vehicle.charging_pile">
                          ({{ vehicle.charging_pile }})
                        </span>
                      </span>
                    </td>
                    <td>
                      {{ formatTime(vehicle.status === '充电中' ? vehicle.charging_time : vehicle.waiting_time) }}
                    </td>
                    <td v-if="hasChargingVehicles && vehicle.status === '充电中'">
                      <div class="progress-bar">
                        <div 
                          class="progress-filled"
                          :style="{ width: `${vehicle.progress_percent || 0}%` }"
                        ></div>
                      </div>
                      <div class="progress-text">
                        {{ vehicle.charged_amount || 0 }}/{{ vehicle.requested_amount }}度
                        ({{ vehicle.progress_percent || 0 }}%)
                      </div>
                    </td>
                    <td v-else-if="hasChargingVehicles">-</td>
                  </tr>
                </tbody>
              </table>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- 报表展示 -->
    <div class="dashboard-section full-width">
      <div class="section-title">
        <h2>充电数据报表</h2>
        <div class="subtitle">查看充电统计数据</div>
      </div>

      <div class="report-section">
        <div class="report-filters">
          <div class="filter-group">
            <label>时间范围</label>
            <select v-model="reportTimeRange" @change="generateReport">
              <option value="day">日报表</option>
              <option value="week">周报表</option>
              <option value="month">月报表</option>
            </select>
          </div>
          
          <div class="filter-group">
            <label>充电桩</label>
            <select v-model="reportPileId" @change="generateReport">
              <option value="all">所有充电桩</option>
              <option v-for="pile in chargingPiles" :key="pile.id" :value="pile.id">{{ pile.name }}</option>
            </select>
          </div>
          
          <div class="filter-status">
            <span v-if="reportLoading" class="loading-indicator">
              <span class="loading-spinner"></span>
              正在生成报表...
            </span>
            <span v-else-if="showReport" class="report-ready">
              📊 报表已生成
            </span>
          </div>
        </div>
        
        <div v-if="showReport">
          <div v-if="reportData.length === 0" class="no-report-data">
            <div class="empty-icon">📊</div>
            <p v-if="reportPileId === 'all'">所选时间范围内暂无充电数据</p>
            <p v-else>该充电桩在所选时间范围内暂无充电数据</p>
            <small v-if="reportPileId === 'all'">请尝试选择其他时间范围或充电桩</small>
            <small v-else>
              充电桩 {{ chargingPiles.find(p => p.id == reportPileId)?.name || '未知' }} 
              在{{ getTimeRangeLabel() }}期间没有充电记录，请选择其他时间范围
            </small>
          </div>
          
          <div v-else class="table-responsive">
            <div class="report-summary">
              <h4>{{ getReportTitle() }}</h4>
              <p class="report-subtitle">数据统计时间：{{ getDateRangeText() }}</p>
            </div>
            
            <table class="report-table">
              <thead>
                <tr>
                  <th>时间范围</th>
                  <th>充电桩编号</th>
                  <th>累计充电次数</th>
                  <th>累计充电时长(小时)</th>
                  <th>累计充电量(度)</th>
                  <th>累计充电费用(元)</th>
                  <th>累计服务费用(元)</th>
                  <th>累计总费用(元)</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="report in reportData" :key="report.id">
                  <td>{{ report.timeRange }}</td>
                  <td>{{ report.pileNumber }}</td>
                  <td>{{ report.totalCharges }}</td>
                  <td>{{ report.totalHours }}</td>
                  <td>{{ report.totalEnergy }}</td>
                  <td>¥{{ report.chargeFee }}</td>
                  <td>¥{{ report.serviceFee }}</td>
                  <td><strong>¥{{ report.totalFee }}</strong></td>
                </tr>
              </tbody>
              <tfoot v-if="reportData.length > 1">
                <tr class="summary-row">
                  <td colspan="2"><strong>合计</strong></td>
                  <td><strong>{{ getTotalCharges() }}</strong></td>
                  <td><strong>{{ getTotalHours() }}</strong></td>
                  <td><strong>{{ getTotalEnergy() }}</strong></td>
                  <td><strong>¥{{ getTotalChargeFee() }}</strong></td>
                  <td><strong>¥{{ getTotalServiceFee() }}</strong></td>
                  <td><strong>¥{{ getTotalFee() }}</strong></td>
                </tr>
              </tfoot>
            </table>
          </div>
        </div>
        
        <div class="chart-container" v-if="showReport && reportData.length > 0">
          <div class="chart-header">
            <h3>数据可视化</h3>
            <div class="chart-subtitle">
              <span v-if="reportData.length === 1">单个充电桩数据分析</span>
              <span v-else>充电桩对比分析（{{ reportData.length }}个充电桩）</span>
            </div>
            <div class="chart-selector">
              <button 
                class="chart-type-btn" 
                :class="{ active: chartType === 'charges' }"
                @click="chartType = 'charges'">
                充电次数
              </button>
              <button 
                class="chart-type-btn" 
                :class="{ active: chartType === 'energy' }"
                @click="chartType = 'energy'">
                充电量
              </button>
              <button 
                class="chart-type-btn" 
                :class="{ active: chartType === 'revenue' }"
                @click="chartType = 'revenue'">
                收入
              </button>
            </div>
          </div>
          
          <div class="chart-placeholder">
            <div class="chart-bars" :class="{ 'single-bar': reportData.length === 1 }">
              <div 
                v-for="(report, index) in reportData" 
                :key="index"
                class="chart-bar"
                :class="{ 'single-bar-item': reportData.length === 1 }"
                :style="{ height: getBarHeight(report) }"
              >
                <div class="bar-value">{{ getChartValue(report) }}</div>
              </div>
            </div>
            <div class="chart-labels">
              <div 
                v-for="(report, index) in reportData" 
                :key="index"
                class="chart-label"
              >
                {{ report.pileNumber }}
              </div>
            </div>
          </div>
          
          <!-- 单个充电桩时显示详细信息卡片 -->
          <div v-if="reportData.length === 1" class="single-pile-stats">
            <div class="stat-item">
              <div class="stat-icon">⚡</div>
              <div class="stat-content">
                <div class="stat-value">{{ reportData[0].totalCharges }}</div>
                <div class="stat-label">累计充电次数</div>
              </div>
            </div>
            <div class="stat-item">
              <div class="stat-icon">⏱️</div>
              <div class="stat-content">
                <div class="stat-value">{{ reportData[0].totalHours }}h</div>
                <div class="stat-label">累计充电时长</div>
              </div>
            </div>
            <div class="stat-item">
              <div class="stat-icon">🔋</div>
              <div class="stat-content">
                <div class="stat-value">{{ reportData[0].totalEnergy }}度</div>
                <div class="stat-label">累计充电量</div>
              </div>
            </div>
            <div class="stat-item">
              <div class="stat-icon">💰</div>
              <div class="stat-content">
                <div class="stat-value">¥{{ reportData[0].totalFee }}</div>
                <div class="stat-label">累计总收入</div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onBeforeUnmount, watch } from 'vue'
import { useRouter } from 'vue-router'
import axios from 'axios'
import * as adminApi from '@/api/admin'

interface ChargingPile {
  id: number;
  name: string;
  isActive: boolean;
  isOccupied: boolean;
  statusText: string;
  totalCharges: number;
  totalHours: number;
  totalEnergy: number;
  queueCount: number;
}

interface WaitingCar {
  id: number;
  pileName: string;
  userId: string;
  batteryCapacity: number;
  requestedCharge: number;
  queueTime: string;
  status: string;
  statusClass: string;
}

interface ReportData {
  id: number;
  timeRange: string;
  pileName: string;
  pileNumber: string;
  totalCharges: number;
  totalHours: number;
  totalEnergy: number;
  chargeFee: string;
  serviceFee: string;
  totalFee: string;
}

const router = useRouter()
const username = ref('管理员')

// 充电桩统计数据
const chargingPiles = ref<ChargingPile[]>([])
const waitingVehicles = ref([])

// 核心数据指标
const activePiles = ref(0)
const totalPiles = ref(0)
const totalQueuedCars = ref(0)
const totalRevenue = ref('0.00')

// 报表数据
const reportTimeRange = ref('day')
const reportPileId = ref('all')
const showReport = ref(false)
const reportLoading = ref(false)
const reportData = ref<ReportData[]>([])
const chartType = ref('charges')

// 等候车辆数据
const loadingVehicles = ref(false)
const hasChargingVehicles = computed(() => 
  waitingVehicles.value && waitingVehicles.value.some(v => v.status === '充电中')
)

// 实时数据刷新
let refreshInterval: number | null = null

// 设置定时刷新功能
const setupRefreshInterval = () => {
  // 清除之前的定时器
  if (refreshInterval !== null) {
    clearInterval(refreshInterval)
  }
  
  // 设置新的定时器 - 每30秒刷新一次数据
  refreshInterval = window.setInterval(() => {
    fetchAdminStatistics()
    fetchWaitingVehicles()
  }, 30000) as unknown as number
}

// 组件卸载前清除定时器
onBeforeUnmount(() => {
  if (refreshInterval !== null) {
    clearInterval(refreshInterval)
  }
})

// 获取管理员仪表盘统计数据
const fetchAdminStatistics = async () => {
  try {
    const token = localStorage.getItem('token')
    if (!token) {
      router.push('/')
      return
    }

    const data = await adminApi.getAdminStatistics()

    activePiles.value = data.activePiles
    totalPiles.value = data.totalPiles
    totalQueuedCars.value = data.totalQueuedCars
    totalRevenue.value = data.totalRevenue.toFixed(2)
    
    // 更新充电桩列表
    chargingPiles.value = data.chargingPiles
  } catch (error) {
    console.error('获取管理员统计数据失败', error)
  }
}

// 获取等候车辆信息
const fetchWaitingVehicles = async () => {
  loadingVehicles.value = true
  try {
    // 获取等候区车辆（未分配充电桩的车辆）
    const waitingAreaResponse = await adminApi.getWaitingArea()
    const waitingAreaVehicles = waitingAreaResponse || []
    
    // 获取所有充电桩的车辆信息（包括充电中和已分配充电桩但在等待的车辆）
    const allVehicles = []
    
    // 添加等候区车辆
    waitingAreaVehicles.forEach(vehicle => {
      allVehicles.push({
        queue_number: vehicle.queue_number,
        user_name: vehicle.user_name,
        charging_mode: vehicle.charging_mode,
        requested_amount: vehicle.requested_amount,
        status: '等候区等候中',
        waiting_time: vehicle.waiting_time || 0,
        charging_time: 0,
        charged_amount: 0,
        progress_percent: 0,
        charging_pile: null
      })
    })
    
    // 获取每个充电桩的车辆信息
    for (const pile of chargingPiles.value) {
      try {
        const pileVehicles = await adminApi.getPileQueue(pile.id)
        if (pileVehicles && Array.isArray(pileVehicles)) {
          pileVehicles.forEach(vehicle => {
            if (vehicle.status === 'charging' || vehicle.is_charging) {
              // 正在充电的车辆
              allVehicles.push({
                queue_number: vehicle.queue_number,
                user_name: vehicle.user_name || `用户${vehicle.user_id}`,
                charging_mode: pile.name.includes('快充') ? 'FAST' : 'TRICKLE',
                requested_amount: vehicle.requested_amount,
                status: '充电中',
                waiting_time: 0,
                charging_time: vehicle.charging_time || vehicle.waiting_time || 0,
                charged_amount: vehicle.charged_amount || 0,
                progress_percent: vehicle.progress_percent || 0,
                charging_pile: pile.name
              })
            } else if (vehicle.status === 'waiting' && vehicle.charging_pile_id) {
              // 已分配充电桩但在排队的车辆
              allVehicles.push({
                queue_number: vehicle.queue_number,
                user_name: vehicle.user_name || `用户${vehicle.user_id}`,
                charging_mode: pile.name.includes('快充') ? 'FAST' : 'TRICKLE',
                requested_amount: vehicle.requested_amount,
                status: '充电区排队中',
                waiting_time: vehicle.waiting_time || 0,
                charging_time: 0,
                charged_amount: 0,
                progress_percent: 0,
                charging_pile: pile.name
              })
            }
          })
        }
      } catch (error) {
        console.warn(`获取充电桩 ${pile.id} 车辆信息失败:`, error)
      }
    }
    
    // 按状态和创建时间排序：充电中的在前，然后是充电区排队，最后是等候区
    allVehicles.sort((a, b) => {
      const statusOrder = { '充电中': 1, '充电区排队中': 2, '等候区等候中': 3 }
      return statusOrder[a.status] - statusOrder[b.status]
    })
    
    waitingVehicles.value = allVehicles
    
  } catch (error) {
    console.error('获取等候车辆信息失败', error)
    waitingVehicles.value = []
  } finally {
    loadingVehicles.value = false
  }
}

// 方法
const togglePileStatus = async (pileId: number) => {
  try {
    const pile = chargingPiles.value.find(p => p.id === pileId)
    
    if (!pile) return
    
    // 检查充电桩状态
    if (pile.isActive && pile.isOccupied) {
      alert('充电桩正在使用中，无法关闭！请等待充电完成后再试。')
      return
    }
    
    let confirmMessage = ''
    let successMessage = ''
    
    if (pile.isActive) {
      confirmMessage = `确定要关闭充电桩 ${pile.name} 吗？\n关闭后用户将无法使用此充电桩。`
      successMessage = '充电桩已成功关闭'
    } else {
      confirmMessage = `确定要启动充电桩 ${pile.name} 吗？\n启动后用户可以使用此充电桩进行充电。`
      successMessage = '充电桩已成功启动'
    }
    
    if (!confirm(confirmMessage)) {
      return
    }
    
    await adminApi.togglePileStatus(pileId)
    
    // 更新本地状态
    const wasActive = pile.isActive
    pile.isActive = !pile.isActive
    
    // 更新运行中充电桩数量
    if (wasActive && !pile.isActive) {
      // 从运行中变为关闭
      activePiles.value = Math.max(0, activePiles.value - 1)
    } else if (!wasActive && pile.isActive) {
      // 从关闭变为运行中
      activePiles.value += 1
    }
    
    alert(successMessage)
    
    // 重新获取最新数据以确保数据一致性
    setTimeout(() => {
      fetchAdminStatistics()
    }, 1000)
    
  } catch (error) {
    console.error('更新充电桩状态失败:', error)
    
    if (error.response && error.response.data && error.response.data.detail) {
      alert(`操作失败：${error.response.data.detail}`)
    } else {
      alert('操作失败，请稍后重试')
    }
  }
}

const viewPileDetails = (pileId: number) => {
  router.push(`/pile-details/${pileId}`)
}

const generateReport = async () => {
  try {
    reportLoading.value = true
    showReport.value = false
    
    // 生成日期范围
    const now = new Date()
    let startDate = new Date()
    let endDate = new Date()
    
    if (reportTimeRange.value === 'day') {
      startDate = new Date(now.getFullYear(), now.getMonth(), now.getDate(), 0, 0, 0)
      endDate = new Date(now.getFullYear(), now.getMonth(), now.getDate(), 23, 59, 59)
    } else if (reportTimeRange.value === 'week') {
      const day = now.getDay() || 7
      startDate = new Date(now.getFullYear(), now.getMonth(), now.getDate() - day + 1, 0, 0, 0)
      endDate = new Date(now.getFullYear(), now.getMonth(), now.getDate() + (7 - day), 23, 59, 59)
    } else {
      startDate = new Date(now.getFullYear(), now.getMonth(), 1, 0, 0, 0)
      endDate = new Date(now.getFullYear(), now.getMonth() + 1, 0, 23, 59, 59)
    }
    
    const token = localStorage.getItem('token')
    if (!token) {
      console.error('没有找到认证token')
      return
    }
    
    console.log('请求报表数据:', {
      start_date: startDate.toISOString(),
      end_date: endDate.toISOString(),
      pile_id: reportPileId.value === 'all' ? undefined : reportPileId.value
    })
    
    const response = await axios.get('/api/admin/report', {
      params: {
        start_date: startDate.toISOString(),
        end_date: endDate.toISOString(),
        pile_id: reportPileId.value === 'all' ? undefined : reportPileId.value
      },
      headers: {
        Authorization: `Bearer ${token}`
      }
    })
    
    console.log('报表API响应:', response.data)
    
    // 处理报表数据
    const reportStats = response.data.pile_statistics || {}
    const data: ReportData[] = []
    
    // 如果选择了特定充电桩，只显示该充电桩数据
    if (reportPileId.value !== 'all') {
      const pileId = reportPileId.value
      const stats = reportStats[pileId]
      const pile = chargingPiles.value.find(p => p.id === parseInt(pileId))
      
      if (pile && stats) {
        data.push({
          id: parseInt(pileId),
          timeRange: getTimeRangeLabel(),
          pileName: pile.name,
          pileNumber: pile.name.split(' ')[1] || pile.name, // 提取充电桩编号
          totalCharges: stats.charging_times || 0,
          totalHours: parseFloat((stats.total_duration || 0).toFixed(2)),
          totalEnergy: parseFloat((stats.total_amount || 0).toFixed(2)),
          chargeFee: (stats.total_electricity_fee || 0).toFixed(2),
          serviceFee: (stats.total_service_fee || 0).toFixed(2),
          totalFee: (stats.total_fee || 0).toFixed(2)
        })
      }
    } else {
      // 显示所有充电桩数据
      for (const pileId in reportStats) {
        const stats = reportStats[pileId]
        const pile = chargingPiles.value.find(p => p.id === parseInt(pileId))
        
        if (pile) {
          data.push({
            id: parseInt(pileId),
            timeRange: getTimeRangeLabel(),
            pileName: pile.name,
            pileNumber: pile.name.split(' ')[1] || pile.name, // 提取充电桩编号
            totalCharges: stats.charging_times || 0,
            totalHours: parseFloat((stats.total_duration || 0).toFixed(2)),
            totalEnergy: parseFloat((stats.total_amount || 0).toFixed(2)),
            chargeFee: (stats.total_electricity_fee || 0).toFixed(2),
            serviceFee: (stats.total_service_fee || 0).toFixed(2),
            totalFee: (stats.total_fee || 0).toFixed(2)
          })
        }
      }
    }
    
    // 按充电桩编号排序
    data.sort((a, b) => a.pileNumber.localeCompare(b.pileNumber))
    
    reportData.value = data
    showReport.value = true
    
    console.log('处理后的报表数据:', data)
    
  } catch (error) {
    console.error('生成报表失败:', error)
    showReport.value = false
    if (error.response) {
      console.error('错误响应:', error.response.data)
      alert(`生成报表失败: ${error.response.data.detail || error.message}`)
    } else {
      alert('生成报表失败，请检查网络连接后重试')
    }
  } finally {
    reportLoading.value = false
  }
}

// 监听筛选条件变化，自动重新生成报表
watch([reportTimeRange, reportPileId], () => {
  // 只有在充电桩数据加载完成后才生成报表
  if (chargingPiles.value.length > 0) {
    generateReport()
  }
}, { immediate: false })

// 总计计算函数
const getTotalCharges = () => {
  return reportData.value.reduce((sum, report) => sum + report.totalCharges, 0)
}

const getTotalHours = () => {
  return reportData.value.reduce((sum, report) => sum + report.totalHours, 0).toFixed(2)
}

const getTotalEnergy = () => {
  return reportData.value.reduce((sum, report) => sum + report.totalEnergy, 0).toFixed(2)
}

const getTotalChargeFee = () => {
  return reportData.value.reduce((sum, report) => sum + parseFloat(report.chargeFee), 0).toFixed(2)
}

const getTotalServiceFee = () => {
  return reportData.value.reduce((sum, report) => sum + parseFloat(report.serviceFee), 0).toFixed(2)
}

const getTotalFee = () => {
  return reportData.value.reduce((sum, report) => sum + parseFloat(report.totalFee), 0).toFixed(2)
}

// 生成报表标题
const getReportTitle = () => {
  const timeType = reportTimeRange.value === 'day' ? '日' : 
                   reportTimeRange.value === 'week' ? '周' : '月'
  const pileText = reportPileId.value === 'all' ? '全部充电桩' : 
                   chargingPiles.value.find(p => p.id == reportPileId.value)?.name || '充电桩'
  return `${pileText}${timeType}报表`
}

// 生成时间范围文本
const getDateRangeText = () => {
  const now = new Date()
  
  if (reportTimeRange.value === 'day') {
    return `${now.getFullYear()}年${now.getMonth() + 1}月${now.getDate()}日`
  } else if (reportTimeRange.value === 'week') {
    const day = now.getDay() || 7
    const startDate = new Date(now.getFullYear(), now.getMonth(), now.getDate() - day + 1)
    const endDate = new Date(now.getFullYear(), now.getMonth(), now.getDate() + (7 - day))
    return `${startDate.getFullYear()}年${startDate.getMonth() + 1}月${startDate.getDate()}日 - ${endDate.getFullYear()}年${endDate.getMonth() + 1}月${endDate.getDate()}日`
  } else {
    return `${now.getFullYear()}年${now.getMonth() + 1}月`
  }
}

const getTimeRangeLabel = () => {
  const now = new Date()
  if (reportTimeRange.value === 'day') {
    return `${now.getFullYear()}-${now.getMonth() + 1}-${now.getDate()}`
  } else if (reportTimeRange.value === 'week') {
    return `${now.getFullYear()}年第${Math.ceil(now.getDate() / 7)}周`
  } else {
    return `${now.getFullYear()}-${now.getMonth() + 1}`
  }
}

const getBarHeight = (report: ReportData) => {
  let value = 0
  let maxValue = 1 // 防止除零错误，设置最小值为1
  
  if (chartType.value === 'charges') {
    value = report.totalCharges
    if (reportData.value.length === 1) {
      // 单个充电桩时，使用固定高度百分比
      maxValue = Math.max(value, 1)
      return value > 0 ? '80%' : '10%'
    } else {
      maxValue = Math.max(...reportData.value.map(r => r.totalCharges), 1)
    }
  } else if (chartType.value === 'energy') {
    value = report.totalEnergy
    if (reportData.value.length === 1) {
      return value > 0 ? '80%' : '10%'
    } else {
      maxValue = Math.max(...reportData.value.map(r => r.totalEnergy), 1)
    }
  } else {
    value = parseFloat(report.totalFee)
    if (reportData.value.length === 1) {
      return value > 0 ? '80%' : '10%'
    } else {
      maxValue = Math.max(...reportData.value.map(r => parseFloat(r.totalFee)), 1)
    }
  }
  
  // 确保最小高度为10%，最大高度为90%
  const percentage = Math.max(10, Math.min(90, (value / maxValue * 80) + 10))
  return `${percentage}%`
}

const getChartValue = (report: ReportData) => {
  if (chartType.value === 'charges') {
    return report.totalCharges
  } else if (chartType.value === 'energy') {
    return `${report.totalEnergy}度`
  } else {
    return `¥${report.totalFee}`
  }
}

const logout = () => {
  // 清除登录状态
  localStorage.removeItem('currentUser')
  localStorage.removeItem('token')
  router.push('/')
}

// 格式化时间（处理小时或分钟）
const formatTime = (timeValue) => {
  if (!timeValue || timeValue === 0) return '0分钟'
  
  // 如果时间值小于1，认为是小时，转换为分钟
  if (timeValue < 1) {
    const minutes = Math.round(timeValue * 60)
    return `${minutes}分钟`
  }
  
  // 如果时间值大于1但小于24，可能是小时
  if (timeValue < 24) {
    const hours = Math.floor(timeValue)
    const minutes = Math.round((timeValue - hours) * 60)
    if (hours > 0) {
      return `${hours}小时${minutes > 0 ? `${minutes}分钟` : ''}`
    }
    return `${minutes}分钟`
  }
  
  // 如果时间值很大，可能是分钟
  const hours = Math.floor(timeValue / 60)
  const minutes = Math.round(timeValue % 60)
  if (hours > 0) {
    return `${hours}小时${minutes > 0 ? `${minutes}分钟` : ''}`
  }
  return `${minutes}分钟`
}

onMounted(async () => {
  // 从本地存储获取用户信息
  const userJson = localStorage.getItem('currentUser')
  if (userJson) {
    try {
      const user = JSON.parse(userJson)
      username.value = user.username
    } catch (e) {
      console.error('解析用户信息失败', e)
    }
  }
  
  // 初始化加载数据 - 先获取充电桩数据，再获取车辆数据
  try {
    await fetchAdminStatistics()
    await fetchWaitingVehicles()
    
    // 充电桩数据加载完成后，自动生成初始报表
    if (chargingPiles.value.length > 0) {
      await generateReport()
    }
  } catch (error) {
    console.error('初始化数据加载失败:', error)
  }
  
  // 设置定时刷新
  setupRefreshInterval()
})
</script>

<style scoped>
:root {
  --admin-primary-color: #1976d2;
  --admin-primary-light: rgba(25, 118, 210, 0.1);
  --admin-primary-dark: #1565c0;
  --card-shadow: 0 4px 12px rgba(0, 0, 0, 0.05);
  --card-hover-shadow: 0 8px 20px rgba(0, 0, 0, 0.08);
  --transition-time: 0.3s;
  --green-color: #4caf50;
  --red-color: #f44336;
  --orange-color: #ff9800;
  --blue-color: #2196f3;
  --light-text: #757575;
  --text-color: #333333;
  --border-color: #e0e0e0;
  --section-bg: white;
  --body-bg: #f9fafc;
}

/* 全局背景 */
body {
  margin: 0;
  padding: 0;
  background-color: var(--body-bg);
  color: var(--text-color);
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen,
    Ubuntu, Cantarell, 'Open Sans', 'Helvetica Neue', sans-serif;
}

html, body {
  height: 100%;
  width: 100%;
  overflow-x: hidden;
}

.admin-dashboard-container {
  max-width: 1400px;
  margin: 0 auto;
  padding: 2rem;
  min-height: 100vh;
  display: flex;
  flex-direction: column;
  gap: 2rem;
}

/* 顶部信息栏 */
.dashboard-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 1rem;
  padding-bottom: 1.5rem;
  border-bottom: 1px solid rgba(0, 0, 0, 0.05);
}

.header-left {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.dashboard-header h1 {
  font-size: 1.8rem;
  color: var(--text-color);
  margin: 0;
  font-weight: 600;
  letter-spacing: -0.5px;
}

.greeting {
  font-size: 1rem;
  color: var(--light-text);
}

.user-highlight {
  color: var(--admin-primary-color);
  font-weight: 500;
}

.user-info {
  display: flex;
  align-items: center;
  gap: 1rem;
}

.user-avatar {
  width: 2.8rem;
  height: 2.8rem;
  border-radius: 50%;
  background-color: var(--admin-primary-color);
  color: white;
  display: flex;
  justify-content: center;
  align-items: center;
  font-size: 1.2rem;
  font-weight: 500;
  box-shadow: 0 2px 10px rgba(25, 118, 210, 0.3);
}

.logout-btn {
  background-color: transparent;
  border: 1px solid var(--border-color);
  color: var(--light-text);
  padding: 0.6rem 1.2rem;
  border-radius: 0.5rem;
  font-size: 0.9rem;
  cursor: pointer;
  transition: all var(--transition-time);
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.logout-icon {
  font-size: 1.2rem;
}

.logout-btn:hover {
  background-color: rgba(0, 0, 0, 0.03);
  color: var(--text-color);
  border-color: var(--admin-primary-color);
}

/* 核心指标卡片 */
.dashboard-stats {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
  gap: 1.5rem;
  margin-bottom: 1rem;
}

.stat-card {
  background-color: var(--section-bg);
  border-radius: 1rem;
  padding: 1.5rem;
  box-shadow: var(--card-shadow);
  display: flex;
  align-items: center;
  gap: 1.2rem;
  transition: all var(--transition-time);
  border-bottom: 3px solid transparent;
}

.stat-card:nth-child(1) {
  border-bottom-color: var(--blue-color);
}

.stat-card:nth-child(2) {
  border-bottom-color: var(--orange-color);
}

.stat-card:nth-child(3) {
  border-bottom-color: var(--green-color);
}

.stat-card:hover {
  transform: translateY(-5px);
  box-shadow: var(--card-hover-shadow);
}

.stat-icon {
  width: 3.2rem;
  height: 3.2rem;
  border-radius: 1rem;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 1.6rem;
  flex-shrink: 0;
}

.pile-icon {
  background-color: rgba(33, 150, 243, 0.1);
  color: var(--blue-color);
}

.pile-icon::before {
  content: "🔌";
}

.queue-icon {
  background-color: rgba(255, 152, 0, 0.1);
  color: var(--orange-color);
}

.queue-icon::before {
  content: "🚗";
}

.revenue-icon {
  background-color: rgba(76, 175, 80, 0.1);
  color: var(--green-color);
}

.revenue-icon::before {
  content: "¥";
}

.stat-content {
  flex: 1;
}

.stat-value {
  font-size: 1.5rem;
  font-weight: 600;
  margin-bottom: 0.2rem;
  color: var(--text-color);
}

.stat-label {
  font-size: 0.9rem;
  color: var(--light-text);
}

/* 主要内容布局 */
.dashboard-main {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 2rem;
  margin-bottom: 1rem;
}

.dashboard-column {
  display: flex;
  flex-direction: column;
  gap: 2rem;
}

.dashboard-section {
  background-color: var(--section-bg);
  border-radius: 1rem;
  padding: 1.5rem;
  box-shadow: var(--card-shadow);
}

.full-width {
  grid-column: 1 / -1;
}

/* 区域标题 */
.section-title {
  margin-bottom: 1.5rem;
}

.section-title h2 {
  font-size: 1.3rem;
  color: var(--text-color);
  margin: 0 0 0.5rem 0;
  font-weight: 600;
  display: flex;
  align-items: center;
}

.section-title h2::before {
  content: "";
  display: inline-block;
  width: 4px;
  height: 1em;
  background-color: var(--admin-primary-color);
  margin-right: 10px;
  border-radius: 2px;
}

.subtitle {
  font-size: 0.9rem;
  color: var(--light-text);
}

/* 充电桩管理 */
.pile-management {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(250px, 1fr));
  gap: 1.5rem;
}

.pile-card {
  background-color: white;
  border-radius: 1rem;
  padding: 1.5rem;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.05);
  transition: all var(--transition-time);
  border: 2px solid transparent;
  position: relative;
  overflow: hidden;
}

.pile-card::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 6px;
  background-color: var(--admin-primary-color);
  opacity: 0.2;
  transition: opacity var(--transition-time);
}

.pile-card:hover {
  transform: translateY(-3px);
  box-shadow: var(--card-hover-shadow);
  border-color: rgba(25, 118, 210, 0.2);
}

.pile-card:hover::before {
  opacity: 1;
}

.status-active:hover::before {
  background-color: var(--green-color);
}

.status-inactive:hover::before {
  background-color: var(--red-color);
}

.pile-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 1.2rem;
}

.pile-header h3 {
  font-size: 1.1rem;
  margin: 0;
  color: var(--text-color);
  font-weight: 600;
}

.pile-status {
  padding: 0.3rem 0.8rem;
  border-radius: 50px;
  font-size: 0.8rem;
  font-weight: 500;
  display: flex;
  align-items: center;
  gap: 0.3rem;
}

.status-icon {
  font-size: 0.9rem;
}

.status-active {
  background-color: rgba(76, 175, 80, 0.1);
  color: var(--green-color);
}

.status-inactive {
  background-color: rgba(244, 67, 54, 0.1);
  color: var(--red-color);
}

.status-occupied {
  background-color: rgba(255, 152, 0, 0.1);
  color: var(--orange-color);
}

/* 队列信息 */
.pile-queue-info {
  padding: 0.5rem 1rem;
  margin: 0.5rem 0;
  background-color: rgba(255, 193, 7, 0.1);
  border-radius: 0.5rem;
  border-left: 3px solid #ffc107;
}

.queue-indicator {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  font-size: 0.8rem;
  color: #e65100;
}

.queue-icon {
  font-size: 1rem;
}

.queue-text {
  font-weight: 500;
}

.pile-stats {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 1rem;
  margin-bottom: 1.5rem;
  padding: 1rem;
  background-color: rgba(0, 0, 0, 0.02);
  border-radius: 0.8rem;
}

.pile-stat {
  text-align: center;
}

.pile-stat .stat-label {
  font-size: 0.75rem;
  color: var(--light-text);
  margin-bottom: 0.3rem;
}

.pile-stat .stat-value {
  font-size: 1.1rem;
  font-weight: 600;
  color: var(--text-color);
}

.pile-footer {
  display: flex;
  gap: 1rem;
  align-items: center;
}

.pile-actions {
  flex: 1;
}

/* 基础按钮样式 */
.toggle-button, .view-button {
  padding: 0.7rem 0;
  border-radius: 0.5rem;
  font-size: 0.9rem;
  font-weight: 500;
  cursor: pointer;
  flex: 1;
  text-align: center;
  border: none;
  
  /* 默认隐藏 */
  opacity: 0;
  transform: translateY(10px);
  transition: opacity 0.3s ease, transform 0.3s ease, background-color 0.3s ease;
}

/* 鼠标悬停在卡片上时显示按钮 */
.pile-card:hover .toggle-button,
.pile-card:hover .view-button {
  opacity: 1;
  transform: translateY(0);
}

/* 关闭按钮 */
.stop-button {
  background-color: var(--red-color);
  color: white;
}

.stop-button:hover:not(:disabled) {
  background-color: #e53935;
}

/* 启动按钮 */
.start-button {
  background-color: var(--green-color);
  color: white;
}

.start-button:hover:not(:disabled) {
  background-color: #43a047;
}

/* 禁用按钮 */
.disabled-button {
  background-color: #9e9e9e;
  color: #616161;
  cursor: not-allowed;
  opacity: 0.7;
}

.disabled-button:disabled {
  opacity: 1;
  transform: translateY(0);
}

.pile-card:hover .disabled-button:disabled {
  opacity: 0.7;
  background-color: #9e9e9e;
}

/* 查看详情按钮 */
.view-button {
  background-color: var(--admin-primary-light);
  color: var(--admin-primary-color);
  min-width: 80px;
}

.view-button:hover {
  background-color: rgba(25, 118, 210, 0.2);
}

/* 等待队列表格 */
.waiting-queue {
  height: 100%;
}

.table-responsive {
  overflow-x: auto;
  background-color: white;
  border-radius: 0.8rem;
  max-height: 400px;
  overflow-y: auto;
}

.queue-table, .report-table {
  width: 100%;
  border-collapse: collapse;
  text-align: left;
}

.queue-table th, .report-table th {
  padding: 1rem;
  background-color: rgba(0, 0, 0, 0.02);
  font-weight: 600;
  color: var(--text-color);
  font-size: 0.9rem;
  border-bottom: 1px solid var(--border-color);
  position: sticky;
  top: 0;
  z-index: 1;
}

.queue-table td, .report-table td {
  padding: 1rem;
  border-bottom: 1px solid var(--border-color);
  color: var(--text-color);
  font-size: 0.9rem;
}

.queue-table tr:last-child td, .report-table tr:last-child td {
  border-bottom: none;
}

.queue-table tr:hover, .report-table tr:hover {
  background-color: rgba(0, 0, 0, 0.01);
}

.status-tag {
  padding: 0.3rem 0.8rem;
  border-radius: 50px;
  font-size: 0.8rem;
  font-weight: 500;
  display: inline-block;
}

.status-waiting {
  background-color: rgba(255, 152, 0, 0.1);
  color: var(--orange-color);
}

.status-charging {
  background-color: rgba(76, 175, 80, 0.1);
  color: var(--green-color);
}

.status-waiting-area {
  background-color: rgba(33, 150, 243, 0.1);
  color: var(--blue-color);
}

.status-completed {
  background-color: rgba(33, 150, 243, 0.1);
  color: var(--blue-color);
}

.status-cancelled {
  background-color: #f8d7da;
  color: #721c24;
}

/* 报表展示 */
.report-section {
  display: flex;
  flex-direction: column;
  gap: 1.5rem;
}

.report-filters {
  display: flex;
  flex-wrap: wrap;
  gap: 1.5rem;
  background-color: rgba(0, 0, 0, 0.02);
  border-radius: 0.8rem;
  padding: 1.2rem;
}

.filter-group {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.filter-group label {
  font-size: 0.9rem;
  color: var(--light-text);
  font-weight: 500;
}

.filter-group select {
  padding: 0.7rem 1rem;
  border: 1px solid var(--border-color);
  border-radius: 0.5rem;
  font-size: 0.9rem;
  background-color: white;
  min-width: 150px;
}

.filter-status {
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.loading-indicator {
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.loading-spinner {
  width: 20px;
  height: 20px;
  border: 2px solid rgba(0, 0, 0, 0.1);
  border-radius: 50%;
  border-top-color: var(--admin-primary-color);
  animation: spin 1s linear infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

.report-ready {
  padding: 0.5rem 1rem;
  background-color: var(--green-color);
  color: white;
  border-radius: 0.5rem;
  font-size: 0.9rem;
  font-weight: 500;
}

/* 图表区域 */
.chart-container {
  margin-top: 1rem;
  background-color: rgba(0, 0, 0, 0.02);
  border-radius: 0.8rem;
  padding: 1.5rem;
}

.chart-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 1.5rem;
  flex-wrap: wrap;
  gap: 1rem;
}

.chart-header h3 {
  font-size: 1.1rem;
  margin: 0;
  color: var(--text-color);
  font-weight: 600;
}

.chart-subtitle {
  font-size: 0.9rem;
  color: var(--light-text);
  font-style: italic;
}

.chart-selector {
  display: flex;
  gap: 0.5rem;
}

.chart-type-btn {
  padding: 0.5rem 1rem;
  border: 1px solid var(--border-color);
  background-color: white;
  border-radius: 0.5rem;
  font-size: 0.9rem;
  cursor: pointer;
  transition: all 0.2s;
}

.chart-type-btn.active {
  background-color: var(--admin-primary-color);
  color: white;
  border-color: var(--admin-primary-color);
}

.chart-placeholder {
  height: 300px;
  display: flex;
  flex-direction: column;
}

.chart-bars {
  flex: 1;
  display: flex;
  justify-content: space-around;
  align-items: flex-end;
  gap: 1rem;
  padding: 0 1rem;
}

.chart-bars.single-bar {
  justify-content: center;
  padding: 0 2rem;
}

.chart-bar {
  flex: 1;
  background: linear-gradient(135deg, var(--admin-primary-color), var(--admin-primary-dark));
  border-radius: 4px 4px 0 0;
  min-height: 20px;
  max-width: 80px;
  display: flex;
  justify-content: center;
  position: relative;
  transition: all 0.5s ease;
  box-shadow: 0 2px 8px rgba(25, 118, 210, 0.3);
}

.chart-bar.single-bar-item {
  max-width: 120px;
  background: linear-gradient(135deg, var(--green-color), #43a047);
  box-shadow: 0 4px 12px rgba(76, 175, 80, 0.4);
}

.chart-bar:hover {
  transform: translateY(-5px);
  box-shadow: 0 6px 16px rgba(25, 118, 210, 0.4);
}

.chart-bar.single-bar-item:hover {
  box-shadow: 0 8px 20px rgba(76, 175, 80, 0.5);
}

.bar-value {
  position: absolute;
  top: -25px;
  font-size: 0.8rem;
  font-weight: 600;
  color: var(--text-color);
  background-color: white;
  padding: 2px 6px;
  border-radius: 4px;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
}

.chart-labels {
  height: 30px;
  display: flex;
  justify-content: space-around;
  margin-top: 10px;
}

.chart-label {
  flex: 1;
  text-align: center;
  font-size: 0.8rem;
  color: var(--light-text);
  padding: 0.5rem 0;
  font-weight: 500;
}

/* 单个充电桩统计卡片 */
.single-pile-stats {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 1rem;
  margin-top: 2rem;
  padding-top: 1.5rem;
  border-top: 1px solid var(--border-color);
}

.stat-item {
  display: flex;
  align-items: center;
  gap: 1rem;
  padding: 1rem;
  background-color: white;
  border-radius: 0.8rem;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.05);
  transition: all 0.3s ease;
}

.stat-item:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.08);
}

.stat-icon {
  font-size: 2rem;
  width: 3rem;
  height: 3rem;
  display: flex;
  align-items: center;
  justify-content: center;
  background-color: var(--admin-primary-light);
  border-radius: 50%;
  flex-shrink: 0;
}

.stat-content {
  flex: 1;
}

.stat-value {
  font-size: 1.2rem;
  font-weight: 600;
  color: var(--text-color);
  margin-bottom: 0.25rem;
}

.stat-label {
  font-size: 0.8rem;
  color: var(--light-text);
}

/* 响应式适配 */
@media (max-width: 992px) {
  .dashboard-main {
    grid-template-columns: 1fr;
  }
  
  .chart-header {
    flex-direction: column;
    align-items: flex-start;
    gap: 1rem;
  }
  
  .single-pile-stats {
    grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
  }
}

@media (max-width: 768px) {
  .admin-dashboard-container {
    padding: 1.5rem;
  }
  
  .dashboard-header {
    flex-direction: column;
    align-items: flex-start;
    gap: 1rem;
  }
  
  .user-info {
    width: 100%;
    justify-content: space-between;
  }
  
  .dashboard-stats, .pile-management {
    grid-template-columns: 1fr;
  }
  
  .pile-stats {
    grid-template-columns: 1fr;
  }
  
  .pile-footer {
    flex-direction: column;
  }
  
  .report-filters {
    flex-direction: column;
  }
  
  .chart-header {
    flex-direction: column;
    gap: 1rem;
    align-items: flex-start;
  }
  
  .chart-selector {
    width: 100%;
    justify-content: center;
  }
  
  .chart-bars.single-bar {
    padding: 0 1rem;
  }
  
  .single-pile-stats {
    grid-template-columns: 1fr;
  }
  
  .stat-item {
    flex-direction: column;
    text-align: center;
    gap: 0.5rem;
  }
}

/* 动画效果 */
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

.dashboard-section {
  animation: fadeIn 0.5s ease-out forwards;
}

/* 等候车辆样式 */
.refresh-btn {
  background: transparent;
  border: 1px solid var(--border-color);
  border-radius: 4px;
  padding: 5px 10px;
  font-size: 0.8rem;
  color: var(--light-text);
  cursor: pointer;
  display: flex;
  align-items: center;
  gap: 5px;
  transition: all 0.3s;
  position: absolute;
  top: 0;
  right: 0;
}

.refresh-btn:hover {
  color: var(--admin-primary-color);
  border-color: var(--admin-primary-color);
  background-color: rgba(25, 118, 210, 0.05);
}

.section-title {
  position: relative;
}

.loading-info, .no-data-info {
  padding: 40px;
  text-align: center;
  background: rgba(0, 0, 0, 0.02);
  border-radius: 8px;
}

.loading-spinner {
  width: 40px;
  height: 40px;
  border: 3px solid rgba(0, 0, 0, 0.1);
  border-radius: 50%;
  border-top-color: var(--admin-primary-color);
  margin: 0 auto 15px;
  animation: spin 1s linear infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

.progress-bar {
  width: 100%;
  height: 8px;
  background-color: #e9ecef;
  border-radius: 4px;
  overflow: hidden;
  margin-bottom: 5px;
}

.progress-filled {
  height: 100%;
  background-color: var(--green-color);
  border-radius: 4px;
}

.progress-text {
  font-size: 0.8rem;
  color: var(--light-text);
  text-align: center;
}

.status-charging {
  background-color: rgba(76, 175, 80, 0.1);
  color: var(--green-color);
}

.status-waiting {
  background-color: rgba(255, 152, 0, 0.1);
  color: var(--orange-color);
}

.status-waiting-area {
  background-color: rgba(33, 150, 243, 0.1);
  color: var(--blue-color);
}

.status-completed {
  background-color: rgba(33, 150, 243, 0.1);
  color: var(--blue-color);
}

.status-occupied {
  background-color: rgba(255, 152, 0, 0.1);
  color: var(--orange-color);
}

/* 报表表格样式 */
.report-summary {
  margin-bottom: 1.5rem;
  padding-bottom: 1rem;
  border-bottom: 1px solid var(--border-color);
}

.report-summary h4 {
  margin: 0 0 0.5rem 0;
  font-size: 1.3rem;
  color: var(--admin-primary-color);
  font-weight: 600;
}

.report-subtitle {
  margin: 0;
  color: var(--light-text);
  font-size: 0.9rem;
}

.report-table {
  width: 100%;
  border-collapse: collapse;
  text-align: left;
  margin-top: 1rem;
}

.report-table th {
  padding: 1rem;
  background-color: rgba(25, 118, 210, 0.05);
  font-weight: 600;
  color: var(--text-color);
  font-size: 0.9rem;
  border-bottom: 2px solid var(--admin-primary-color);
  position: sticky;
  top: 0;
  z-index: 1;
  text-align: center;
}

.report-table td {
  padding: 1rem;
  border-bottom: 1px solid var(--border-color);
  color: var(--text-color);
  font-size: 0.9rem;
  text-align: center;
}

.report-table tr:hover {
  background-color: rgba(0, 0, 0, 0.02);
}

.report-table .summary-row {
  background-color: rgba(25, 118, 210, 0.1);
  font-weight: 600;
  border-top: 2px solid var(--admin-primary-color);
}

.report-table .summary-row td {
  padding: 1.2rem 1rem;
  color: var(--admin-primary-color);
  border-bottom: none;
}

.report-table .summary-row:hover {
  background-color: rgba(25, 118, 210, 0.15);
}

/* 空数据提示 */
.no-report-data {
  text-align: center;
  padding: 3rem;
  color: var(--light-text);
  font-size: 1rem;
}

.no-report-data .empty-icon {
  font-size: 3rem;
  margin-bottom: 1rem;
  color: #ccc;
}
</style> 