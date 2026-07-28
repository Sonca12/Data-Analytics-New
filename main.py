import os
import datetime
import json
import html
import urllib.request
import feedparser
import requests
import google.generativeai as genai
from dotenv import load_dotenv
from playwright.sync_api import sync_playwright
import sys

# Cấu hình in tiếng Việt trên Windows
sys.stdout.reconfigure(encoding='utf-8')

# 1. Load biến môi trường
load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
LINKEDIN_ACCESS_TOKEN = os.getenv("LINKEDIN_ACCESS_TOKEN")
TEST_MODE = os.getenv("TEST_MODE", "true").lower() == "true"

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
    """Dùng Gemini AI để viết bài đăng LinkedIn"""
    print("Đang nhờ Gemini AI phân tích và viết bài...", flush=True)
    genai.configure(api_key=GEMINI_API_KEY)
    model = genai.GenerativeModel('gemini-3.5-flash')
    
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
    response = model.generate_content(prompt)
    return response.text.strip()

def generate_infographic_html(paper_info):
    """Dùng Gemini AI để tạo toàn bộ HTML/CSS infographic đẹp, chi tiết, sát nội dung bài báo"""
    print("Đang nhờ Gemini AI thiết kế infographic HTML/CSS...", flush=True)
    genai.configure(api_key=GEMINI_API_KEY)
    model = genai.GenerativeModel('gemini-3.5-flash')

    prompt = f"""Bạn là một UI designer chuyên tạo infographic đẹp cho mạng xã hội.
Hãy tạo một file HTML/CSS hoàn chỉnh (1200x675px) làm ảnh bìa LinkedIn cho bài báo khoa học dưới đây.

Thông tin bài báo:
- Tiêu đề: {paper_info['title']}
- Tác giả: {paper_info['authors']}
- Tóm tắt: {paper_info['abstract']}

Yêu cầu THIẾT KẾ (quan trọng):
1. Kích thước cố định: width=1200px, height=675px, overflow=hidden, không scroll.
2. Màu sắc: Tạo palette màu gradient đẹp PHÙ HỢP với chủ đề nghiên cứu (ví dụ: Computer Vision → tím/xanh đậm, NLP → cam/vàng, Finance → xanh lá/vàng gold, Healthcare → xanh lam/trắng...).
3. Font: Sử dụng Google Fonts (Inter hoặc Outfit) import qua @import.
4. Layout PHẢI bao gồm đủ các thành phần sau:
   a. HEADER: Logo/badge "RESEARCH INSIGHT" + tên lĩnh vực nghiên cứu (ví dụ: "Computer Vision" / "NLP" / "Data Analytics")
   b. TIÊU ĐỀ CHÍNH: Tên bài báo (rút gọn nếu quá dài, tối đa 12 từ), font lớn, nổi bật
   c. TÁC GIẢ: Hiển thị tên tác giả (rút gọn nếu nhiều)
   d. KEY FINDINGS: 3-4 bullet points tóm tắt phát hiện/đóng góp chính của bài báo (trích từ abstract, bằng tiếng Anh hoặc tiếng Việt đều được)
   e. METHODOLOGY FLOW: Sơ đồ 3 bước (Input → Process → Output) nhưng với nội dung CHI TIẾT và CỤ THỂ từ bài báo (không dùng placeholder chung chung)
   f. KEYWORD TAGS: 4-5 tag từ khóa liên quan (ví dụ: #DeepLearning #CV #Benchmark)
   g. FOOTER: "Source: arxiv.org" + ngày hiện tại
5. Hiệu ứng: Glassmorphism, gradient nền, box-shadow, border-radius bo tròn đẹp.
6. Đảm bảo tất cả text KHÔNG bị tràn ra ngoài khung 1200x675px.

Quan trọng:
- Chỉ trả về CODE HTML thuần túy, bắt đầu bằng <!DOCTYPE html> và kết thúc bằng </html>.
- KHÔNG thêm markdown, KHÔNG thêm giải thích, KHÔNG dùng ```html wrapper.
- Nội dung PHẢI cụ thể, sát với bài báo được cung cấp, KHÔNG dùng nội dung mẫu/placeholder.
"""
    try:
        response = model.generate_content(prompt)
        html_text = response.text.strip()
        # Loại bỏ markdown code fence nếu Gemini vẫn thêm vào
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
