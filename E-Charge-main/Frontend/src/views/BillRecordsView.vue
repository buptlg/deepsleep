<template>
  <div class="bill-records-container">
    <div class="page-header">
      <h1>充电详单</h1>
      <button class="back-btn" @click="goBack">返回</button>
    </div>

    <div class="filter-card">
      <div class="filters">
        <div class="filter-item">
          <label for="dateRange">时间范围</label>
          <select id="dateRange" v-model="dateRange" @change="applyFilters" class="select-input">
            <option value="all">全部时间</option>
            <option value="today">今天</option>
            <option value="week">本周</option>
            <option value="month">本月</option>
            <option value="custom">自定义范围</option>
          </select>
        </div>
        
        <div class="filter-item">
          <label for="chargingPile">充电桩</label>
          <select id="chargingPile" v-model="selectedPile" @change="applyFilters" class="select-input">
            <option value="all">全部充电桩</option>
            <option value="fast">快充桩</option>
            <option value="slow">慢充桩</option>
          </select>
        </div>
        
        <div class="filter-item">
          <label for="sortOrder">排序方式</label>
          <select id="sortOrder" v-model="sortOrder" @change="applyFilters" class="select-input">
            <option value="newest">时间最新</option>
            <option value="oldest">时间最早</option>
            <option value="costHigh">费用从高到低</option>
            <option value="costLow">费用从低到高</option>
          </select>
        </div>
      </div>
    </div>

    <div v-if="loading" class="loading-container">
      <div class="loading-spinner"></div>
      <p>加载中...</p>
    </div>

    <div v-else-if="!records.length" class="no-data-container">
      <div class="no-data-icon">📋</div>
      <h3>暂无充电记录</h3>
      <p>您还没有完成的充电记录。</p>
    </div>

    <div v-else class="records-section">
      <div class="summary-card">
        <div class="summary-item">
          <div class="summary-label">总充电次数</div>
          <div class="summary-value">{{ summary.totalCount }}</div>
        </div>
        <div class="summary-item">
          <div class="summary-label">总充电量</div>
          <div class="summary-value">{{ summary.totalAmount }} 度</div>
        </div>
        <div class="summary-item">
          <div class="summary-label">总费用</div>
          <div class="summary-value">{{ summary.totalCost }} 元</div>
        </div>
      </div>

      <div v-for="record in pageRecords" :key="record.id" class="record-card">
        <div class="record-header">
          <div class="record-id">详单编号: {{ record.id }}</div>
          <div class="record-status" :class="getStatusClass(record.status)">
            {{ getStatusText(record.status) }}
          </div>
        </div>
        
        <div class="record-body">
          <div class="record-column">
            <div class="record-item">
              <div class="record-label">充电桩</div>
              <div class="record-value">{{ record.pileName }}</div>
            </div>
            <div class="record-item">
              <div class="record-label">充电量</div>
              <div class="record-value">{{ record.chargeAmount }} 度</div>
            </div>
            <div class="record-item">
              <div class="record-label">充电时长</div>
              <div class="record-value">{{ record.chargeDuration }}</div>
            </div>
          </div>
          
          <div class="record-column">
            <div class="record-item">
              <div class="record-label">启动时间</div>
              <div class="record-value">{{ formatDate(record.startTime) }}</div>
            </div>
            <div class="record-item">
              <div class="record-label">停止时间</div>
              <div class="record-value">{{ formatDate(record.endTime) }}</div>
            </div>
            <div class="record-item">
              <div class="record-label">充电费用</div>
              <div class="record-value">{{ record.chargeCost }} 元</div>
            </div>
            <div class="record-item">
              <div class="record-label">服务费用</div>
              <div class="record-value">{{ record.serviceCost }} 元</div>
            </div>
          </div>
        </div>
        
        <div class="record-footer">
          <div class="total-cost">
            总费用: <span class="cost-value">{{ record.totalCost }}</span> 元
          </div>
          <button class="detail-btn" @click="viewDetail(record)">查看详情</button>
        </div>
      </div>
      
      <div class="pagination">
        <button 
          class="page-btn" 
          :disabled="currentPage === 1"
          @click="changePage(currentPage - 1)"
        >
          上一页
        </button>
        
        <div class="page-info">
          {{ currentPage }} / {{ totalPages }}
        </div>
        
        <button 
          class="page-btn" 
          :disabled="currentPage === totalPages"
          @click="changePage(currentPage + 1)"
        >
          下一页
        </button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, watch } from 'vue'
