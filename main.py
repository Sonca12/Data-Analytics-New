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
    arxiv_id = paper_info['link'].split('/')[-1]

    prompt = f"""Bạn là UI/UX designer. Điền nội dung từ bài báo vào skeleton HTML sau rồi trả về file HTML hoàn chỉnh.

Thông tin bài báo:
- Tiêu đề: {paper_info['title']}
- Tác giả: {paper_info['authors']}
- Tóm tắt: {paper_info['abstract']}

SKELETON HTML (điền vào các [PLACEHOLDER], giữ nguyên CSS):

<!DOCTYPE html>
<html><head><meta charset="UTF-8">
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700;800&display=swap');
*{{margin:0;padding:0;box-sizing:border-box;}}
html,body{{width:1200px;height:675px;overflow:hidden;font-family:'Inter',sans-serif;
  background:linear-gradient(135deg,[BG1] 0%,[BG2] 50%,[BG3] 100%);}}
.wrap{{display:flex;width:1200px;height:675px;padding:18px;gap:14px;align-items:stretch;}}
.left{{width:255px;flex-shrink:0;background:rgba(255,255,255,0.07);backdrop-filter:blur(12px);
  border:1px solid rgba(255,255,255,0.13);border-radius:16px;padding:18px;
  display:flex;flex-direction:column;gap:8px;}}
.badge{{display:inline-block;background:linear-gradient(90deg,#f72585,#7209b7);color:#fff;
  font-size:9px;font-weight:700;letter-spacing:1.5px;padding:4px 10px;border-radius:20px;}}
.field{{font-size:10px;color:rgba(255,255,255,0.5);font-weight:600;letter-spacing:1px;text-transform:uppercase;}}
.ptitle{{font-size:17px;font-weight:800;color:#fff;line-height:1.3;}}
.auth{{font-size:11px;color:rgba(255,255,255,0.55);}}
.hr{{height:1px;background:rgba(255,255,255,0.13);margin:2px 0;}}
.finds{{display:flex;flex-direction:column;gap:5px;flex:1;overflow:hidden;}}
.find{{font-size:10.5px;color:rgba(255,255,255,0.85);line-height:1.4;}}
.foot{{font-size:9.5px;color:rgba(255,255,255,0.35);margin-top:auto;}}
.mid{{flex:1;background:rgba(255,255,255,0.05);backdrop-filter:blur(8px);
  border:1px solid rgba(255,255,255,0.1);border-radius:16px;padding:16px 12px;
  display:flex;flex-direction:column;}}
.dtitle{{font-size:12px;font-weight:700;color:rgba(255,255,255,0.6);letter-spacing:1px;
  text-transform:uppercase;text-align:center;margin-bottom:10px;}}
.pipeline{{display:flex;align-items:center;justify-content:center;flex:1;gap:4px;padding:0 4px;}}
.node{{display:flex;flex-direction:column;align-items:center;justify-content:center;
  width:118px;height:148px;border-radius:14px;padding:10px 8px;text-align:center;flex-shrink:0;}}
.ni{{font-size:28px;margin-bottom:5px;}}
.nl{{font-size:11.5px;font-weight:700;color:#fff;line-height:1.2;margin-bottom:3px;}}
.nd{{font-size:9.5px;color:rgba(255,255,255,0.82);line-height:1.3;}}
.n1{{background:linear-gradient(135deg,#00b09b,#96c93d);}}
.n2{{background:linear-gradient(135deg,#4776e6,#8e54e9);}}
.n3{{background:linear-gradient(135deg,#7209b7,#3a0ca3);}}
.n4{{background:linear-gradient(135deg,#3a0ca3,#4361ee);}}
.n5{{background:linear-gradient(135deg,#f7971e,#ffd200);}}
.arr{{font-size:22px;color:rgba(255,255,255,0.45);flex-shrink:0;}}
.dfoot{{font-size:9px;color:rgba(255,255,255,0.3);text-align:center;margin-top:8px;}}
.right{{width:232px;flex-shrink:0;background:rgba(255,255,255,0.07);backdrop-filter:blur(12px);
  border:1px solid rgba(255,255,255,0.13);border-radius:16px;padding:18px;
  display:flex;flex-direction:column;gap:10px;}}
.mtitle{{font-size:10px;font-weight:700;color:rgba(255,255,255,0.5);letter-spacing:1px;text-transform:uppercase;}}
.mcard{{background:rgba(255,255,255,0.09);border-radius:10px;padding:10px 12px;}}
.mnum{{font-size:24px;font-weight:800;color:#fff;}}
.mlbl{{font-size:10px;color:rgba(255,255,255,0.55);margin-top:1px;}}
.tags{{display:flex;flex-direction:column;gap:5px;margin-top:auto;}}
.tag{{padding:5px 10px;border-radius:20px;font-size:10.5px;font-weight:600;color:#fff;text-align:center;}}
</style></head>
<body><div class="wrap">
<div class="left">
  <div class="badge">RESEARCH INSIGHT</div>
  <div class="field">[LĨNH VỰC: Robotics / Computer Vision / NLP / ...]</div>
  <div class="ptitle">[TIÊU ĐỀ RÚT GỌN ≤10 TỪ]</div>
  <div class="auth">[TÁC GIẢ ĐẦU] et al.</div>
  <div class="hr"></div>
  <div class="finds">
    <div class="find">✦ [KEY FINDING 1 — cụ thể từ abstract]</div>
    <div class="find">✦ [KEY FINDING 2 — cụ thể từ abstract]</div>
    <div class="find">✦ [KEY FINDING 3 — cụ thể từ abstract]</div>
    <div class="find">✦ [KEY FINDING 4 — cụ thể từ abstract]</div>
  </div>
  <div class="foot">arxiv.org · {today}</div>
</div>
<div class="mid">
  <div class="dtitle">🔬 [TÊN DIAGRAM PHÙ HỢP VỚI BÀI BÁO]</div>
  <div class="pipeline">
    <div class="node n1"><div class="ni">[🔢]</div><div class="nl">[NODE 1 TÊN]</div><div class="nd">[mô tả 3-5 từ]</div></div>
    <div class="arr">➤</div>
    <div class="node n2"><div class="ni">[🔢]</div><div class="nl">[NODE 2 TÊN]</div><div class="nd">[mô tả 3-5 từ]</div></div>
    <div class="arr">➤</div>
    <div class="node n3"><div class="ni">[🔢]</div><div class="nl">[NODE 3 TÊN]</div><div class="nd">[mô tả 3-5 từ]</div></div>
    <div class="arr">➤</div>
    <div class="node n4"><div class="ni">[🔢]</div><div class="nl">[NODE 4 TÊN]</div><div class="nd">[mô tả 3-5 từ]</div></div>
    <div class="arr">➤</div>
    <div class="node n5"><div class="ni">[🔢]</div><div class="nl">[NODE 5 TÊN]</div><div class="nd">[mô tả 3-5 từ]</div></div>
  </div>
  <div class="dfoot">Source: arxiv.org/{arxiv_id}</div>
</div>
<div class="right">
  <div class="mtitle">Key Metrics</div>
  <div class="mcard"><div class="mnum">[SỐ LIỆU 1]</div><div class="mlbl">[Mô tả]</div></div>
  <div class="mcard"><div class="mnum">[SỐ LIỆU 2]</div><div class="mlbl">[Mô tả]</div></div>
  <div class="tags">
    <div class="tag" style="background:linear-gradient(90deg,#f72585,#b5179e);">#[TAG1]</div>
    <div class="tag" style="background:linear-gradient(90deg,#7209b7,#4361ee);">#[TAG2]</div>
    <div class="tag" style="background:linear-gradient(90deg,#4361ee,#4cc9f0);">#[TAG3]</div>
    <div class="tag" style="background:linear-gradient(90deg,#f7971e,#ffd200);color:#222;">#[TAG4]</div>
  </div>
</div>
</div></body></html>

Hướng dẫn điền:
- [BG1],[BG2],[BG3]: 3 màu hex tối phù hợp chủ đề bài báo (VD robotics: #0d0221,#0a1628,#0f2557)
- [NODE x TÊN]: tên CỤ THỂ từ pipeline/framework của bài báo (không dùng "Input","Process","Output")
- [SỐ LIỆU]: số/thống kê từ abstract. Nếu không có số → dùng từ ngắn như "5 Sources","6 Challenges"
- Trả về HTML hoàn chỉnh duy nhất, không giải thích thêm.
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
