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

def fetch_latest_kdnuggets_article():
    """Lấy bài viết mới nhất từ KDnuggets RSS"""
    print("Đang tìm bài viết mới nhất trên KDnuggets...", flush=True)
    url = 'https://www.kdnuggets.com/feed'
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
    
    response = requests.get(url, headers=headers, timeout=15)
    feed = feedparser.parse(response.content)
    
    if not feed.entries:
        raise Exception("Không tìm thấy bài viết nào trên KDnuggets!")
        
    entry = feed.entries[0]
    author = entry.get('author', 'KDnuggets Team')
    summary_raw = entry.get('summary', entry.get('description', ''))
    
    import re
    clean_summary = re.sub(r'<[^>]+>', '', summary_raw).strip()
    
    return {
        "title": entry.title,
        "summary": clean_summary,
        "author": author,
        "link": entry.link
    }

def generate_linkedin_post(article_info):
    """Dùng Groq AI (LLaMA 3.3 70B) để viết bài đăng LinkedIn chuẩn Data Analyst thực chiến & cuốn hút"""
    print("Đang nhờ Groq AI phân tích và viết bài câu chuyện thực chiến...", flush=True)

    prompt = f"""Bạn là một Data Analyst & Data Engineer dày dặn kinh nghiệm đang xây dựng thương hiệu cá nhân trên LinkedIn.
Hãy đọc bài viết chuyên môn dưới đây từ KDnuggets và viết một bài đăng LinkedIn bằng tiếng Việt cực kỳ cuốn hút, thực chiến và dễ tiếp thu.

Thông tin bài viết:
- Tiêu đề: {article_info['title']}
- Tác giả: {article_info['author']}
- Link bài gốc: {article_info['link']}
- Tóm tắt nội dung: {article_info['summary']}

Yêu cầu cấu trúc & phong cách bài viết:
1. HOOK MỞ ĐẦU (1-2 câu + emoji):
   - Đặt một vấn đề/thách thức/câu hỏi thực tế mà nhiều Data Analyst / Data Engineer hay gặp phải trong công việc hàng ngày.
   - Không tóm tắt bài báo khô khan, hãy biến nó thành một câu chuyện hoặc bài học kinh nghiệm công việc!

2. WORKFLOW / CÁCH HOẠT ĐỘNG CHÍNH (3-4 bullet points ngắn gọn, cô đọng):
   - Giải thích bản chất cách hoạt động, các bước thực hiện hoặc phương pháp/công cụ được nói tới.
   - Sử dụng ngôn từ thực chiến, dễ hiểu (vd: Data Ingestion -> Preprocessing -> Model/Logic -> Output).

3. BÀI HỌC & ỨNG DỤNG CHO DATA ANALYST (2-3 ý cụ thể):
   - Bài học rút ra cho công việc Data Analytics/Data Science thực tế (vd: tối ưu SQL query, xử lý data pipeline, chọn model, dashboard insight...).
   - Tại sao kỹ thuật/tư duy này lại quan trọng và giúp tăng hiệu suất công việc?

4. KẾT LUẬN & TƯƠNG TÁC:
   - Đính kèm link bài viết gốc.
   - Đặt 1 câu hỏi mở thực tế để khơi gợi thảo luận bên dưới phần bình luận.

5. HASHTAGS:
   - Thêm 4-5 hashtag phù hợp: #DataAnalytics #DataScience #Python #DataEngineering #BusinessIntelligence #TechInsights

Lưu ý:
- Chỉ trả về nội dung bài viết, không thêm lời mở đầu hay kết thúc của AI.
- Giữ văn phong chuyên nghiệp nhưng thân thiện, truyền cảm hứng.
"""
    return call_groq(prompt)

