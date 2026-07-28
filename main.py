import os
import datetime
import time
import json
import html
import urllib.request
import feedparser
import requests
from groq import Groq
from dotenv import load_dotenv
from playwright.sync_api import sync_playwright
import sys

# Cấu hình in tiếng Việt trên Windows
sys.stdout.reconfigure(encoding='utf-8')

# 1. Load biến môi trường
load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")  # giữ lại để dự phòng
GROQ_API_KEY   = os.getenv("GROQ_API_KEY")
LINKEDIN_ACCESS_TOKEN = os.getenv("LINKEDIN_ACCESS_TOKEN")
TEST_MODE = os.getenv("TEST_MODE", "true").lower() == "true"

def call_groq(prompt, max_retries=3, max_tokens=4096):
    """Gọi Groq API (LLaMA 3.3 70B) với retry tự động khi gặp lỗi rate limit"""
    client = Groq(api_key=GROQ_API_KEY)
    wait_times = [15, 30, 60]
    for attempt in range(max_retries + 1):
        try:
            completion = client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.7,
                max_tokens=max_tokens,
            )
            return completion.choices[0].message.content.strip()
        except Exception as e:
            err_str = str(e)
            if ("429" in err_str or "rate_limit" in err_str.lower()) and attempt < max_retries:
                wait = wait_times[attempt]
                print(f"⚠️  Rate limit Groq. Thử lại sau {wait}s... (lần {attempt+1}/{max_retries})", flush=True)
                time.sleep(wait)
            else:
                raise

def fetch_latest_arxiv_paper():
    """Lấy bài báo mới nhất về Data Analytics từ Arxiv"""
    print("Đang tìm bài báo khoa học mới nhất trên Arxiv...", flush=True)
    query = 'all:data+analytics'
    url = f'http://export.arxiv.org/api/query?search_query={query}&start=0&max_results=1&sortBy=submittedDate&sortOrder=descending'
    
    # Sử dụng requests để tránh lỗi SSL trên Windows
    response = requests.get(url, timeout=15)
    feed = feedparser.parse(response.content)
    
    if not feed.entries:
        raise Exception("Không tìm thấy bài báo nào!")
        
    entry = feed.entries[0]
    return {
        "title": entry.title,
        "abstract": entry.summary,
        "authors": ", ".join(author.name for author in entry.authors),
        "link": entry.link
    }

def generate_linkedin_post(paper_info):
    """Dùng Groq AI (LLaMA 3.3 70B) để viết bài đăng LinkedIn"""
    print("Đang nhờ Groq AI phân tích và viết bài...", flush=True)

    prompt = f"""Bạn là một chuyên gia Data Analyst đang xây dựng thương hiệu cá nhân trên LinkedIn.
Hãy đọc tóm tắt bài báo khoa học dưới đây và viết một bài đăng LinkedIn bằng tiếng Việt thật chuyên nghiệp, cuốn hút và dễ hiểu.

Thông tin bài báo:
- Tiêu đề: {paper_info['title']}
- Tác giả: {paper_info['authors']}
- Link: {paper_info['link']}
- Tóm tắt (Abstract): {paper_info['abstract']}

Yêu cầu cấu trúc bài viết:
1. Mở đầu: Một tiêu đề hoặc câu hook thật thu hút, có chứa emoji.
2. Nội dung chính: Tóm tắt ngắn gọn bài báo nói về điều gì (sử dụng bullet points).
3. Insight/Bài học: Là một Data Analyst, bạn rút ra được điều gì từ nghiên cứu này, hoặc nó có thể ứng dụng thế nào vào thực tế?
4. Kết luận & Nguồn: Để lại link bài gốc và đặt câu hỏi mở để tương tác với người đọc.
5. Hashtags: Thêm 4-5 hashtag phù hợp (VD: #DataAnalytics #DataScience #MachineLearning #TechNews)

Lưu ý: Chỉ trả về nội dung bài viết, không cần thêm các câu mào đầu như "Dưới đây là bài viết...".
"""
    return call_groq(prompt)

