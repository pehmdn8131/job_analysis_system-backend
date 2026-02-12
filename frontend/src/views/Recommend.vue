<template>
  <div class="recommend-container">

    <el-card class="search-card">
      <template #header>
        <div class="card-header">
          <span>🎯 职位智能匹配系统</span>
        </div>
      </template>

      <div class="main-search-bar">
        <el-input
            v-model="queryForm.keyword"
            placeholder="请输入职位名称 (如: Python, 产品经理) 或 技能关键字"
            size="large"
            class="keyword-input"
            clearable
            @keyup.enter="handleSearch"
            @clear="searchedKeyword = ''"
        >
          <template #prepend>职位搜索</template>
          <template #append>
            <el-button type="primary" @click="handleSearch" :loading="loading" :icon="Search">搜索</el-button>
          </template>
        </el-input>
      </div>

      <el-form :inline="true" :model="queryForm" class="filter-form">
        <el-form-item label="期望城市">
          <el-select v-model="queryForm.city" placeholder="不限" filterable clearable style="width:140px">
            <el-option v-for="city in cityOptions" :key="city" :label="city" :value="city"/>
          </el-select>
        </el-form-item>
        <el-form-item label="技能精准筛选">
          <el-select v-model="queryForm.skill" multiple collapse-tags :placeholder="skillPlaceholder" style="width:220px">
            <el-option v-for="item in skillOptions" :key="item" :label="item" :value="item"/>
          </el-select>
        </el-form-item>
        <el-form-item label="最低薪资">
          <el-input-number v-model="queryForm.salary" :step="1000" :min="0" style="width: 130px" controls-position="right" />
        </el-form-item>
        <el-form-item label="经验">
          <el-select v-model="queryForm.experience" placeholder="不限" style="width:120px" clearable>
            <el-option label="应届生" value="应届生" />
            <el-option label="1-3年" value="1-3年" />
            <el-option label="3-5年" value="3-5年" />
            <el-option label="5年以上" value="5-10年" />
          </el-select>
        </el-form-item>
        <el-form-item label="学历">
          <el-select v-model="queryForm.education" placeholder="不限" style="width:120px" clearable>
            <el-option label="本科" value="本科" />
            <el-option label="硕士" value="硕士" />
            <el-option label="大专" value="大专" />
          </el-select>
        </el-form-item>
        <el-form-item>
          <el-button type="success" plain @click="handleFilterApply" :disabled="jobList.length === 0">应用筛选</el-button>
        </el-form-item>
      </el-form>
    </el-card>

    <div class="result-area">
      <el-empty v-if="jobList.length === 0 && !loading" :image-size="200" description="暂无相关数据">
        <template #description>
          <div v-if="searchedKeyword">
            <p style="color: #909399; margin-bottom: 10px;">
              数据库中暂时没有关于 <span style="color: #f56c6c; font-weight: bold">"{{ searchedKeyword }}"</span> 的职位
            </p>
            <p style="font-size: 13px; color: #C0C4CC;">您可以启动采集引擎，从互联网实时抓取该岗位数据</p>
          </div>
          <span v-else>请输入关键词开始搜索</span>
        </template>
        <div v-if="searchedKeyword">
          <el-button type="primary" size="large" :icon="Search" color="#626aef" class="crawl-btn" @click="handleQuickCrawl" :disabled="realtimeStatus.is_running">
            {{ realtimeStatus.is_running ? '采集任务运行中...' : `立即采集 "${searchedKeyword}"` }}
          </el-button>
        </div>
      </el-empty>

      <div class="result-count" v-if="jobList.length > 0">
        共为您推荐 <span style="color: #409eff; font-weight: bold">{{ jobList.length }}</span> 个匹配岗位
        <span style="font-size: 12px; color: #999; margin-left: 10px">(当前第 {{ currentPage }} 页)</span>
      </div>

      <el-row :gutter="20" v-if="jobList.length > 0">
        <el-col :span="8" v-for="job in pagedJobList" :key="job.id">
          <el-card shadow="hover" class="job-card" @click="goToDetail(job.detail_url)">
            <div class="card-top">
              <div class="job-name-box">
                <h3 class="job-name" v-html="highlightKeyword(job.job_name)"></h3>
                <span class="salary-text">{{ job.salary }}</span>
              </div>
              <el-tag type="danger" effect="dark" class="score-badge">{{ job.score }}分</el-tag>
            </div>
            <div class="card-mid">
              <div class="company-row">
                <el-icon><OfficeBuilding /></el-icon>
                <span class="company-name">{{ job.company || '未知公司' }}</span>
              </div>
              <div class="info-row">
                <span><el-icon><Location /></el-icon> {{ job.city ? job.city.split('-')[0] : '未知' }}</span>
                <el-divider direction="vertical" />
                <span><el-icon><Timer /></el-icon> {{ job.experience || '经验不限' }}</span>
                <el-divider direction="vertical" />
                <span><el-icon><Reading /></el-icon> {{ job.education }}</span>
              </div>
            </div>
            <div class="card-bot">
              <div class="match-box" v-if="job.match_reasons.length">
                <span v-for="reason in job.match_reasons.slice(0, 2)" :key="reason" class="match-tag">✓ {{ reason }}</span>
              </div>
              <div class="skill-box">
                <el-tag v-for="tag in parseSkills(job.skills).slice(0, 3)" :key="tag" type="info" size="small" effect="plain" class="skill-item">{{ tag }}</el-tag>
              </div>
            </div>
          </el-card>
        </el-col>
      </el-row>

      <div class="pagination-box" v-if="jobList.length > 0">
        <el-pagination background layout="prev, pager, next" :total="jobList.length" :page-size="pageSize" v-model:current-page="currentPage" @current-change="handlePageChange"/>

        <transition name="el-fade-in">
          <div v-if="isLastPage" class="load-more-section">
            <el-divider content-position="center">没有满意的结果？</el-divider>
            <el-button type="primary" size="large" :icon="RefreshRight" class="crawl-more-btn" @click="handleQuickCrawl" :loading="isCrawling" :disabled="realtimeStatus.is_running">
              {{ realtimeStatus.is_running ? '正在后台采集...' : `采集更多 "${searchedKeyword || '相关'}" 职位` }}
            </el-button>
          </div>
        </transition>
      </div>
    </div>
  </div>
