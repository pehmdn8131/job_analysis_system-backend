# spider.py
from DrissionPage import ChromiumPage, ChromiumOptions
from models import db, Job
import time, re, hashlib, json, random
from html import unescape
from datetime import datetime

# ==========================================
# 🔥 全局状态变量 (用于前端进度条)
# ==========================================
spider_status = {
    'is_running': False,
    'total_added': 0,
    'current_page': 0,
    'log': '就绪'
}


# ========== 1. 工具函数 (保留旧版逻辑) ==========

def clean_salary(salary_str):
    if not salary_str: return 0, 0
    s = salary_str.lower()
    nums = re.findall(r'\d+\.?\d*', s)
    if not nums: return 0, 0
    multiplier = 1
    if '万' in s:
        multiplier = 10000
    elif '千' in s:
        multiplier = 1000
    is_year = '年' in s
    try:
        min_sal = float(nums[0]) * multiplier
        max_sal = float(nums[1]) * multiplier if len(nums) > 1 else min_sal
        if is_year:
            min_sal /= 12
            max_sal /= 12
        return int(min_sal), int(max_sal)
    except:
        return 0, 0


def gen_hash(job_name, company, job_id=None):
    if job_id:
        return hashlib.md5(f"{job_id}_{job_name}_{company}".encode()).hexdigest()
    return hashlib.md5(f"{job_name}_{company}".encode()).hexdigest()


def extract_card_tags(card):
    """提取标签 (保留新版的黑名单机制，效果更好)"""
    technical_tags = []
    welfare_blacklist = [
        "五险", "一金", "双休", "包吃", "包住", "年假", "节日", "旅游", "补", "假", "奖", "氛围",
        "下午茶", "体检", "年终", "股票", "期权", "弹性", "免费", "班车", "晋升", "培训",
        "定期", "团建", "高温", "采暖", "通讯", "交通", "餐补", "房补", "周末", "带薪", "绩效", "全勤",
        "市场", "客户", "维护", "销售", "战略", "开拓", "招商", "运营"
    ]
    try:
        tags = card.eles('.tag', timeout=0.2)
        for tag in tags:
            text = tag.text.strip()
            if not text: continue
            is_welfare = any(bad in text for bad in welfare_blacklist)
            if not is_welfare and len(text) < 15:
                technical_tags.append(text)
    except:
        pass
    return ",".join(list(set(technical_tags)))


def get_company_name(card):
    """
    🔥 使用你旧代码里的逻辑，因为它在你那边是好用的
    """
    company = "未知公司"
    try:
        # 尝试找链接
        company_links = card.eles('a.cname')
        if company_links:
            return company_links[0].text.strip()

        # 兜底：文本分析
        if company == "未知公司":
            lines = [line.strip() for line in card.text.split('\n') if line.strip()]
            for line in lines:
                if len(line) > 2 and '公司' in line and not any(char.isdigit() for char in line[:5]):
                    company = line
                    break
    except:
        pass
    return company


# ========== 核心任务 ==========

