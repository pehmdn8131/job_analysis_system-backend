from DrissionPage import ChromiumPage
from DrissionPage import ChromiumOptions
from app import app, db, Job
import time, random, re, hashlib, json, os
from html import unescape
from datetime import datetime

KEYWORD = "Java"
MAX_PAGES = 2
PROGRESS_FILE = "progress.json"


# ========== 薪资清洗 ==========
def clean_salary(salary_str):
    if not salary_str:
        return 0, 0
    s = salary_str.lower()
    nums = re.findall(r'\d+\.?\d*', s)
    if not nums:
        return 0, 0
    if '万' in s:
        min_sal = float(nums[0]) * 10000
        max_sal = float(nums[1]) * 10000 if len(nums) > 1 else min_sal
        if '年' in s:
            min_sal /= 12
            max_sal /= 12
    else:
        min_sal = float(nums[0]) * 1000
        max_sal = float(nums[1]) * 1000 if len(nums) > 1 else min_sal
    return int(min_sal), int(max_sal)


# ========== 唯一哈希 ==========
def gen_hash(job_name, company, job_id=None):
    if job_id:
        return hashlib.md5(f"{job_id}_{job_name}_{company}".encode()).hexdigest()
    return hashlib.md5(f"{job_name}_{company}".encode()).hexdigest()


# ========== (新增) 提取卡片上的技术标签 ==========
def extract_card_tags(card):
    """
    从列表卡片中提取标签，并过滤掉福利待遇类的词
    """
    technical_tags = []

    # 1. 定义福利待遇关键词（黑名单）
    # 只要标签包含这些词，就认为它不是技术栈
    welfare_blacklist = [
        "五险", "一金", "社保", "公积金",
        "双休", "单双", "休", "假", "年假",
        "补", "餐", "房", "包吃", "包住",
        "奖", "薪", "红", "提成",
        "体检", "旅游", "团建", "节日", "生日",
        "弹性", "氛围", "零食", "下午茶", "期权",
        "晋升", "培训", "扁平", "领导好", "股票",
        "免费", "交通", "通讯", "采暖", "高温"
    ]

    try:
        # 获取卡片内所有的 tag 元素
        # 根据你的日志，class 可能是 'tag'
        tags = card.eles('.tag')

        for tag in tags:
            text = tag.text.strip()
            if not text:
                continue

            # 检查是否包含黑名单词汇
            is_welfare = False
            for bad_word in welfare_blacklist:
                if bad_word in text:
                    is_welfare = True
                    break

            # 如果不是福利词，且长度适中（排除太长的废话），认为是技术词
            if not is_welfare and len(text) < 15:
                technical_tags.append(text)

    except Exception as e:
        pass  # 提取失败就算了，不影响主流程

    # 去重并用逗号拼接
    return ",".join(list(set(technical_tags)))


# ========== 解析详情页 ==========
def parse_detail_page(tab):
    education = "不限"
    skills = ""

    try:
        tab.wait.ele_displayed('body', timeout=3)
    except:
        pass

    try:
        if tab.ele('.login_layer_close', timeout=1):
            tab.ele('.login_layer_close').click()
    except:
        pass

    desc = ""
    selectors = ['.bmsg.job_msg.inbox', '.job_msg', '.job-detail']

    for selector in selectors:
        try:
            elem = tab.ele(selector, timeout=0.5)
            if elem:
                desc = elem.text
                break
        except:
            continue

    if not desc:
        try:
            desc = tab.ele('body', timeout=0.5).text[:1000]
        except:
            return education, skills

    # 提取技能 (这里保留详情页提取逻辑，作为补充)
    skill_keywords = ["Python", "Flask", "Django", "MySQL", "Linux", "Docker", "Git",
                      "Redis", "Vue", "React", "Java", "C++", "算法", "后端", "全栈"]
    skills_found = []
    desc_upper = desc.upper()
    for keyword in skill_keywords:
        if keyword.upper() in desc_upper:
            skills_found.append(keyword)

    skills = ",".join(list(set(skills_found)))[:100]

    return education, skills


# ========== 进度保存 ==========
def save_progress(page_num):
    with open(PROGRESS_FILE, "w") as f:
        json.dump({"page": page_num}, f)


def load_progress():
    if os.path.exists(PROGRESS_FILE):
        with open(PROGRESS_FILE) as f:
            return json.load(f).get("page", 1)
    return 1


def get_company_name(card):
    company = "未知公司"
    try:
        company_links = card.eles('a.cname')
        if company_links:
            return company_links[0].text.strip()

        if company == "未知公司":
            lines = [line.strip() for line in card.text.split('\n') if line.strip()]
            for line in lines:
                if len(line) > 2 and '公司' in line and not any(char.isdigit() for char in line[:5]):
                    company = line
                    break
    except:
        pass
    return company


def get_job_detail_url(job_id, job_name):
    if not job_id: return None
    return f"https://jobs.51job.com/all/{job_id}.html"


