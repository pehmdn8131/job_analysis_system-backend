<template>
  <div class="dashboard-container">

    <el-row :gutter="20" class="data-cards">
      <el-col :span="8">
        <el-card shadow="hover" class="stat-card">
          <template #header>
            <div class="card-header">
              <span>📚 当前收录岗位</span>
              <el-tag type="info" effect="plain" size="small">实时</el-tag>
            </div>
          </template>
          <div class="card-num">{{ totalJobs }} <span class="unit">个</span></div>
        </el-card>
      </el-col>
      <el-col :span="8">
        <el-card shadow="hover" class="stat-card">
          <template #header>
            <div class="card-header">
              <span>🏙️ 覆盖城市</span>
              <el-tag type="success" effect="plain" size="small">City</el-tag>
            </div>
          </template>
          <div class="card-num">{{ totalCities }} <span class="unit">座</span></div>
        </el-card>
      </el-col>
      <el-col :span="8">
        <el-card shadow="hover" class="stat-card">
          <template #header>
            <div class="card-header">
              <span>💰 平均月薪</span>
              <el-tag type="danger" effect="plain" size="small">Avg</el-tag>
            </div>
          </template>
          <div class="card-num salary-num">¥ {{ avgSalary }}</div>
        </el-card>
      </el-col>
    </el-row>

    <el-card class="chart-card" shadow="never">
      <template #header>
        <div class="chart-header">
          <span>📊 招聘数据全景分析</span>
          <div class="chart-actions">
            <el-button :icon="Refresh" circle size="small" @click="initChart" />
          </div>
        </div>
      </template>
      <div ref="chartRef" style="width: 100%; height: 550px;"></div>
    </el-card>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import * as echarts from 'echarts'
import axios from 'axios'
import { Refresh } from '@element-plus/icons-vue'

// --- 图表相关变量 ---
const chartRef = ref(null)
const totalJobs = ref(0)
const totalCities = ref(0)
const avgSalary = ref(0)

// ==========================================
// 📊 图表初始化与数据获取
// ==========================================
const initChart = async () => {
  if (!chartRef.value) return

  // 销毁旧实例（防止 resize 报错）
  let myChart = echarts.getInstanceByDom(chartRef.value)
  if (myChart) {
    myChart.dispose()
  }
  myChart = echarts.init(chartRef.value)

  myChart.showLoading({
    text: '数据加载中...',
    color: '#409eff'
  })

  try {
    const res = await axios.get('http://127.0.0.1:5000/api/analysis/city')

    if (res.data.code === 200) {
      const chartData = res.data.data      // 这是用于画图的 Top 15 数据
      const report = res.data.report       // 🔥 这是用于展示的真实统计数据

      // 1. 优先使用后端传回来的真实统计数据
      if (report) {
        totalJobs.value = report.total_jobs
        totalCities.value = report.total_cities
        avgSalary.value = report.avg_salary
      } else {
        // 兜底逻辑：万一后端没传 report，才用累加法（虽然不准）
        totalJobs.value = chartData.reduce((a, b) => a + b.value, 0)
        totalCities.value = chartData.length
      }

      // 2. 准备图表数据
      const cities = chartData.map(item => item.name)
      const counts = chartData.map(item => item.value)
      const salaries = chartData.map(item => item.avg_salary)

      // 配置图表
      const option = {
        title: {
          text: '热门城市岗位分布 (Top 15)',
          subtext: `数据库共收录 ${totalJobs.value} 条数据`, // 标题也可以显示真实总数
          left: 'center',
          top: 10
        },
        tooltip: {
          trigger: 'axis',
          axisPointer: { type: 'cross' }
        },
        grid: { left: '3%', right: '4%', bottom: '3%', containLabel: true },
        legend: { data: ['岗位数量', '平均薪资'], bottom: 10 },
        xAxis: {
          type: 'category',
          data: cities,
          axisLabel: { interval: 0, rotate: 30, color: '#666' },
          axisLine: { lineStyle: { color: '#ccc' } }
        },
        yAxis: [
          {
            type: 'value',
            name: '岗位数量',
            position: 'left',
            splitLine: { lineStyle: { type: 'dashed' } }
          },
          {
            type: 'value',
            name: '薪资 (元)',
            position: 'right',
            axisLabel: { formatter: '{value}' },
            splitLine: { show: false }
          }
        ],
        series: [
          {
            name: '岗位数量',
            type: 'bar',
            data: counts,
            itemStyle: {
              borderRadius: [4, 4, 0, 0],
              color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
                { offset: 0, color: '#83bff6' },
                { offset: 0.5, color: '#188df0' },
                { offset: 1, color: '#188df0' }
              ])
            },
            barMaxWidth: 40,
            animationDuration: 2000
          },
          {
            name: '平均薪资',
            type: 'line',
            yAxisIndex: 1,
            data: salaries,
            itemStyle: { color: '#67C23A' },
            symbol: 'circle',
            symbolSize: 8,
            smooth: true,
            lineStyle: { width: 3, shadowColor: 'rgba(0,0,0,0.3)', shadowBlur: 10 }
          }
        ]
      }
      myChart.setOption(option)
    }
  } catch (error) {
    console.error("获取数据失败", error)
  } finally {
    myChart.hideLoading()
  }

  window.addEventListener('resize', () => myChart.resize())
}

onMounted(() => {
  initChart()
})
</script>

<style scoped>
.dashboard-container {
  padding: 0;
}

.data-cards { margin-bottom: 20px; }
.stat-card { text-align: center; border-radius: 8px; transition: all 0.3s; }
.stat-card:hover { transform: translateY(-3px); box-shadow: 0 10px 20px rgba(0,0,0,0.1); }

.card-header { display: flex; justify-content: space-between; align-items: center; }

.card-num {
  font-size: 32px;
  font-weight: bold;
  color: #409EFF;
  margin-top: 10px;
}
.salary-num { color: #67C23A; }
.unit { font-size: 14px; color: #909399; font-weight: normal; margin-left: 5px; }

.chart-card { border-radius: 8px; }
.chart-header { display: flex; justify-content: space-between; align-items: center; }
</style>