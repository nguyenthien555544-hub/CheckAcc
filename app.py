import os
from flask import Flask, render_template_string, request, redirect, url_for
import cloudscraper
import re
import time
from datetime import datetime

app = Flask(__name__)
scraper = cloudscraper.create_scraper(browser={'browser': 'chrome', 'platform': 'android', 'mobile': True})

# --- CẤU HÌNH KEY TRUY CẬP ---
ACCESS_KEY = "KEYTHIENGAY" # Bro có thể đổi key này tùy ý

HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>Bot Check Acc TikTok</title>
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <style>
        body { background-color: #0d1117; color: #c9d1d9; font-family: sans-serif; padding: 10px; }
        .card { background: #161b22; padding: 15px; border-radius: 12px; border: 1px solid #30363d; max-width: 550px; margin: auto; }
        h2 { color: #ff0050; text-align: center; margin-bottom: 15px; }
        input, textarea { width: 94%; padding: 10px; border-radius: 8px; border: 1px solid #30363d; background: #0d1117; color: white; margin-bottom: 12px; }
        .btn { width: 100%; padding: 12px; background: #ff0050; color: white; border: none; border-radius: 8px; font-weight: bold; cursor: pointer; }
        .res-table { width: 100%; margin-top: 20px; border-collapse: collapse; font-size: 11px; }
        .res-table th { background: #21262d; padding: 8px; border: 1px solid #30363d; text-align: left; }
        .res-table td { padding: 8px; border: 1px solid #30363d; }
        .score { font-weight: bold; color: #3fb950; }
        .low { color: #da3633; }
    </style>
</head>
<body>
    <div class="card">
        <h2> BOT CHECK ACC </h2>
        
        {% if not authorized %}
        <form method="POST">
            <input type="password" name="key" placeholder="Nhập Access Key để sử dụng..." required>
            <button type="submit" class="btn">XÁC THỰC</button>
            {% if msg %}<p style="color:red; font-size:12px; text-align:center;">{{ msg }}</p>{% endif %}
        </form>
        {% else %}
        <form method="POST">
            <input type="hidden" name="key" value="{{ key }}">
            <textarea name="list_u" placeholder="Dán list username (mỗi dòng 1 tên)..." required></textarea>
            <button type="submit" class="btn">Check </button>
        </form>

        {% if results %}
        <table class="res-table">
            <thead>
                <tr>
                    <th>User</th>
                    <th>Tuổi (Ngày)</th>
                    <th>Tổng View</th>
                    <th>Tương Tác</th>
                    <th>Score</th>
                </tr>
            </thead>
            <tbody>
                {% for r in results %}
                <tr>
                    <td>@{{ r.u }}</td>
                    <td>{{ r.a }}</td>
                    <td>{{ r.v_total }}</td>
                    <td>{{ r.lik }}</td>
                    <td class="score {{ 'low' if r.s < 50 }}">{{ r.s }}%</td>
                </tr>
                {% endfor %}
            </tbody>
        </table>
        {% endif %}
        <p style="text-align:center; margin-top:15px;"><a href="/" style="color:#58a6ff; font-size:12px; text-decoration:none;">Đăng xuất / Làm mới</a></p>
        {% endif %}
    </div>
</body>
</html>
"""

@app.route('/', methods=['GET', 'POST'])
def index():
    results = []
    authorized = False
    msg = None
    key = request.form.get('key', '')

    if key == ACCESS_KEY:
        authorized = True
        list_u = request.form.get('list_u', '')
        if list_u:
            users = [u.strip().replace("@", "") for u in list_u.split('\n') if u.strip()]
            for u in users[:15]: # Quét tối đa 15 acc/lần để tránh bị chặn
                try:
                    r = scraper.get(f"https://www.tiktok.com/@{u}", timeout=10)
                    if r.status_code == 200:
                        html = r.text
                        v_ids = re.findall(r'"id":"(\d{18,20})"', html)
                        # Lấy view từ metadata video đầu tiên (nếu có)
                        view_match = re.search(r'"playCount":(\d+)', html)
                        lik_match = re.search(r'"heartCount":(\d+)', html)
                        
                        view = int(view_match.group(1)) if view_match else 0
                        lik = int(lik_match.group(1)) if lik_match else 0
                        
                        age = 0
                        if v_ids:
                            ts = int(min(v_ids)) >> 32
                            age = (datetime.now() - datetime.fromtimestamp(ts)).days

                        # CÔNG THỨC CHẤM ĐIỂM MỚI
                        # Tuổi (max 40đ) + Tương tác (max 30đ) + View (max 30đ)
                        s_age = min(40, age // 10)
                        s_lik = min(30, lik // 500)
                        s_view = min(30, view // 5000)
                        score = s_age + s_lik + s_view
                        
                        results.append({'u': u, 'a': age, 'v_total': f"{view:,}", 'lik': f"{lik:,}", 's': score})
                        time.sleep(1.2)
                except: continue
    elif key != '':
        msg = "Sai mã truy cập rồi bro ơi!"

    return render_template_string(HTML_TEMPLATE, authorized=authorized, results=results, msg=msg, key=key)

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