</template>

<script setup>
import {ref, reactive, onMounted, computed, watch, onUnmounted} from "vue";
import axios from "axios";
import { ElMessage } from "element-plus";
import { OfficeBuilding, Location, Timer, Reading, Search, RefreshRight } from '@element-plus/icons-vue'

// =================== 状态定义 ===================
const loading = ref(false)
const isCrawling = ref(false)
const jobList = ref([])
const cityOptions = ref([])
const skillOptions = ref([])
const searchedKeyword = ref('')
const currentPage = ref(1)
const pageSize = ref(9)

// 爬虫实时状态
const realtimeStatus = reactive({
  is_running: false,
  total_added: 0
})

const queryForm = reactive({
  keyword: '',
  city: '',
  skill: [],
  salary: 0,
  education: '',
  experience: ''
});

// =================== 计算属性 ===================
const pagedJobList = computed(() => {
  const start = (currentPage.value - 1) * pageSize.value
  const end = start + pageSize.value
  return jobList.value.slice(start, end)
})

const skillPlaceholder = computed(() => {
  if (jobList.value.length === 0) return '请先搜索职位'
  return `在结果中筛选 (${skillOptions.value.length}个相关技能)`
})

const isLastPage = computed(() => {
  if (jobList.value.length === 0) return false
  const maxPage = Math.ceil(jobList.value.length / pageSize.value)
  return currentPage.value === maxPage
})

watch(() => jobList.value, () => { currentPage.value = 1 })

// =================== 核心功能 ===================

const handleSearch = () => {
  queryForm.skill = []
  searchedKeyword.value = queryForm.keyword
  getRecommendations(true)
}

const handleFilterApply = () => { getRecommendations(false) }

const handlePageChange = () => {
  document.querySelector('.result-area')?.scrollIntoView({ behavior: 'smooth' })
}

const getRecommendations = async (isNewSearch = false, silent = false) => {
  if (!queryForm.keyword && isNewSearch) {
    if(!silent) ElMessage.warning('请输入搜索关键词')
    return
  }
  if (!silent) loading.value = true
  try {
    const res = await axios.get('http://127.0.0.1:5000/api/recommend', { params: queryForm })
    if (res.data.code === 200) {
      jobList.value = res.data.data
      if (isNewSearch) {
        updateSkillOptions(jobList.value)
        searchedKeyword.value = queryForm.keyword
      }
    }
  } catch (error){
    if (!silent) ElMessage.error('服务不可用')
  } finally {
    if (!silent) loading.value = false
  }
}

const handleQuickCrawl = async () => {
  const keyword = searchedKeyword.value || queryForm.keyword
  if (!keyword) return ElMessage.warning("请先输入关键词")
  if (realtimeStatus.is_running) return;

  isCrawling.value = true
  try {
    const res = await axios.post('http://127.0.0.1:5000/api/spider/start', { keyword: keyword })
    if (res.data.code === 200) {
      ElMessage.success('采集任务已启动')

      // 🔥 优化点：启动时，重置本地计数，准备监听
      lastTotalAdded = 0
      startStatusPolling()
      // 注意：这里删除了 startListPolling()，不再盲目轮询列表
    } else {
      ElMessage.warning(res.data.msg)
      isCrawling.value = false
    }
  } catch (error) {
    ElMessage.error('无法启动采集')
    isCrawling.value = false
  }
}

