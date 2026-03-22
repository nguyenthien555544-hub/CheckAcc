import os
from flask import Flask, render_template_string, request
import cloudscraper
import re
from datetime import datetime

app = Flask(__name__)
scraper = cloudscraper.create_scraper(browser={'browser': 'chrome', 'platform': 'android', 'mobile': True})

# Bộ nhớ tạm lưu bảng xếp hạng (Sẽ reset khi server Render khởi động lại)
leaderboard = []

HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>Bot CHECK ACC TIKTOK</title>
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <style>
        body { background-color: #0d1117; color: #c9d1d9; font-family: sans-serif; padding: 15px; }
        .card { background: #161b22; padding: 20px; border-radius: 12px; border: 1px solid #30363d; max-width: 450px; margin: auto; }
        h2 { color: #ff0050; text-align: center; margin-bottom: 5px; }
        .tagline { text-align: center; font-size: 12px; color: #8b949e; margin-bottom: 20px; }
        input { width: 90%; padding: 12px; border-radius: 6px; border: 1px solid #30363d; background: #0d1117; color: white; margin-bottom: 15px; }
        .btn { width: 100%; padding: 12px; background: #ff0050; color: white; border: none; border-radius: 6px; font-weight: bold; cursor: pointer; }
        .result { margin-top: 20px; background: #0d1117; padding: 15px; border-radius: 8px; border-left: 4px solid #ff0050; }
        .leaderboard { margin-top: 25px; background: #21262d; padding: 15px; border-radius: 8px; border: 1px solid #30363d; }
        .rank-item { display: flex; justify-content: space-between; padding: 8px 0; border-bottom: 1px solid #30363d; font-size: 14px; }
        .green { color: #3fb950; font-weight: bold; }
        .orange { color: #d29922; }
    </style>
</head>
<body>
    <div class="card">
        <h2>🛡️ BOT CHECK ACC</h2>
        <p class="tagline">Hệ thống phân tích & xếp hạng acc nuôi Pro</p>
        
        <form method="POST">
            <input type="text" name="u" placeholder="Nhập Username TikTok..." required>
            <button type="submit" class="btn">🚀 PHÂN TÍCH NGAY</button>
        </form>

        {% if d %}
        <div class="result">
            <h3 style="margin:0 0 10px 0; color:#ff0050;">👤 @{{ d.u }}</h3>
            <p>👥 Follower: <b class="green">{{ d.f }}</b></p>
            <p>🎬 Video: <b>{{ d.v }}</b></p>
            <p>🕰️ Tuổi acc: <b>{{ d.a }} ngày</b></p>
            <p style="text-align:center; font-size:18px;">🏆 Độ cứng: <b class="green">{{ d.s }}%</b></p>
        </div>
        {% endif %}

        <div class="leaderboard">
            <h3 style="margin-top:0; font-size:16px; color:#58a6ff;">🏆 TOP ACC SIÊU CỨNG</h3>
            {% if ranks %}
                {% for item in ranks %}
                <div class="rank-item">
                    <span>{{ loop.index }}. @{{ item.u }}</span>
                    <span class="green">{{ item.s }}%</span>
                </div>
                {% endfor %}
            {% else %}
                <p style="font-size:12px; color:#8b949e;">Chưa có dữ liệu xếp hạng.</p>
            {% endif %}
        </div>
    </div>
</body>
</html>
"""

@app.route('/', methods=['GET', 'POST'])
def index():
    global leaderboard
    d, err = None, None
    if request.method == 'POST':
        u = request.form.get('u', '').strip().replace("@", "")
        try:
            r = scraper.get(f"https://www.tiktok.com/@{u}", timeout=15)
            if r.status_code == 200:
                html = r.text
                v_ids = re.findall(r'"id":"(\d{18,20})"', html)
                fol = int(re.search(r'"followerCount":(\d+)', html).group(1) or 0)
                vid = int(re.search(r'"videoCount":(\d+)', html).group(1) or 0)
                
                age = 0
                if v_ids:
                    ts = int(min(v_ids)) >> 32
                    age = (datetime.now() - datetime.fromtimestamp(ts)).days

                # Công thức tính độ cứng
                score = min(100, vid*4 + age//12 + fol//500)
                d = {'u': u, 'f': f"{fol:,}", 'v': vid, 'a': age, 's': score}
                
                # Cập nhật bảng xếp hạng (Lấy top 5)
                leaderboard.append({'u': u, 's': score})
                leaderboard = sorted(leaderboard, key=lambda x: x['s'], reverse=True)[:5]
                
        except: pass
    return render_template_string(HTML_TEMPLATE, d=d, ranks=leaderboard)

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