def generate_infographic_html(article_info):
    """Dùng Groq AI (LLaMA 3.3 70B) để tạo infographic dạng sơ đồ workflow kỹ thuật đẹp, sát nội dung bài viết"""
    print("Đang nhờ Groq AI thiết kế workflow diagram...", flush=True)
    today = datetime.datetime.now().strftime("%d/%m/%Y")

    prompt = f"""Bạn là UI/UX designer đỉnh cao. Điền nội dung chuyên môn từ bài viết dưới đây vào skeleton HTML để tạo ra một Technical Workflow Diagram (1200x675px) chuyên nghiệp.

Thông tin bài viết:
- Tiêu đề: {article_info['title']}
- Tác giả: {article_info['author']}
- Tóm tắt nội dung: {article_info['summary']}

SKELETON HTML (Hãy giữ nguyên cấu trúc CSS & HTML, chỉ điền nội dung vào các vị trí [PLACEHOLDER]):

<!DOCTYPE html>
<html><head><meta charset="UTF-8">
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700;800&display=swap');
*{{margin:0;padding:0;box-sizing:border-box;}}
html,body{{width:1200px;height:675px;overflow:hidden;font-family:'Inter',sans-serif;
  background:linear-gradient(135deg,[BG1] 0%,[BG2] 50%,[BG3] 100%);}}
.wrap{{display:flex;flex-direction:column;width:1200px;height:675px;padding:20px 24px;gap:14px;}}
.header{{display:flex;justify-content:space-between;align-items:center;background:rgba(255,255,255,0.07);
  backdrop-filter:blur(12px);border:1px solid rgba(255,255,255,0.13);border-radius:14px;padding:12px 20px;height:68px;}}
.header-left{{display:flex;align-items:center;gap:12px;}}
.badge{{background:linear-gradient(90deg,#00f2fe,#4facfe);color:#0b0f19;font-size:10px;font-weight:800;
  letter-spacing:1.5px;padding:5px 12px;border-radius:20px;text-transform:uppercase;}}
.header-title{{font-size:18px;font-weight:800;color:#fff;max-width:700px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;}}
.header-sub{{font-size:11px;color:rgba(255,255,255,0.5);font-weight:600;}}

.main-body{{flex:1;display:flex;background:rgba(255,255,255,0.04);backdrop-filter:blur(8px);
  border:1px solid rgba(255,255,255,0.09);border-radius:16px;padding:20px;flex-direction:column;justify-content:center;}}
.workflow-title{{font-size:13px;font-weight:700;color:rgba(255,255,255,0.6);letter-spacing:1.5px;
  text-transform:uppercase;text-align:center;margin-bottom:18px;}}
.pipeline{{display:flex;align-items:center;justify-content:space-between;gap:6px;width:100%;}}
.stage{{flex:1;display:flex;flex-direction:column;background:rgba(255,255,255,0.06);border:1px solid rgba(255,255,255,0.12);
  border-radius:14px;padding:14px 12px;min-height:280px;position:relative;box-shadow:0 8px 24px rgba(0,0,0,0.2);}}
.stage-step{{font-size:10px;font-weight:800;color:rgba(255,255,255,0.4);letter-spacing:1px;margin-bottom:6px;}}
.stage-header{{display:flex;align-items:center;gap:8px;margin-bottom:8px;}}
.stage-icon{{font-size:22px;}}
.stage-name{{font-size:13px;font-weight:800;color:#fff;line-height:1.2;}}
.stage-divider{{height:2px;border-radius:2px;margin:6px 0 10px 0;}}
.s1 .stage-divider{{background:linear-gradient(90deg,#00b09b,#96c93d);}}
.s2 .stage-divider{{background:linear-gradient(90deg,#00c6ff,#0072ff);}}
.s3 .stage-divider{{background:linear-gradient(90deg,#7209b7,#4361ee);}}
.s4 .stage-divider{{background:linear-gradient(90deg,#f72585,#b5179e);}}
.s5 .stage-divider{{background:linear-gradient(90deg,#f7971e,#ffd200);}}
.stage-desc{{font-size:10.5px;color:rgba(255,255,255,0.85);line-height:1.45;display:flex;flex-direction:column;gap:6px;}}
.stage-bullet{{display:flex;align-items:flex-start;gap:4px;}}
.arrow{{font-size:22px;color:rgba(255,255,255,0.4);flex-shrink:0;user-select:none;}}

.bottom-bar{{display:flex;gap:14px;height:95px;}}
.card-takeaway{{flex:1.2;background:rgba(255,255,255,0.07);backdrop-filter:blur(12px);
  border:1px solid rgba(255,255,255,0.13);border-radius:14px;padding:12px 16px;display:flex;flex-direction:column;justify-content:center;}}
.ct-title{{font-size:10px;font-weight:700;color:#00f2fe;letter-spacing:1px;text-transform:uppercase;margin-bottom:4px;}}
.ct-text{{font-size:11.5px;font-weight:600;color:#fff;line-height:1.35;}}
.card-tools{{flex:0.8;background:rgba(255,255,255,0.07);backdrop-filter:blur(12px);
  border:1px solid rgba(255,255,255,0.13);border-radius:14px;padding:12px 16px;display:flex;flex-direction:column;justify-content:center;}}
.tools-title{{font-size:10px;font-weight:700;color:rgba(255,255,255,0.5);letter-spacing:1px;text-transform:uppercase;margin-bottom:6px;}}
.tools-pills{{display:flex;flex-wrap:wrap;gap:6px;}}
.pill{{background:rgba(255,255,255,0.12);color:#fff;font-size:10px;font-weight:600;padding:3px 9px;border-radius:12px;}}
</style></head>
<body>
<div class="wrap">
  <div class="header">
    <div class="header-left">
      <div class="badge">TECHNICAL WORKFLOW</div>
      <div class="header-title">[TIÊU ĐỀ RÚT GỌN MAX 8 TỪ]</div>
    </div>
    <div class="header-sub">KDnuggets Insight · {today}</div>
  </div>

  <div class="main-body">
    <div class="workflow-title">⚙️ [TÊN WORKFLOW QUY TRÌNH KỸ THUẬT: e.g. Data Pipeline & Analytics Workflow]</div>
    <div class="pipeline">
      <div class="stage s1">
        <div class="stage-step">STAGE 01</div>
        <div class="stage-header"><div class="stage-icon">[EMOJI]</div><div class="stage-name">[STAGE 1 TÊN]</div></div>
        <div class="stage-divider"></div>
        <div class="stage-desc">
          <div class="stage-bullet">• [Chi tiết bước 1]</div>
          <div class="stage-bullet">• [Chi tiết 2]</div>
        </div>
      </div>
      <div class="arrow">➔</div>
      <div class="stage s2">
        <div class="stage-step">STAGE 02</div>
        <div class="stage-header"><div class="stage-icon">[EMOJI]</div><div class="stage-name">[STAGE 2 TÊN]</div></div>
        <div class="stage-divider"></div>
        <div class="stage-desc">
          <div class="stage-bullet">• [Chi tiết bước 2]</div>
          <div class="stage-bullet">• [Chi tiết 2]</div>
        </div>
      </div>
      <div class="arrow">➔</div>
      <div class="stage s3">
        <div class="stage-step">STAGE 03</div>
        <div class="stage-header"><div class="stage-icon">[EMOJI]</div><div class="stage-name">[STAGE 3 TÊN]</div></div>
        <div class="stage-divider"></div>
        <div class="stage-desc">
          <div class="stage-bullet">• [Chi tiết bước 3]</div>
          <div class="stage-bullet">• [Chi tiết 2]</div>
        </div>
      </div>
      <div class="arrow">➔</div>
      <div class="stage s4">
        <div class="stage-step">STAGE 04</div>
        <div class="stage-header"><div class="stage-icon">[EMOJI]</div><div class="stage-name">[STAGE 4 TÊN]</div></div>
        <div class="stage-divider"></div>
        <div class="stage-desc">
          <div class="stage-bullet">• [Chi tiết bước 4]</div>
          <div class="stage-bullet">• [Chi tiết 2]</div>
        </div>
      </div>
      <div class="arrow">➔</div>
      <div class="stage s5">
        <div class="stage-step">STAGE 05</div>
        <div class="stage-header"><div class="stage-icon">[EMOJI]</div><div class="stage-name">[STAGE 5 TÊN]</div></div>
        <div class="stage-divider"></div>
        <div class="stage-desc">
          <div class="stage-bullet">• [Chi tiết bước 5]</div>
          <div class="stage-bullet">• [Chi tiết 2]</div>
        </div>
      </div>
    </div>
  </div>

  <div class="bottom-bar">
    <div class="card-takeaway">
      <div class="ct-title">💡 Core Value & Takeaway</div>
      <div class="ct-text">[BÀI HỌC VÀ GIÁ TRỊ CỐT LÕI CỦA NỘI DUNG NÀY]</div>
    </div>
    <div class="card-tools">
      <div class="tools-title">🛠️ Tech Stack & Keywords</div>
      <div class="tools-pills">
        <div class="pill">#[TOOL_1]</div>
        <div class="pill">#[TOOL_2]</div>
        <div class="pill">#[TOOL_3]</div>
        <div class="pill">#[TOOL_4]</div>
      </div>
    </div>
  </div>
</div>
</body>
</html>

Hướng dẫn điền:
- [BG1],[BG2],[BG3]: 3 màu hex tối hiện đại (VD: #0b0f19, #111827, #1f2937 hoặc dark navy/dark cyan)
- [STAGE x TÊN]: tên CỤ THỂ theo quy trình hoạt động chuyên môn từ bài viết
- [TOOL_x]: tên công nghệ, công cụ hoặc từ khóa liên quan (Python, SQL, Pandas, Scikit-learn, Feature Engineering...)
- Trả về HTML hoàn chỉnh duy nhất, KHÔNG giải thích thêm.
"""
    try:
        html_text = call_groq(prompt, max_tokens=8192)
        if html_text.startswith("```"):
            lines = html_text.split("\n")
            html_text = "\n".join(lines[1:-1] if lines[-1].strip() == "```" else lines[1:])
        return html_text
    except Exception as e:
        print(f"Lỗi khi tạo infographic HTML: {e}", flush=True)
        title = html.escape(article_info['title'][:80])
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
  <p>Data Analytics Insight</p>
