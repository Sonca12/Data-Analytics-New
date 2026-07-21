import os
import datetime
import json
import urllib.request
import feedparser
import requests
import google.generativeai as genai
from dotenv import load_dotenv
from PIL import Image, ImageDraw, ImageFont
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

def generate_diagram_steps(paper_info):
    """Dùng Gemini AI để tóm tắt bài báo thành 3 bước ngắn: Input -> Process -> Output"""
    print("Đang nhờ Gemini AI tóm tắt sơ đồ hoạt động...", flush=True)
    genai.configure(api_key=GEMINI_API_KEY)
    model = genai.GenerativeModel(
        'gemini-3.5-flash',
        generation_config={"response_mime_type": "application/json"}
    )

    prompt = f"""Dựa vào tóm tắt bài báo khoa học dưới đây, hãy tóm tắt cách hoạt động của
phương pháp/hệ thống được nói đến thành 3 bước ngắn theo mô hình Input -> Process -> Output.

Tiêu đề: {paper_info['title']}
Tóm tắt (Abstract): {paper_info['abstract']}

Yêu cầu:
- Mỗi bước chỉ 2-5 từ ngắn gọn, bằng tiếng Việt, không dùng dấu ngoặc hay dấu câu thừa.
- Trả về đúng định dạng JSON với 4 khóa: "title", "input", "process", "output".
- "title" là tên ngắn gọn (dưới 6 từ) mô tả chủ đề chính của nghiên cứu.

Ví dụ định dạng:
{{"title": "Dự đoán giá nhà", "input": "Dữ liệu bất động sản", "process": "Mô hình học máy", "output": "Giá dự đoán"}}
"""
    try:
        response = model.generate_content(prompt)
        data = json.loads(response.text)
        return {
            "title": data.get("title", paper_info["title"][:40]),
            "input": data.get("input", "Dữ liệu đầu vào"),
            "process": data.get("process", "Xử lý / Mô hình"),
            "output": data.get("output", "Kết quả đầu ra"),
        }
    except Exception as e:
        print(f"Không thể tóm tắt sơ đồ bằng AI, dùng giá trị mặc định: {e}", flush=True)
        return {
            "title": paper_info["title"][:40],
            "input": "Dữ liệu đầu vào",
            "process": "Xử lý / Mô hình",
            "output": "Kết quả đầu ra",
        }

def _load_font(size, bold=False):
    """Tải font chữ có dấu tiếng Việt, ưu tiên font hệ thống Windows"""
    candidates = [
        "arialbd.ttf" if bold else "arial.ttf",
        "segoeuib.ttf" if bold else "segoeui.ttf",
        "calibrib.ttf" if bold else "calibri.ttf",
    ]
    windows_fonts_dir = r"C:\Windows\Fonts"
    for name in candidates:
        path = os.path.join(windows_fonts_dir, name)
        if os.path.exists(path):
            try:
                return ImageFont.truetype(path, size)
            except Exception:
                continue
    return ImageFont.load_default()