import { useRouter } from 'vue-router'
import axios from 'axios'

const router = useRouter()
const loading = ref(true)

// 筛选条件
const dateRange = ref('all')
const selectedPile = ref('all')
const sortOrder = ref('newest')

// 分页
const currentPage = ref(1)
const totalPages = ref(1)
const pageSize = 5

// 统计数据
const summary = ref({
  totalCount: 0,
  totalAmount: 0,
  totalCost: 0,
})

// 原始数据和处理后的数据
const rawRecords = ref<BillRecord[]>([])
const records = ref<BillRecord[]>([])

// 详单记录
interface BillRecord {
  id: number
  pileName?: string
  charging_pile_id: number
  request_id: number
  chargeAmount?: number
  charging_amount: number
  chargeDuration?: string
  charging_duration: number
  createdAt?: string
  start_time: string
  end_time: string
  chargeCost?: number
  electricity_fee: number
  serviceCost?: number
  service_fee: number
  totalCost?: number
  total_fee: number
  status?: 'completed' | 'interrupted' | 'cancelled'
  pileType?: string
}

const formattedRecords = computed(() => {
  return records.value.map(record => {
    // 将小时转为"小时分钟"格式
    const hours = Math.floor(record.charging_duration)
    const minutes = Math.round((record.charging_duration - hours) * 60)
    const durationText = `${hours}小时${minutes}分钟`
    
    return {
      ...record,
      id: record.id,
      pileName: record.pileName || `充电桩 ${record.charging_pile_id}`,
      chargeAmount: record.charging_amount,
      chargeDuration: durationText,
      startTime: record.start_time,
      endTime: record.end_time,
      chargeCost: record.electricity_fee,
      serviceCost: record.service_fee,
      totalCost: record.total_fee,
      status: 'completed' // 默认为已完成状态
    }
  })
})

// 获取原始数据
const fetchRawData = async () => {
  loading.value = true
  
  try {
    const token = localStorage.getItem('token')
    if (!token) {
      router.push('/')
      return
    }

    const response = await axios.get('/api/charging/details', {
      headers: {
        Authorization: `Bearer ${token}`
      }
    })
    
    // 获取充电桩信息
    const pilesResponse = await axios.get('/api/charging/piles', {
      headers: {
        Authorization: `Bearer ${token}`
      }
    })
    
    const piles = pilesResponse.data
    
    // 处理原始数据 - 添加充电桩信息
    const chargeRecords = response.data.map((record: any) => {
      const pile = piles.find((p: any) => p.id === record.charging_pile_id)
      return {
        ...record,
        pileName: pile ? pile.pile_number : `充电桩 ${record.charging_pile_id}`,
        pileType: pile ? pile.charging_mode : null
      }
    })
    
    rawRecords.value = chargeRecords
    
    // 应用筛选
    applyFilters()
    
  } catch (error) {
    console.error('获取详单记录失败:', error)
  } finally {
    loading.value = false
  }
}

