import os
from flask import Flask, render_template_string, request
import cloudscraper
import re
import time
from datetime import datetime

app = Flask(__name__)
scraper = cloudscraper.create_scraper(browser={'browser': 'chrome', 'platform': 'android', 'mobile': True})

# --- CẤU HÌNH KEY ---
ACCESS_KEY = "admin123"

HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>Bot Check Acc</title>
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <style>
        body { background-color: #0d1117; color: #c9d1d9; font-family: sans-serif; padding: 10px; }
        .card { background: #161b22; padding: 15px; border-radius: 12px; border: 1px solid #30363d; max-width: 500px; margin: auto; }
        h2 { color: #ff0050; text-align: center; }
        input, textarea { width: 93%; padding: 10px; border-radius: 8px; border: 1px solid #30363d; background: #0d1117; color: white; margin-bottom: 12px; }
        .btn { width: 100%; padding: 12px; background: #ff0050; color: white; border: none; border-radius: 8px; font-weight: bold; cursor: pointer; }
        .res-table { width: 100%; margin-top: 20px; border-collapse: collapse; font-size: 11px; }
        .res-table th { background: #21262d; padding: 8px; border: 1px solid #30363d; text-align: left; }
        .res-table td { padding: 8px; border: 1px solid #30363d; }
        .sc { font-weight: bold; color: #3fb950; }
        .low { color: #da3633; }
    </style>
</head>
<body>
    <div class="card">
        <h2>🛡️ BOT CHECK ACC</h2>
        
        {% if not auth %}
        <form method="POST">
            <input type="password" name="k" placeholder="Nhập Key..." required>
            <button type="submit" class="btn">XÁC THỰC</button>
        </form>
        {% else %}
        <form method="POST">
            <input type="hidden" name="k" value="{{ k }}">
            <textarea name="list" placeholder="Dán list username..." required></textarea>
            <button type="submit" class="btn">CHECK</button>
        </form>

        {% if results %}
        <table class="res-table">
            <thead>
                <tr>
                    <th>User</th>
                    <th>Tuổi (Ngày)</th>
                    <th>View</th>
                    <th>Tim</th>
                    <th>Score</th>
                </tr>
            </thead>
            <tbody>
                {% for r in results %}
                <tr>
                    <td>@{{ r.u }}</td>
                    <td>{{ r.a }}</td>
                    <td>{{ r.v }}</td>
                    <td>{{ r.l }}</td>
                    <td class="sc {{ 'low' if r.s < 50 }}">{{ r.s }}%</td>
                </tr>
                {% endfor %}
            </tbody>
        </table>
        {% endif %}
        {% endif %}
    </div>
</body>
</html>
"""

@app.route('/', methods=['GET', 'POST'])
def index():
    results, auth, k = [], False, request.form.get('k', '')
    if k == ACCESS_KEY:
        auth = True
        list_u = request.form.get('list', '')
        if list_u:
            users = [u.strip().replace("@", "") for u in list_u.split('\n') if u.strip()]
            for u in users[:10]: # Quét 10 acc để tránh lỗi 502
                try:
                    r = scraper.get(f"https://www.tiktok.com/@{u}", timeout=10)
                    if r.status_code == 200:
                        html = r.text
                        v_ids = re.findall(r'"id":"(\d{18,20})"', html)
                        view = int(re.search(r'"playCount":(\d+)', html).group(1) or 0)
                        lik = int(re.search(r'"heartCount":(\d+)', html).group(1) or 0)
                        age = 0
                        if v_ids:
                            ts = int(min(v_ids)) >> 32
                            age = (datetime.now() - datetime.fromtimestamp(ts)).days
                        
                        # Chấm điểm dựa trên 3 trụ cột
                        score = min(100, (age // 10) + (lik // 500) + (view // 5000))
                        results.append({'u': u, 'a': age, 'v': f"{view:,}", 'l': f"{lik:,}", 's': score})
                        time.sleep(1)
                except: continue
    return render_template_string(HTML_TEMPLATE, auth=auth, results=results, k=k)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))
