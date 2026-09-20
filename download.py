import os
import re
import time
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin

# 配置
BASE_URL = "https://www.javrate.com"
# 列表页 URL 模板，页码从 1 到 122
LIST_URL_TEMPLATE = "https://www.javrate.com/actor/list/3-0-{page}.html"
TOTAL_PAGES = 122
SAVE_DIR = r"C:\Users\Administrator\Desktop\javrate_actors"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}

os.makedirs(SAVE_DIR, exist_ok=True)

def sanitize_filename(name):
    """清理文件名中不合法的字符"""
    return re.sub(r'[\\/:*?"<>|]', "_", name).strip()

def download_image(img_url, save_path):
    """下载图片，如果已存在则跳过"""
    if os.path.exists(save_path):
        return "skipped"
    try:
        resp = requests.get(img_url, headers=HEADERS, timeout=15)
        resp.raise_for_status()
        with open(save_path, "wb") as f:
            f.write(resp.content)
        return "ok"
    except Exception as e:
        print(f"  下载失败: {img_url} -> {e}")
        return "fail"

def extract_actors_from_page(soup):
    """从一页的 HTML 中提取所有女优 (名字, 图片URL)"""
    actors = []
    for card in soup.find_all("div", class_="actor-card"):
        link = card.find("a", class_="actress-card-link")
        if not link:
            continue

        name = link.get("data-actress-name") or link.get("title", "").strip()
        img_tag = card.find("img")
        if not (img_tag and name):
            continue

        img_src = img_tag.get("src") or img_tag.get("data-src")
        if not img_src:
            continue

        # 处理图片路径
        if img_src.startswith("./"):
            filename = img_src.split("/")[-1]
            img_url = f"https://picture.avking.xyz/{filename}"
        else:
            img_url = urljoin(BASE_URL, img_src)

        actors.append((name, img_url))
    return actors

def main():
    total_downloaded = 0
    total_skipped = 0
    total_failed = 0
    failed_images = []   # 记录失败的图片名字

    for page in range(1, TOTAL_PAGES + 1):
        url = LIST_URL_TEMPLATE.format(page=page)
        print(f"\n===== 第 {page}/{TOTAL_PAGES} 页 =====")
        print(f"请求: {url}")

        try:
            resp = requests.get(url, headers=HEADERS, timeout=20)
            resp.raise_for_status()
            resp.encoding = resp.apparent_encoding
        except Exception as e:
            print(f"  页面请求失败: {e}")
            time.sleep(3)
            continue

        soup = BeautifulSoup(resp.text, "html.parser")
        actors = extract_actors_from_page(soup)

        if not actors:
            print("  本页未找到女优信息，可能页面结构有变。")
            continue

        print(f"  找到 {len(actors)} 位女优，开始下载...")

        for i, (name, img_url) in enumerate(actors, 1):
            safe_name = sanitize_filename(name)
            ext = os.path.splitext(img_url)[1] or ".webp"
            save_path = os.path.join(SAVE_DIR, f"{safe_name}{ext}")

            result = download_image(img_url, save_path)

            if result == "ok":
                print(f"  [{i}/{len(actors)}] {name}  ✅ 已下载")
                total_downloaded += 1
            elif result == "skipped":
                print(f"  [{i}/{len(actors)}] {name}  ⏭️ 已存在，跳过")
                total_skipped += 1
            else:
                print(f"  [{i}/{len(actors)}] {name}  ❌ 失败")
                failed_images.append(name)
                total_failed += 1

            time.sleep(0.3)  # 每张图片之间的间隔

        time.sleep(2)  # 每页之间的间隔，避免请求过快

    print("\n===== 全部完成 =====")
    print(f"下载成功: {total_downloaded}")
    print(f"已存在跳过: {total_skipped}")
    print(f"下载失败: {total_failed}")
    print(f"保存目录: {SAVE_DIR}")

    if failed_images:
        print("\n===== 失败的图片 =====")
        for name in failed_images:
            print(f"  - {name}")

if __name__ == "__main__":
    main()