// 应用筛选逻辑
const applyFilters = () => {
  if (rawRecords.value.length === 0) {
    records.value = []
    return
  }
  
  let filteredRecords = [...rawRecords.value]
  
  // 根据充电桩类型过滤数据
  if (selectedPile.value !== 'all') {
    filteredRecords = filteredRecords.filter((record: any) => {
      if (selectedPile.value === 'fast') {
        return record.pileType === 'FAST' || record.pileType === 'fast'
      } else if (selectedPile.value === 'slow') {
        return record.pileType === 'TRICKLE' || record.pileType === 'trickle'
      }
      return true
    })
  }
  
  // 根据日期范围过滤
  if (dateRange.value !== 'all') {
    const now = new Date()
    let startDate: Date
    
    if (dateRange.value === 'today') {
      startDate = new Date(now.getFullYear(), now.getMonth(), now.getDate())
    } else if (dateRange.value === 'week') {
      const dayOfWeek = now.getDay() || 7 // 将周日调整为7
      startDate = new Date(now)
      startDate.setDate(now.getDate() - (dayOfWeek - 1))
      startDate.setHours(0, 0, 0, 0)
    } else if (dateRange.value === 'month') {
      startDate = new Date(now.getFullYear(), now.getMonth(), 1)
    } else {
      startDate = new Date(0) // 1970年，默认日期
    }
    
    filteredRecords = filteredRecords.filter((record: any) => {
      const recordDate = new Date(record.end_time)
      return recordDate >= startDate && recordDate <= now
    })
  }
  
  // 应用排序
  if (sortOrder.value === 'newest') {
    filteredRecords.sort((a: any, b: any) => new Date(b.end_time).getTime() - new Date(a.end_time).getTime())
  } else if (sortOrder.value === 'oldest') {
    filteredRecords.sort((a: any, b: any) => new Date(a.end_time).getTime() - new Date(b.end_time).getTime())
  } else if (sortOrder.value === 'costHigh') {
    filteredRecords.sort((a: any, b: any) => b.total_fee - a.total_fee)
  } else if (sortOrder.value === 'costLow') {
    filteredRecords.sort((a: any, b: any) => a.total_fee - b.total_fee)
  }
  
  records.value = filteredRecords
  
  // 计算统计数据
  calculateSummary()
  
  // 重置到第一页并设置分页
  currentPage.value = 1
  totalPages.value = Math.ceil(records.value.length / pageSize)
}

const calculateSummary = () => {
  let totalAmount = 0
  let totalCost = 0
  
  records.value.forEach(record => {
    totalAmount += record.charging_amount
    totalCost += record.total_fee
  })
  
  summary.value = {
    totalCount: records.value.length,
    totalAmount: totalAmount,
    totalCost: totalCost
  }
}

// 状态展示
const getStatusText = (status: string) => {
  switch (status) {
    case 'completed': return '已完成'
    case 'interrupted': return '中断'
    case 'cancelled': return '已取消'
    default: return '已完成'
  }
}

const getStatusClass = (status: string) => {
  switch (status) {
    case 'completed': return 'status-completed'
    case 'interrupted': return 'status-interrupted'
    case 'cancelled': return 'status-cancelled'
    default: return 'status-completed'
  }
}

// 格式化日期
const formatDate = (dateString: string) => {
  try {
    if (!dateString) return "未知时间";
    
    // 尝试创建日期对象
    const date = new Date(dateString);
    
    // 检查日期是否有效
    if (isNaN(date.getTime())) {
      console.warn("无效的日期格式:", dateString);
      return "格式错误";
    }
    
    return date.toLocaleString('zh-CN', {
      year: 'numeric',
      month: '2-digit',
      day: '2-digit',
      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit'
    });
  } catch (e) {
    console.error("日期格式化错误:", e, dateString);
    return "日期错误";
  }
}

// 事件处理
const changePage = (pageNum: number) => {
  currentPage.value = pageNum
}

const viewDetail = (record: any) => {
  // 实际应用中可能会跳转到详情页或打开模态框
  alert(`查看详单 ${record.id} 的详细信息`)
}

const goBack = () => {
  router.push('/user-dashboard')
}

// 获取当前页的记录
const pageRecords = computed(() => {
  const start = (currentPage.value - 1) * pageSize
  const end = start + pageSize
  return formattedRecords.value.slice(start, end)
})

onMounted(() => {
  fetchRawData()
})

// 监听筛选条件变化，自动应用筛选
watch([dateRange, selectedPile, sortOrder], () => {
  applyFilters()
})
</script>