def generate_infographic_html(paper_info):
    """Dùng Groq AI (LLaMA 3.3 70B) để tạo infographic dạng sơ đồ kiến trúc đẹp, sát nội dung bài báo"""
    print("Đang nhờ Groq AI thiết kế architecture diagram...", flush=True)
    today = datetime.datetime.now().strftime("%d/%m/%Y")

    prompt = f"""Bạn là một UI/UX designer chuyên tạo research infographic và architecture diagram cho mạng xã hội khoa học.
Hãy tạo một file HTML/CSS/SVG hoàn chỉnh (1200x675px) minh họa kiến trúc/pipeline/sơ đồ logic của bài báo khoa học dưới đây.

Thông tin bài báo:
- Tiêu đề: {paper_info['title']}
- Tác giả: {paper_info['authors']}
- Tóm tắt: {paper_info['abstract']}

== YÊU CẦU BỐ CỤC (3 CỘT) ==

[CỘT TRÁI - 280px] PAPER INFO PANEL:
  • Badge "RESEARCH INSIGHT" màu gradient nổi bật góc trên
  • Tên lĩnh vực (Computer Vision / NLP / Data Analytics / Robotics...)
  • Tiêu đề bài báo rút gọn (tối đa 10 từ), font lớn, bold, màu trắng
  • Tên tác giả đầu tiên + "et al." nếu nhiều người
  • Divider line
  • 3-4 KEY FINDINGS dạng bullet ✦ với nội dung CỤ THỂ từ abstract
  • Footer: "arxiv.org · {today}"

[CỘT GIỮA - 640px] ARCHITECTURE DIAGRAM (phần quan trọng nhất):
  Đây phải là một SƠ ĐỒ TRỰC QUAN thật sự với các node hộp nối nhau bằng mũi tên.
  Dựa vào abstract, phân tích pipeline/kiến trúc của phương pháp và vẽ:
  • 3-6 NODE dạng hộp bo tròn (rounded rectangle), mỗi node có: icon emoji + tên giai đoạn + mô tả ngắn
  • Mũi tên SVG (<line> + <marker arrowhead>) nối các node lại
  • Layout ngang (left→right) hoặc dọc (top→bottom) tùy pipeline
  • Màu node khác nhau: INPUT=xanh lá gradient, PROCESS=xanh tím gradient, OUTPUT=cam vàng gradient
  • Tiêu đề sơ đồ: "Pipeline Overview" hoặc "System Architecture"
  • Có thể dùng CSS flexbox/grid để bố trí các node + SVG overlay cho mũi tên

[CỘT PHẢI - 280px] METRICS & TAGS PANEL:
  • Tiêu đề "KEY METRICS" hoặc "CONTRIBUTIONS"
  • 2-3 metric dạng số lớn hoặc contribution card (lấy từ abstract nếu có số liệu)
  • 4-5 KEYWORD TAGS dạng pill/badge màu sắc
  • Icon visual nhỏ

== YÊU CẦU KỸ THUẬT ==
1. Kích thước: html,body width=1200px height=675px overflow=hidden tuyệt đối.
2. Nền: dark gradient đẹp phù hợp chủ đề (dark navy, dark purple, dark teal...).
3. Font: @import Google Fonts 'Inter' hoặc 'Space Grotesk'.
4. Glassmorphism: background: rgba(255,255,255,0.08); backdrop-filter: blur(10px); border: 1px solid rgba(255,255,255,0.15).
5. Tất cả text phải READABLE, contrast đủ cao, font-size tối thiểu 11px.
6. Sử dụng position: absolute hoặc flexbox để layout chính xác, KHÔNG overflow.

== QUY TẮC BẮT BUỘC ==
- Chỉ trả về CODE HTML thuần túy bắt đầu <!DOCTYPE html> kết thúc </html>.
- KHÔNG thêm ```html, KHÔNG giải thích, KHÔNG comment ngoài code HTML.
- Nội dung node/text PHẢI lấy từ bài báo thực — KHÔNG dùng "Input Data", "Process", "Output" chung chung.
- Diagram PHẢI phản ánh đúng logic/pipeline của phương pháp được mô tả trong abstract.
- Diagram của cột giữa: dùng display:flex, flex-direction:row, align-items:center, các node là div bo tròn, giữa các node là ➡️.
"""
    try:
        html_text = call_groq(prompt, max_tokens=8192)
        # Loại bỏ markdown code fence nếu model vẫn thêm vào
        if html_text.startswith("```"):
            lines = html_text.split("\n")
            html_text = "\n".join(lines[1:-1] if lines[-1].strip() == "```" else lines[1:])
        return html_text
    except Exception as e:
        print(f"Lỗi khi tạo infographic HTML: {e}", flush=True)
        # Fallback: trả về HTML đơn giản
        title = html.escape(paper_info['title'][:80])
        return f"""<!DOCTYPE html>
<html><head><meta charset="UTF-8">
<style>
  body {{ width:1200px; height:675px; margin:0; background:linear-gradient(135deg,#1a1a2e,#16213e,#0f3460);
          display:flex; flex-direction:column; align-items:center; justify-content:center;
          font-family:Arial,sans-serif; color:white; overflow:hidden; }}
  h1 {{ font-size:36px; text-align:center; max-width:900px; }}
  p {{ font-size:20px; opacity:0.7; }}
</style></head>
<body>
  <h1>{title}</h1>
  <p>Data Analytics Research Insight</p>
</body></html>"""

