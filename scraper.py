import asyncio
import json
import os
import random
import time
from bs4 import BeautifulSoup
from playwright.sync_api import sync_playwright

TARGET_DIV_CLASS = "K-MQV"
LOAD_MORE_CLASS = "load-more-content"
MAX_COUNT = 5000
CHUNK_SIZE = 200
OUTPUT_DIR = "output"

os.makedirs(OUTPUT_DIR, exist_ok=True)

def fix_image_url(url):
    if url and url.startswith("//"):
        return "https:" + url
    if url and not url.startswith("http"):
        return "https://" + url.lstrip("/")
    return url

def parse_target_div(div):
    data = {}

    # Extract title and article URL
    title_anchor = div.select_one("h3.headline-title a.title-link")
    if title_anchor:
        data["title"] = title_anchor.get_text(strip=True)
        raw_url = title_anchor.get("href")
        data["url"] = fix_image_url(raw_url)
    else:
        data["title"] = None
        data["url"] = None

    # Image tag handling
    image_tag = div.select_one("div.left-image a img")
    if not image_tag:
        image_tag = div.select_one("img.qt-image.image")
    if image_tag:
        src = image_tag.get("src")
        data["image_url"] = fix_image_url(src)
        data["image_caption"] = image_tag.get("alt")
    else:
        data["image_url"] = None
        data["image_caption"] = None

    # Excerpt
    excerpt_anchor = div.select_one("a.excerpt")
    data["excerpt"] = excerpt_anchor.get_text(strip=True) if excerpt_anchor else None

    # Published time
    time_tag = div.select_one("div.story-meta-data time.published-time")
    data["published_time"] = time_tag.get_text(strip=True) if time_tag else None

    return data

def is_valid_entry(entry):
    return all(entry.get(k) for k in ["title", "url", "image_url", "excerpt", "published_time"])

def dump_data_chunk(data_list, part_number):
    file_path = os.path.join(OUTPUT_DIR, f"output_part_{part_number}.json")
    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(data_list, f, ensure_ascii=False, indent=2)
    print(f"✅ Dumped {len(data_list)} items to {file_path}")

def scrape_prothomalo():
    url = "https://www.prothomalo.com/search?sort=latest-published"

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        page = browser.new_page()
        page.goto(url)

        collected = []
        dumped_parts = 0

        while len(collected) < MAX_COUNT:
            page_content = page.content()
            soup = BeautifulSoup(page_content, "html.parser")
            target_divs = soup.find_all("div", class_=TARGET_DIV_CLASS)
            print(f"🔎 Found {len(target_divs)} total divs")

            for div in target_divs[len(collected):]:
                data = parse_target_div(div)
                if is_valid_entry(data):
                    collected.append(data)

                if len(collected) % CHUNK_SIZE == 0 and len(collected) // CHUNK_SIZE > dumped_parts:
                    dumped_parts += 1
                    dump_data_chunk(collected[-CHUNK_SIZE:], dumped_parts)

                if len(collected) >= MAX_COUNT:
                    break

            try:
                load_more = page.query_selector(f".{LOAD_MORE_CLASS}")
                if not load_more:
                    print("🚫 No more 'Load More' button found.")
                    break
                time.sleep(random.uniform(2, 4))
                load_more.click()
                time.sleep(random.uniform(3, 5))
            except Exception as e:
                print(f"⚠️ Exception during 'Load More': {e}")
                break

        browser.close()

        # Final dump if needed
        remaining = len(collected) % CHUNK_SIZE
        if remaining:
            dumped_parts += 1
            dump_data_chunk(collected[-remaining:], dumped_parts)

        print(f"\n🎉 Scraped and saved {len(collected)} valid items.")

if __name__ == "__main__":
    scrape_prothomalo()