// 🔥 优化后的智能轮询：只在数量变化时刷新列表
let statusTimer = null
let lastTotalAdded = 0 // 记录上一次的数量

const startStatusPolling = () => {
  if (statusTimer) clearInterval(statusTimer)

  statusTimer = setInterval(async () => {
    try {
      const res = await axios.get('http://127.0.0.1:5000/api/spider/status')
      if (res.data.code === 200) {
        const data = res.data.data

        realtimeStatus.is_running = data.is_running

        // 🔥 核心逻辑：只有当“已入库数量”增加时，才去刷新列表
        if (data.total_added > lastTotalAdded) {
          lastTotalAdded = data.total_added // 更新本地记录
          getRecommendations(false, true)   // 静默刷新列表
        }

        // 任务结束逻辑
        if (!data.is_running) {
          clearInterval(statusTimer)
          isCrawling.value = false
          // 结束后最后刷一次，确保不漏数据
          getRecommendations(false, true)
        }
      }
    } catch (e) {}
  }, 1000)
}

onUnmounted(() => {
  if (statusTimer) clearInterval(statusTimer)
})

// 工具函数
const parseSkills = (s) => s ? s.replace(/ /g, '').split(',').slice(0, 6) : []
const highlightKeyword = (t) => {
  if (!queryForm.keyword) return t
  const reg = new RegExp(queryForm.keyword, 'gi')
  return t.replace(reg, m => `<span style="color:#f56c6c">${m}</span>`)
}
const updateSkillOptions = (jobs) => {
  const s = new Set(); jobs.forEach(j => j.skills && j.skills.split(',').forEach(t => t.trim() && t.length<15 && s.add(t.trim())))
  skillOptions.value = Array.from(s).sort()
}
const goToDetail = (url) => url && window.open(url, '_blank')
const loadOptions = async () => { try { const r = await axios.get('http://127.0.0.1:5000/api/cities'); if(r.data.code===200) cityOptions.value=r.data.data }catch(e){} }
onMounted(loadOptions)
</script>

<style scoped>
.recommend-container { max-width: 1200px; margin: 0 auto; padding-bottom: 80px; }

.main-search-bar { margin-bottom: 20px; display: flex; justify-content: center; }
.keyword-input { width: 600px; }
.filter-form { background: #f9fafc; padding: 15px; border-radius: 8px; }
.result-count { margin: 15px 0; color: #909399; font-size: 14px; }
.job-card { margin-bottom: 20px; cursor: pointer; transition: all 0.3s; border-radius: 8px; border: 1px solid #ebeef5; height: 200px; display: flex; flex-direction: column; justify-content: space-between; }
.job-card:hover { transform: translateY(-5px); box-shadow: 0 10px 20px rgba(0,0,0,0.1); border-color: #409eff; }
.card-top { display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 5px; }
.job-name-box { flex: 1; overflow: hidden; }
.job-name { margin: 0 0 5px 0; font-size: 16px; font-weight: bold; color: #303133; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.salary-text { color: #f56c6c; font-weight: 800; font-size: 15px; }
.score-badge { font-weight: bold; font-size: 12px; }
.card-mid { margin-bottom: 10px; font-size: 13px; color: #606266; }
.company-row { display: flex; align-items: center; gap: 5px; margin-bottom: 5px; font-weight: 500; }
.company-name { white-space: nowrap; overflow: hidden; text-overflow: ellipsis; max-width: 200px; }
.info-row { display: flex; align-items: center; color: #909399; font-size: 12px; }
.match-box { margin-bottom: 5px; display: flex; flex-wrap: wrap; gap: 5px; height: 20px; overflow: hidden;}
.match-tag { font-size: 12px; color: #67c23a; background: #f0f9eb; padding: 0px 4px; border-radius: 4px; }
.skill-box { display: flex; flex-wrap: wrap; gap: 5px; height: 24px; overflow: hidden; }
.skill-item { margin: 0; }
.pagination-box { margin-top: 30px; display: flex; flex-direction: column; align-items: center; }
.load-more-section { margin-top: 40px; text-align: center; width: 100%; max-width: 600px; }
.crawl-more-btn { width: 220px; box-shadow: 0 4px 12px rgba(64, 158, 255, 0.3); transition: all 0.3s; }
.crawl-more-btn:hover { transform: translateY(-2px); box-shadow: 0 6px 16px rgba(64, 158, 255, 0.4); }
.crawl-btn { margin-top: 20px; animation: pulse 2s infinite; }

@keyframes pulse { 0% { box-shadow: 0 0 0 0 rgba(98, 106, 239, 0.4); } 70% { box-shadow: 0 0 0 10px rgba(98, 106, 239, 0); } 100% { box-shadow: 0 0 0 0 rgba(98, 106, 239, 0); } }
</style>