def render_diagram_image(paper_info):
    """Render infographic HTML/CSS thành ảnh PNG bằng Playwright (Chromium headless)"""
    print("Đang render infographic minh họa bằng Playwright...", flush=True)

    os.makedirs("posts", exist_ok=True)
    today_str = datetime.datetime.now().strftime("%Y-%m-%d")
    filename = f"posts/{today_str}.png"

    html_content = generate_infographic_html(paper_info)

    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={"width": 1200, "height": 675})
        page.set_content(html_content, wait_until="networkidle")  # chờ Google Fonts load
        page.screenshot(path=filename)
        browser.close()

    print(f"Đã lưu ảnh infographic vào file: {filename}", flush=True)
    return filename


# ═══════════════════════════════════════════════════════════════
# LEGACY: đoạn HTML template cũ được giữ lại phòng khi cần debug
# ═══════════════════════════════════════════════════════════════
def _legacy_build_diagram_html(steps):
    """[LEGACY] Template HTML/CSS cũ cho sơ đồ Input -> Process -> Output"""
    title = html.escape(steps["title"])
    input_text = html.escape(steps["input"])
    process_text = html.escape(steps["process"])
    output_text = html.escape(steps["output"])

    return f"""<!DOCTYPE html>
<html lang="vi">
<head>
<meta charset="UTF-8">
<style>
  * {{ margin: 0; padding: 0; box-sizing: border-box; }}
  html, body {{
    width: 1200px;
    height: 675px;
    font-family: 'Segoe UI', 'Noto Sans', Arial, sans-serif;
    background: linear-gradient(135deg, #0f2027 0%, #203a43 45%, #2c5364 100%);
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    overflow: hidden;
  }}
  .title {{
    color: #ffffff;
    font-size: 42px;
    font-weight: 700;
    text-align: center;
    max-width: 1000px;
    margin-bottom: 60px;
    text-shadow: 0 2px 12px rgba(0,0,0,0.35);
  }}
  .flow {{
    display: flex;
    align-items: center;
    gap: 28px;
  }}
  .card {{
    width: 300px;
    min-height: 240px;
    background: rgba(255, 255, 255, 0.97);
    border-radius: 24px;
    padding: 32px 24px;
    display: flex;
    flex-direction: column;
    align-items: center;
    text-align: center;
    box-shadow: 0 20px 40px rgba(0, 0, 0, 0.25);
    position: relative;
  }}
  .badge {{
    position: absolute;
    top: -22px;
    width: 44px;
    height: 44px;
    border-radius: 50%;
    background: linear-gradient(135deg, #00c6ff, #0072ff);
    color: white;
    font-weight: 700;
    font-size: 20px;
    display: flex;
    align-items: center;
    justify-content: center;
    box-shadow: 0 6px 16px rgba(0, 114, 255, 0.5);
  }}
  .icon {{
    font-size: 48px;
    margin: 18px 0 10px;
  }}
  .label {{
    color: #0072ff;
    font-weight: 700;
    font-size: 20px;
    letter-spacing: 1px;
    margin-bottom: 14px;
  }}
  .content {{
    color: #1a2b3c;
    font-size: 22px;
    font-weight: 600;
    line-height: 1.35;
  }}
  .arrow {{
    color: #ffffff;
    font-size: 46px;
    opacity: 0.85;
  }}
</style>
</head>
<body>
  <div class="title">{title}</div>
  <div class="flow">
    <div class="card">
      <div class="badge">1</div>
      <div class="icon">📥</div>
      <div class="label">INPUT</div>
      <div class="content">{input_text}</div>
    </div>
    <div class="arrow">&#8594;</div>
    <div class="card">
      <div class="badge">2</div>
      <div class="icon">⚙️</div>
      <div class="label">PROCESS</div>
      <div class="content">{process_text}</div>
    </div>
    <div class="arrow">&#8594;</div>
    <div class="card">
      <div class="badge">3</div>
      <div class="icon">📤</div>
      <div class="label">OUTPUT</div>
      <div class="content">{output_text}</div>
    </div>
  </div>
</body>
</html>"""



