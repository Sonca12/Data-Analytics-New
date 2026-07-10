import os
import datetime
import urllib.request
import feedparser
import requests
import google.generativeai as genai
from dotenv import load_dotenv
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
    print("Đang tìm bài báo khoa học mới nhất trên Arxiv...")
    query = 'all:data+analytics'
    url = f'http://export.arxiv.org/api/query?search_query={query}&start=0&max_results=1&sortBy=submittedDate&sortOrder=descending'
    
    # Sử dụng requests để tránh lỗi SSL trên Windows
    response = requests.get(url)
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
    print("Đang nhờ Gemini AI phân tích và viết bài...")
    genai.configure(api_key=GEMINI_API_KEY)
    model = genai.GenerativeModel('gemini-1.0-pro')
    
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

def post_to_linkedin(content):
    """Đăng bài lên LinkedIn qua API"""
    if not LINKEDIN_ACCESS_TOKEN:
        print("Bỏ qua bước đăng LinkedIn vì thiếu Access Token.")
        return

    print("Đang kết nối với LinkedIn...")
    headers = {
        'Authorization': f'Bearer {LINKEDIN_ACCESS_TOKEN}',
        'X-Restli-Protocol-Version': '2.0.0',
        'Content-Type': 'application/json'
    }
    
    try:
        # Lấy thông tin URN của user
        user_info_resp = requests.get('https://api.linkedin.com/v2/userinfo', headers=headers)
        if user_info_resp.status_code != 200:
            print(f"Lỗi khi lấy thông tin user LinkedIn: {user_info_resp.text}")
            return
            
        author_urn = f"urn:li:person:{user_info_resp.json()['sub']}"
        
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
                    "shareMediaCategory": "NONE"
                }
            },
            "visibility": {
                "com.linkedin.ugc.MemberNetworkVisibility": "PUBLIC"
            }
        }
        
        if not TEST_MODE:
            post_resp = requests.post(post_url, headers=headers, json=post_data)
            if post_resp.status_code == 201:
                print("Đã đăng bài lên LinkedIn thành công!")
            else:
                print(f"Lỗi khi đăng bài: {post_resp.text}")
        else:
            print("[TEST MODE] Giả lập đăng bài thành công lên LinkedIn.")
            
    except Exception as e:
        print(f"Lỗi trong quá trình xử lý LinkedIn: {e}")

def save_post_to_file(content):
    """Lưu bài viết vào thư mục posts/ để đẩy lên GitHub"""
    os.makedirs("posts", exist_ok=True)
    today_str = datetime.datetime.now().strftime("%Y-%m-%d")
    filename = f"posts/{today_str}.md"
    
    with open(filename, "w", encoding="utf-8") as f:
        f.write(content)
    print(f"Đã lưu bài viết vào file: {filename}")

def main():
    try:
        # Bước 1: Lấy thông tin bài báo
        paper_info = fetch_latest_arxiv_paper()
        
        # Bước 2: Nhờ AI viết bài
        post_content = generate_linkedin_post(paper_info)
        print("\n--- NỘI DUNG BÀI VIẾT TẠO BỞI AI ---\n")
        print(post_content)
        print("\n------------------------------------\n")
        
        # Bước 3: Lưu thành file markdown
        save_post_to_file(post_content)
        
        # Bước 4: Đăng lên LinkedIn
        post_to_linkedin(post_content)
        
        print("Hoàn thành quy trình tự động của ngày hôm nay!")
        
    except Exception as e:
        print(f"Có lỗi xảy ra: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
