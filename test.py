from DrissionPage._pages.chromium_page import ChromiumPage
import time

def check_page_structure():
    """检查51job页面结构"""
    page = ChromiumPage()
    page.get(f'https://we.51job.com/pc/search?keyword=%E5%AE%A2%E6%88%B7%E7%BB%8F%E7%90%86&searchType=2&sortType=0&metro=')
    time.sleep(5)

    # 保存页面
    with open('51job_page.html', 'w', encoding='utf-8') as f:
        f.write(page.html)

    print("页面已保存为 51job_page.html")

    # 查找所有可能的职位相关元素
    print("\n查找职位相关元素...")
    all_elements = page.eles('div, span, li')
    job_elements = []

    for elem in all_elements[:100]:  # 只检查前100个元素
        txt = elem.text
        if txt and 'python' in txt.lower():
            job_elements.append(elem)
            print(f"找到可能元素: {elem.tag} class={elemclass_name} text={txt[:50]}")

    page.quit()


if __name__ == '__main__':
    # 先检查页面结构
    check_page_structure()
    # 再运行爬虫
    # run_spider()