def run_spider_task(keyword, target_pages=1):
    """
    keyword: 搜索关键词
    target_pages: 期望获取的新数据页数 (每页按50条计算)
    """
    global spider_status

    # ==========================================
    # 🎯 设定目标
    # 51job 每页约 20 条。如果用户想要 3 页新数据，
    # 目标就是找到 3 * 50 = 150 条新岗位。
    # ==========================================
    TARGET_NEW_JOBS = target_pages * 20

    # 🛡️ 安全熔断：防止全网只有1页数据，爬虫却想找10页，导致死循环。
    # 限制最多向后翻多少页（比如最多翻 50 页）
    MAX_SCAN_DEPTH = 50

    # 1. 重置状态
    spider_status['is_running'] = True
    spider_status['total_added'] = 0
    spider_status['current_page'] = 0
    spider_status['log'] = f"正在启动浏览器搜索: {keyword}..."

    print(f"🕷️ 启动爬虫任务: {keyword}")
    print(f"🎯 目标: 获取 {target_pages} 页新数据 (约 {TARGET_NEW_JOBS} 条)")

    co = ChromiumOptions()
    co.set_argument('--blink-settings=imagesEnabled=false')

    page = ChromiumPage(co)
    page.set.timeouts(5)

    new_jobs_count = 0  # 当前次运行新增的数量
    current_page_num = 1  # 当前正在爬取的页码

    try:
        search_url = f'https://we.51job.com/pc/search?keyword={keyword}'
        page.get(search_url)

        try:
            page.wait.ele_displayed('.joblist-item-job-wrapper', timeout=10)
        except:
            spider_status['log'] = "页面加载较慢..."

        # ==========================================
        # 🔥 核心修改：使用 while 循环直到目标达成
        # ==========================================
        while new_jobs_count < TARGET_NEW_JOBS and current_page_num <= MAX_SCAN_DEPTH:

            spider_status['current_page'] = current_page_num
            status_msg = f"正在处理第 {current_page_num} 页 | 进度: {new_jobs_count}/{TARGET_NEW_JOBS}"
            spider_status['log'] = status_msg
            print(f"\n📄 {status_msg}")

            # 滚动加载
            for i in range(3):
                page.scroll.to_bottom()
                time.sleep(0.5)

            cards = page.eles('.joblist-item-job-wrapper')
            if not cards:
                print("❌ 未找到职位卡片 (可能是翻到底了)")
                break

            total_cards = len(cards)

            # --- 开始解析本页 ---
            for i, card in enumerate(cards):
                # 如果已经达到目标，直接跳出卡片循环
                if new_jobs_count >= TARGET_NEW_JOBS:
                    break

                spider_status[
                    'log'] = f"第 {current_page_num} 页: 解析 {i + 1}/{total_cards} | 已入库: {new_jobs_count}"

                try:
                    # --- 元素定位逻辑 (保持不变) ---
                    sensors_div = None
                    try:
                        divs = card.eles('tag:div')
                        for div in divs:
                            if div.attr('sensorsname') == 'JobShortExposure':
                                sensors_div = div
                                break
                    except:
                        pass

                    if not sensors_div: continue
                    sensors_data_str = sensors_div.attr('sensorsdata')
                    if not sensors_data_str: continue
                    data = json.loads(unescape(sensors_data_str))

                    job_id = data.get("jobId", "")
                    job_name = data.get("jobTitle", "").strip()
                    if not job_name: continue

                    salary_str = data.get("jobSalary", "").strip()
                    city = data.get("jobArea", "").strip()
                    experience = data.get("jobYear", "").strip()
                    education = data.get("jobDegree", "不限").strip()

                    company = data.get("jobCompanyName", "").strip()
                    if not company:
                        company = get_company_name(card)

                    s_min, s_max = clean_salary(salary_str)
                    detail_url = f"https://jobs.51job.com/all/{job_id}.html"
                    job_hash = gen_hash(job_name, company, job_id)

                    # 查重
                    if Job.query.filter_by(hash=job_hash).first():
                        # print(f"  跳过重复: {job_name}")
                        continue

                    skills = extract_card_tags(card)

                    job_obj = Job(
                        job_name=job_name,
                        company=company,
                        salary=salary_str,
                        salary_min=s_min,
                        salary_max=s_max,
                        city=city,
                        experience=experience,
                        education=education,
                        skills=skills,
                        detail_url=detail_url,
                        hash=job_hash,
                        create_time=datetime.now()
                    )

                    # 实时入库
                    db.session.add(job_obj)
                    db.session.commit()

                    new_jobs_count += 1
                    spider_status['total_added'] = new_jobs_count
                    print(f"  ✅ ({new_jobs_count}/{TARGET_NEW_JOBS}) {job_name}")

                except Exception as e:
                    db.session.rollback()
                    continue

            # --- 本页循环结束 ---

            # 如果已经达成目标，退出最外层 while 循环
            if new_jobs_count >= TARGET_NEW_JOBS:
                spider_status['log'] = "🎉 目标达成，停止采集"
                print("🎉 已采集到足够的新数据，任务结束。")
                break

            # 翻页逻辑
            try:
                next_btn = page.ele('css:button.btn-next', timeout=2) or \
                           page.ele('xpath://button[contains(text(), "下一页")]', timeout=2) or \
                           page.ele('css:li.next', timeout=2)

                if next_btn and 'disabled' not in (next_btn.attr('class') or ''):
                    next_btn.click()
                    time.sleep(2)
                    current_page_num += 1  # 页码+1
                else:
                    print("🚫 没有下一页了，停止采集。")
                    break
            except:
                print("🚫 翻页按钮未找到或出错，停止。")
                break

    except Exception as e:
        spider_status['log'] = f"出错: {str(e)}"
        print(f"❌ 爬虫全局异常: {e}")
    finally:
        page.quit()
        spider_status['is_running'] = False
        spider_status['log'] = f"采集完成，共入库 {new_jobs_count} 条"

    return new_jobs_count