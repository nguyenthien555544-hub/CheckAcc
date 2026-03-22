from flask import Flask, render_template_string, request, send_file
import cloudscraper
import re
import os
import time
from datetime import datetime

app = Flask(__name__)
scraper = cloudscraper.create_scraper(browser={'browser': 'chrome', 'platform': 'android', 'mobile': True})
HISTORY_FILE = "nhat_ky_nuoi_acc.txt"

# Giao diện Dark Mode chuẩn Pro
HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>TikTok V23 Ultimate</title>
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <style>
        body { background-color: #0d1117; color: #c9d1d9; font-family: -apple-system,BlinkMacSystemFont,"Segoe UI",Helvetica,Arial,sans-serif; padding: 10px; }
        .card { background: #161b22; padding: 20px; border-radius: 12px; border: 1px solid #30363d; max-width: 450px; margin: auto; box-shadow: 0 8px 24px rgba(0,0,0,0.5); }
        h2 { color: #ff0050; text-align: center; margin-bottom: 20px; }
        input { width: 88%; padding: 12px; border-radius: 6px; border: 1px solid #30363d; background: #0d1117; color: white; margin-bottom: 10px; font-size: 16px; }
        .btn-check { width: 95%; padding: 12px; background: #ff0050; color: white; border: none; border-radius: 6px; font-weight: bold; cursor: pointer; font-size: 16px; }
        .btn-down { width: 95%; padding: 10px; background: #21262d; color: #58a6ff; border: 1px solid #30363d; border-radius: 6px; margin-top: 10px; cursor: pointer; }
        .result-box { margin-top: 20px; background: #0d1117; padding: 15px; border-radius: 8px; border-left: 4px solid #ff0050; text-align: left; }
        .row { display: flex; justify-content: space-between; margin-bottom: 10px; font-size: 14px; border-bottom: 1px solid #21262d; padding-bottom: 4px; }
        .val { color: #58a6ff; font-weight: bold; }
        .green { color: #3fb950; } .orange { color: #d29922; }
    </style>
</head>
<body>
    <div class="card">
        <h2>🛡️ TIKTOK CHECK ACC</h2>
        <form method="POST">
            <input type="text" name="user" placeholder="Nhập Username (vd: yeuanhdl)" required>
            <button type="submit" class="btn-check">CHECK ACC & LƯU LS</button>
        </form>
        
        <a href="/download"><button class="btn-down">📂 TẢI LỊCH SỬ (.TXT)</button></a>

        {% if d %}
        <div class="result-box">
            <h3 style="margin-top:0; color:#ff0050;">👤 @{{ d.user }}</h3>
            <div class="row"><span>👥 Follower:</span> <span class="val green">{{ d.fol }}</span></div>
            <div class="row"><span>🎬 Tổng Video:</span> <span class="val">{{ d.vid }}</span></div>
            <div class="row"><span>📅 Đăng lần đầu:</span> <span class="val orange">{{ d.f_date }}</span></div>
            <div class="row"><span>🕰️ Tuổi acc:</span> <span class="val">{{ d.age }} ngày</span></div>
            <hr style="border:0.5px solid #30363d;">
            <div style="text-align:center;">
                <span style="font-size:16px;">🏆 Độ hoàn thiện: </span>
                <b style="font-size:24px;" class="green">{{ d.score }}%</b>
            </div>
            <p style="font-size:12px; color:#8b949e; text-align:center; margin-top:10px;">{{ d.adv }}</p>
        </div>
        {% elif err %}
        <p style="color:#f85149; margin-top:15px; font-weight:bold;">{{ err }}</p>
        {% endif %}
    </div>
</body>
</html>
"""

@app.route('/', methods=['GET', 'POST'])
def index():
    data, err = None, None
    if request.method == 'POST':
        user = request.form.get('user').strip().replace("@", "")
        try:
            time.sleep(1.5) # Né TikTok quét
            res = scraper.get(f"https://www.tiktok.com/@{user}", timeout=15)
            if res.status_code == 200:
                html = res.text
                # Lấy ID video nhỏ nhất để tính ngày tạo
                v_ids = re.findall(r'"id":"(\d{18,20})"', html)
                fol = re.search(r'"followerCount":(\d+)', html).group(1) or 0
                vid = re.search(r'"videoCount":(\d+)', html).group(1) or 0
                
                f_date, age_days = "N/A", 0
                if v_ids:
                    ts = int(min(v_ids)) >> 32
                    dt = datetime.fromtimestamp(ts)
                    f_date = dt.strftime('%d/%m/%Y')
                    age_days = (datetime.now() - dt).days

                # Chấm điểm độ "cứng"
                score = min(100, int(vid)*4 + age_days//12 + int(fol)//200)
                adv = "🔥 Sẵn sàng rải link!" if score > 70 else "🌱 Cần nuôi thêm video/tương tác."
                
                data = {'user': user, 'fol': f"{int(fol):,}", 'vid': vid, 'f_date': f_date, 'age': age_days, 'score': score, 'adv': adv}
                
                # Lưu lịch sử check
                with open(HISTORY_FILE, "a", encoding="utf-8") as f:
                    f.write(f"[{datetime.now().strftime('%d/%m %H:%M')}] @{user} - FL: {fol}, Video: {vid}, Age: {age_days}d, Score: {score}%\n")
            else:
                err = "❌ Không tìm thấy Username hoặc bị TikTok chặn IP."
        except Exception as e:
            err = f"❗ Lỗi kết nối: {str(e)}"
    return render_template_string(HTML_TEMPLATE, d=data, err=err)

@app.route('/download')
def download():
    if os.path.exists(HISTORY_FILE):
        return send_file(HISTORY_FILE, as_attachment=True)
    return "Chưa có dữ liệu lịch sử để tải!"

if __name__ == '__main__':
    # Chạy Web Server tại localhost:5000
    app.run(host='0.0.0.0', port=5000)