def post_to_linkedin(content, image_path=None):
    """Đăng bài lên LinkedIn qua API"""
    if not LINKEDIN_ACCESS_TOKEN:
        print("Bỏ qua bước đăng LinkedIn vì thiếu Access Token.", flush=True)
        return

    print("Đang kết nối với LinkedIn...", flush=True)
    headers = {
        'Authorization': f'Bearer {LINKEDIN_ACCESS_TOKEN}',
        'X-Restli-Protocol-Version': '2.0.0',
        'Content-Type': 'application/json'
    }
    
    try:
        # Lấy thông tin URN của user
        user_info_resp = requests.get('https://api.linkedin.com/v2/userinfo', headers=headers, timeout=15)
        if user_info_resp.status_code != 200:
            print(f"Lỗi khi lấy thông tin user LinkedIn: {user_info_resp.text}", flush=True)
            return
            
        author_urn = f"urn:li:person:{user_info_resp.json()['sub']}"

        # Nếu có ảnh sơ đồ minh họa, upload trước để lấy asset URN
        media_category = "NONE"
        media_assets = []
        if image_path and os.path.exists(image_path):
            asset_urn = upload_image_to_linkedin(author_urn, image_path, headers)
            if asset_urn:
                media_category = "IMAGE"
                media_assets = [{
                    "status": "READY",
                    "description": {"text": "Sơ đồ minh họa cách hoạt động"},
                    "media": asset_urn,
                    "title": {"text": "Cách hoạt động"}
                }]

        # Đăng bài
        post_url = 'https://api.linkedin.com/v2/ugcPosts'
        post_data = {
            "author": author_urn,
            "lifecycleState": "PUBLISHED",
            "specificContent": {
                "com.linkedin.ugc.ShareContent": {
                    "shareCommentary": {
                        "text": content
                    },
                    "shareMediaCategory": media_category,
                    **({"media": media_assets} if media_assets else {})
                }
            },
            "visibility": {
                "com.linkedin.ugc.MemberNetworkVisibility": "PUBLIC"
            }
        }
        
        if not TEST_MODE:
            post_resp = requests.post(post_url, headers=headers, json=post_data, timeout=15)
            if post_resp.status_code == 201:
                print("Đã đăng bài lên LinkedIn thành công!", flush=True)
            else:
                print(f"Lỗi khi đăng bài: {post_resp.text}", flush=True)
        else:
            print("[TEST MODE] Giả lập đăng bài thành công lên LinkedIn.", flush=True)
            
    except Exception as e:
        print(f"Lỗi trong quá trình xử lý LinkedIn: {e}", flush=True)