# ========== 主程序 ==========
def run_spider():
    start_page = 1

    co = ChromiumOptions()
    co.set_argument('--blink-settings=imagesEnabled=false')
    page = ChromiumPage(co)
    page.set.timeouts(5)
    page.set.download_path('.')
    page.set.window.max()

    search_url = f'https://we.51job.com/pc/search?keyword={KEYWORD}'
    print(f"正在访问: {search_url}")
    page.get(search_url)

    try:
        page.wait.ele_displayed('.joblist-item-job-wrapper', timeout=20)
    except:
        page.wait.load_start()

    try:
        for page_num in range(start_page, MAX_PAGES + 1):
            print(f"\n===== 第 {page_num} 页 =====")

            print("正在滚动加载...")
            for i in range(3):
                page.scroll.to_bottom()
                time.sleep(0.5)

            cards = page.eles('.joblist-item-job-wrapper')
            print(f"找到 {len(cards)} 个职位卡片")

            if not cards:
                print("❌ 未找到职位卡片")
                break

            for i, card in enumerate(cards):
                try:
                    # 1. 获取基础数据
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
                    salary_str = data.get("jobSalary", "").strip()
                    city = data.get("jobArea", "").strip()
                    experience = data.get("jobYear", "").strip()
                    education = data.get("jobDegree", "不限").strip()

                    if not job_name: continue

                    company = get_company_name(card)
                    s_min, s_max = clean_salary(salary_str)
                    detail_url = get_job_detail_url(job_id, job_name)
                    job_hash = gen_hash(job_name, company, job_id)

                    # 2. 检查数据库
                    with app.app_context():
                        exists = Job.query.filter_by(hash=job_hash).first()

                    if exists:
                        print(f"⏭️ 已存在: {job_name}")
                        continue

                    # ===============================================
                    # ✅ 核心修改：先从卡片提取技能标签
                    # ===============================================
                    card_skills = extract_card_tags(card)
                    skills = card_skills  # 默认使用卡片技能

                    edu_detail = education

                    # 3. (可选) 爬取详情页
                    # 如果你希望只用卡片数据，可以把下面这个 if detail_url 块注释掉，速度会极快！
                    # 如果你想合并两者，保留下面的代码
                    if detail_url:
                        try:
                            tab = page.new_tab(detail_url)
                            tab.wait.load_start()
                            if 'login' not in tab.url:
                                edu_extracted, skills_extracted = parse_detail_page(tab)
                                if edu_extracted and edu_extracted != "不限":
                                    edu_detail = edu_extracted

                                # 合并技能：卡片技能 + 详情页技能
                                combined_skills = set(card_skills.split(',')) | set(skills_extracted.split(','))
                                # 去除空字符串
                                combined_skills.discard('')
                                skills = ",".join(list(combined_skills))

                            tab.close()
                        except:
                            try:
                                tab.close()
                            except:
                                pass

                        time.sleep(random.uniform(0.5, 1.0))

                    # 4. 保存
                    try:
                        with app.app_context():
                            job_obj = Job(
                                job_name=job_name,
                                salary=salary_str,
                                salary_min=s_min,
                                salary_max=s_max,
                                city=city,
                                experience=experience,
                                education=edu_detail,
                                skills=skills,  # 这里存入的就是过滤后的技术标签
                                company=company,
                                detail_url=detail_url,
                                hash=job_hash,
                                create_time=datetime.now()
                            )
                            db.session.add(job_obj)
                            db.session.commit()
                            print(f"💾 已保存: {job_name} | 技能: {skills[:30]}...")
                    except Exception as e:
                        print(f"数据库保存出错: {e}")

                except Exception as e:
                    print(f"卡片处理出错: {e}")
                    continue

            save_progress(page_num + 1)

            # 翻页逻辑
            if page_num < MAX_PAGES:
                print(f"\n准备翻页: 第 {page_num} -> {page_num + 1} 页...")
                try:
                    old_first_job = cards[0].ele('.job-info').text[:10]
                except:
                    old_first_job = "unknown"

                next_success = False
                try:
                    next_btn = page.ele('css:button.btn-next', timeout=2) or \
                               page.ele('xpath://button[contains(text(), "下一页")]', timeout=2) or \
                               page.ele('css:li.next', timeout=2)

                    if next_btn and 'disabled' not in (next_btn.attr('class') or ''):
                        next_btn.scroll.to_see()
                        time.sleep(0.5)
                        next_btn.click()
                        print("🖱️ 点击了下一页按钮")
                        next_success = True
                except:
                    pass

                if not next_success:
                    next_url = f'https://we.51job.com/pc/search?keyword={KEYWORD}&p={page_num + 1}'
                    print(f"🔗 尝试URL跳转: {next_url}")
                    page.get(next_url)

                print("⏳ 等待数据更新...")
                is_new_page = False
                check_start = time.time()
                while time.time() - check_start < 10:
                    try:
                        new_cards = page.eles('.joblist-item-job-wrapper')
                        if new_cards:
                            new_first_job = new_cards[0].ele('.job-info').text[:10]
                            if new_first_job != old_first_job:
                                is_new_page = True
                                print(f"✅ 翻页成功")
                                break
                    except:
                        pass
                    time.sleep(1)

                time.sleep(2)
            else:
                break

    except KeyboardInterrupt:
        print("\n🛑 用户手动停止程序")
    finally:
        page.quit()


if __name__ == '__main__':
    run_spider()