<style scoped>
.bill-records-container {
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

.filter-card {
  background-color: white;
  border-radius: 10px;
  padding: 20px;
  margin-bottom: 20px;
  box-shadow: 0 2px 10px rgba(0, 0, 0, 0.05);
  display: flex;
  justify-content: space-between;
  align-items: flex-end;
}

.filters {
  display: flex;
  gap: 20px;
  flex-wrap: wrap;
}

.filter-item {
  flex: 1;
  min-width: 200px;
}

.filter-item label {
  display: block;
  margin-bottom: 8px;
  font-size: 14px;
  color: var(--text-color);
}

.select-input {
  width: 100%;
  padding: 10px;
  border: 1px solid var(--border-color);
  border-radius: 6px;
  font-size: 14px;
  background-color: white;
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
  margin-bottom: 0;
}

.summary-card {
  background-color: #f8f9fa;
  border-radius: 10px;
  padding: 20px;
  display: flex;
  justify-content: space-around;
  margin-bottom: 20px;
  box-shadow: 0 2px 6px rgba(0, 0, 0, 0.05);
}

.summary-item {
  text-align: center;
}

.summary-label {
  font-size: 14px;
  color: var(--light-text);
  margin-bottom: 5px;
}

.summary-value {
  font-size: 24px;
  font-weight: 600;
  color: var(--text-color);
}

.record-card {
  background-color: white;
  border-radius: 10px;
  margin-bottom: 15px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.05);
  overflow: hidden;
}

.record-header {
  background-color: #f8f9fa;
  padding: 15px 20px;
  display: flex;
  justify-content: space-between;
  align-items: center;
  border-bottom: 1px solid var(--border-color);
}

.record-id {
  font-size: 15px;
  font-weight: 500;
  color: var(--text-color);
}

.record-status {
  font-size: 13px;
  padding: 4px 10px;
  border-radius: 12px;
  font-weight: 500;
}

.status-completed {
  background-color: #d4edda;
  color: #155724;
}

.status-interrupted {
  background-color: #fff3cd;
  color: #856404;
}

.status-cancelled {
  background-color: #f8d7da;
  color: #721c24;
}

.record-body {
  padding: 20px;
  display: flex;
  gap: 30px;
}

.record-column {
  flex: 1;
}

.record-item {
  margin-bottom: 15px;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.record-label {
  font-size: 14px;
  color: var(--light-text);
}

.record-value {
  font-size: 14px;
  color: var(--text-color);
  font-weight: 500;
}

.record-footer {
  background-color: #f8f9fa;
  padding: 15px 20px;
  display: flex;
  justify-content: space-between;
  align-items: center;
  border-top: 1px solid var(--border-color);
}

.total-cost {
  font-size: 15px;
  color: var(--text-color);
}

.cost-value {
  font-size: 18px;
  font-weight: 600;
  color: #e53935;
}

.detail-btn {
  background-color: var(--primary-color);
  color: white;
  border: none;
  padding: 8px 16px;
  border-radius: 4px;
  font-size: 13px;
  cursor: pointer;
  transition: all 0.3s;
}

.detail-btn:hover {
  background-color: var(--primary-dark);
}

.pagination {
  display: flex;
  justify-content: center;
  align-items: center;
  margin-top: 30px;
  gap: 20px;
}

.page-btn {
  background-color: white;
  border: 1px solid var(--border-color);
  padding: 8px 15px;
  border-radius: 4px;
  font-size: 14px;
  cursor: pointer;
  transition: all 0.3s;
}

.page-btn:hover:not(:disabled) {
  background-color: #f5f5f5;
}

.page-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.page-info {
  font-size: 14px;
  color: var(--light-text);
}

@media (max-width: 768px) {
  .filter-card {
    flex-direction: column;
    gap: 20px;
    align-items: stretch;
  }
  
  .filters {
    flex-direction: column;
    gap: 15px;
  }
  
  .filter-item {
    width: 100%;
  }
  
  .record-body {
    flex-direction: column;
    gap: 15px;
  }
  
  .summary-card {
    flex-direction: column;
    gap: 15px;
    align-items: center;
  }
  
  .record-footer {
    flex-direction: column;
    gap: 10px;
    align-items: flex-start;
  }
  
  .detail-btn {
    width: 100%;
  }
}
</style> 