def upload_image_to_linkedin(author_urn, image_path, headers):
    """Đăng ký upload ảnh lên LinkedIn và trả về asset URN"""
    try:
        register_url = 'https://api.linkedin.com/v2/assets?action=registerUpload'
        register_data = {
            "registerUploadRequest": {
                "recipes": ["urn:li:digitalmediaRecipe:feedshare-image"],
                "owner": author_urn,
                "serviceRelationships": [{
                    "relationshipType": "OWNER",
                    "identifier": "urn:li:userGeneratedContent"
                }]
            }
        }
        register_resp = requests.post(register_url, headers=headers, json=register_data, timeout=15)
        if register_resp.status_code != 200:
            print(f"Lỗi khi đăng ký upload ảnh: {register_resp.text}", flush=True)
            return None

        register_value = register_resp.json()['value']
        upload_url = register_value['uploadMechanism']['com.linkedin.digitalmedia.uploading.MediaUploadHttpRequest']['uploadUrl']
        asset_urn = register_value['asset']

        with open(image_path, 'rb') as f:
            image_bytes = f.read()

        upload_headers = {'Authorization': f"Bearer {LINKEDIN_ACCESS_TOKEN}"}
        upload_resp = requests.put(upload_url, headers=upload_headers, data=image_bytes, timeout=30)
        if upload_resp.status_code not in (200, 201):
            print(f"Lỗi khi tải ảnh lên LinkedIn: {upload_resp.status_code}", flush=True)
            return None

        return asset_urn
    except Exception as e:
        print(f"Lỗi khi upload ảnh lên LinkedIn: {e}", flush=True)
        return None

def save_post_to_file(content):
    """Lưu bài viết vào thư mục posts/ để đẩy lên GitHub"""
    os.makedirs("posts", exist_ok=True)
    today_str = datetime.datetime.now().strftime("%Y-%m-%d")
    filename = f"posts/{today_str}.md"
    
    with open(filename, "w", encoding="utf-8") as f:
        f.write(content)
    print(f"Đã lưu bài viết vào file: {filename}", flush=True)

def main():
    try:
        # Bước 1: Lấy thông tin bài báo
        paper_info = fetch_latest_arxiv_paper()
        
        # Bước 2: Nhờ AI viết bài
        post_content = generate_linkedin_post(paper_info)
        print("\n--- NỘI DUNG BÀI VIẾT TẠO BỞI AI ---\n", flush=True)
        print(post_content, flush=True)
        print("\n------------------------------------\n", flush=True)
        
        # Bước 3: Lưu thành file markdown
        save_post_to_file(post_content)

        # Bước 3b: Gemini thiết kế infographic HTML/CSS và render bằng Playwright
        image_path = None
        try:
            image_path = render_diagram_image(paper_info)
        except Exception as e:
            print(f"Bỏ qua bước tạo infographic minh họa do lỗi: {e}", flush=True)

        # Bước 4: Đăng lên LinkedIn (kèm sơ đồ minh họa nếu có)
        post_to_linkedin(post_content, image_path=image_path)
        
        print("Hoàn thành quy trình tự động của ngày hôm nay!", flush=True)
        
    except Exception as e:
        print(f"Có lỗi xảy ra: {e}", flush=True)
        sys.exit(1)

if __name__ == "__main__":
    main()