</body></html>"""

def render_diagram_image(article_info):
    """Render infographic HTML/CSS thành ảnh PNG bằng Playwright (Chromium headless)"""
    print("Đang render infographic minh họa bằng Playwright...", flush=True)

    os.makedirs("posts", exist_ok=True)
    today_str = datetime.datetime.now().strftime("%Y-%m-%d")
    filename = f"posts/{today_str}.png"

    html_content = generate_infographic_html(article_info)

    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={"width": 1200, "height": 675})
        page.set_content(html_content, wait_until="networkidle")
        page.screenshot(path=filename)
        browser.close()

    print(f"Đã lưu ảnh infographic vào file: {filename}", flush=True)
    return filename

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
        user_info_resp = requests.get('https://api.linkedin.com/v2/userinfo', headers=headers, timeout=15)
        if user_info_resp.status_code != 200:
            print(f"Lỗi khi lấy thông tin user LinkedIn: {user_info_resp.text}", flush=True)
            return
            
        author_urn = f"urn:li:person:{user_info_resp.json()['sub']}"

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
        # Bước 1: Lấy thông tin bài viết từ KDnuggets
        article_info = fetch_latest_kdnuggets_article()
        
        # Bước 2: Nhờ AI viết bài
        post_content = generate_linkedin_post(article_info)
        print("\n--- NỘI DUNG BÀI VIẾT TẠO BỞI AI ---\n", flush=True)
        print(post_content, flush=True)
        print("\n------------------------------------\n", flush=True)
        
        # Bước 3: Lưu thành file markdown
        save_post_to_file(post_content)

        # Bước 3b: Groq thiết kế workflow diagram HTML/CSS và render bằng Playwright
        image_path = None
        try:
            image_path = render_diagram_image(article_info)
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