def draw_explainer_diagram(steps):
    """Vẽ sơ đồ Input -> Process -> Output bằng Pillow, dựa trên nội dung do AI tóm tắt"""
    print("Đang vẽ sơ đồ minh họa cách hoạt động...", flush=True)

    width, height = 1200, 675
    bg_color = (255, 255, 255)
    accent_color = (13, 71, 161)      # xanh đậm
    box_fill = (227, 242, 253)        # xanh nhạt
    box_outline = (13, 71, 161)
    text_color = (13, 71, 161)
    arrow_color = (66, 66, 66)

    image = Image.new("RGB", (width, height), bg_color)
    draw = ImageDraw.Draw(image)

    title_font = _load_font(40, bold=True)
    label_font = _load_font(26, bold=True)
    content_font = _load_font(24)

    # Tiêu đề trên cùng
    title_text = steps["title"]
    title_bbox = draw.textbbox((0, 0), title_text, font=title_font)
    title_w = title_bbox[2] - title_bbox[0]
    draw.text(((width - title_w) / 2, 40), title_text, fill=accent_color, font=title_font)

    # 3 hộp: Input / Process / Output
    box_w, box_h = 320, 220
    gap = 70
    total_w = box_w * 3 + gap * 2
    start_x = (width - total_w) / 2
    box_y = 260

    labels = ["INPUT", "PROCESS", "OUTPUT"]
    contents = [steps["input"], steps["process"], steps["output"]]

    box_positions = []
    for i in range(3):
        x0 = start_x + i * (box_w + gap)
        y0 = box_y
        x1 = x0 + box_w
        y1 = y0 + box_h
        box_positions.append((x0, y0, x1, y1))

        draw.rounded_rectangle([x0, y0, x1, y1], radius=20, fill=box_fill, outline=box_outline, width=3)

        # Nhãn (INPUT/PROCESS/OUTPUT)
        label_bbox = draw.textbbox((0, 0), labels[i], font=label_font)
        label_w = label_bbox[2] - label_bbox[0]
        draw.text((x0 + (box_w - label_w) / 2, y0 + 20), labels[i], fill=accent_color, font=label_font)

        # Nội dung do AI tóm tắt, tự động xuống dòng nếu dài
        wrapped = _wrap_text(contents[i], content_font, box_w - 40, draw)
        line_height = 32
        total_text_h = len(wrapped) * line_height
        text_start_y = y0 + (box_h - total_text_h) / 2 + 20
        for j, line in enumerate(wrapped):
            line_bbox = draw.textbbox((0, 0), line, font=content_font)
            line_w = line_bbox[2] - line_bbox[0]
            draw.text((x0 + (box_w - line_w) / 2, text_start_y + j * line_height), line, fill=text_color, font=content_font)

    # Vẽ mũi tên nối giữa các hộp
    for i in range(2):
        x_start = box_positions[i][2]
        x_end = box_positions[i + 1][0]
        y_mid = box_y + box_h / 2
        draw.line([(x_start + 10, y_mid), (x_end - 20, y_mid)], fill=arrow_color, width=4)
        draw.polygon(
            [(x_end - 20, y_mid - 12), (x_end - 20, y_mid + 12), (x_end, y_mid)],
            fill=arrow_color
        )

    return image

def _wrap_text(text, font, max_width, draw):
    """Tự động ngắt dòng để chữ không bị tràn khỏi hộp"""
    words = text.split()
    lines = []
    current_line = ""
    for word in words:
        test_line = f"{current_line} {word}".strip()
        bbox = draw.textbbox((0, 0), test_line, font=font)
        if bbox[2] - bbox[0] <= max_width:
            current_line = test_line
        else:
            if current_line:
                lines.append(current_line)
            current_line = word
    if current_line:
        lines.append(current_line)
    return lines if lines else [text]

def save_image_to_file(image):
    """Lưu ảnh sơ đồ minh họa vào thư mục posts/ cùng ngày với bài viết"""
    os.makedirs("posts", exist_ok=True)
    today_str = datetime.datetime.now().strftime("%Y-%m-%d")
    filename = f"posts/{today_str}.png"

    image.save(filename)
    print(f"Đã lưu ảnh minh họa vào file: {filename}", flush=True)
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

        # Bước 3b: Tóm tắt sơ đồ Input -> Process -> Output và tự vẽ bằng Pillow
        image_path = None
        try:
            diagram_steps = generate_diagram_steps(paper_info)
            diagram_image = draw_explainer_diagram(diagram_steps)
            image_path = save_image_to_file(diagram_image)
        except Exception as e:
            print(f"Bỏ qua bước tạo sơ đồ minh họa do lỗi: {e}", flush=True)

        # Bước 4: Đăng lên LinkedIn (kèm sơ đồ minh họa nếu có)
        post_to_linkedin(post_content, image_path=image_path)
        
        print("Hoàn thành quy trình tự động của ngày hôm nay!", flush=True)
        
    except Exception as e:
        print(f"Có lỗi xảy ra: {e}", flush=True)
        sys.exit(1)

if __name__ == "__main__":
    main()
