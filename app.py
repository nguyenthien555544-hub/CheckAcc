import os
from flask import Flask, render_template_string, request
import cloudscraper
import re
import time
from datetime import datetime

app = Flask(__name__)
scraper = cloudscraper.create_scraper(browser={'browser': 'chrome', 'platform': 'android', 'mobile': True})

HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>Bot Check Acc </title>
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <style>
        body { background-color: #0d1117; color: #c9d1d9; font-family: sans-serif; padding: 10px; }
        .card { background: #161b22; padding: 15px; border-radius: 12px; border: 1px solid #30363d; max-width: 500px; margin: auto; }
        h2 { color: #ff0050; text-align: center; margin-bottom: 5px; }
        textarea { width: 94%; height: 100px; padding: 10px; border-radius: 8px; border: 1px solid #30363d; background: #0d1117; color: white; margin-bottom: 10px; font-size: 14px; }
        .btn { width: 100%; padding: 12px; background: #238636; color: white; border: none; border-radius: 8px; font-weight: bold; cursor: pointer; }
        .res-table { width: 100%; margin-top: 20px; border-collapse: collapse; font-size: 12px; }
        .res-table th { background: #21262d; padding: 8px; border: 1px solid #30363d; text-align: left; }
        .res-table td { padding: 8px; border: 1px solid #30363d; }
        .score-box { font-weight: bold; border-radius: 4px; padding: 2px 5px; }
        .good { background: #238636; color: white; }
        .bad { background: #da3633; color: white; }
        .warn { background: #d29922; color: white; }
    </style>
</head>
<body>
    <div class="card">
        <h2>🛡️ BOT CHECK ACC </h2>
        <p style="text-align:center; font-size:12px; color:#8b949e;">Dán danh sách username (mỗi dòng 1 tên)</p>
        
        <form method="POST">
            <textarea name="list_u" placeholder="yeuanh123&#10;account_nuoi_01&#10;..." required></textarea>
            <button type="submit" class="btn">CHECK HÀNG LOẠT</button>
        </form>

        {% if results %}
        <table class="res-table">
            <thead>
                <tr>
                    <th>User</th>
                    <th>FL</th>
                    <th>Vid</th>
                    <th>Tuổi</th>
                    <th>T.Tác</th>
                    <th>Score</th>
                </tr>
            </thead>
            <tbody>
                {% for r in results %}
                <tr>
                    <td>@{{ r.u }}</td>
                    <td>{{ r.f }}</td>
                    <td>{{ r.v }}</td>
                    <td>{{ r.a }}d</td>
                    <td class="{{ 'good' if r.ir > 5 else 'warn' }}">{{ r.ir }}%</td>
                    <td><span class="score-box {{ 'good' if r.s > 70 else ('warn' if r.s > 40 else 'bad') }}">{{ r.s }}%</span></td>
                </tr>
                {% endfor %}
            </tbody>
        </table>
        <p style="font-size:11px; color:#8b949e; margin-top:10px;">*T.Tác: Tỷ lệ Tim/Follower. Score > 70% là acc cực cứng.</p>
        {% endif %}
    </div>
</body>
</html>
"""

@app.route('/', methods=['GET', 'POST'])
def index():
    results = []
    if request.method == 'POST':
        raw_list = request.form.get('list_u', '').split('\n')
        users = [u.strip().replace("@", "") for u in raw_list if u.strip()]
        
        for u in users[:20]: # Giới hạn 20 acc mỗi lần quét để tránh bị TikTok chặn
            try:
                r = scraper.get(f"https://www.tiktok.com/@{u}", timeout=10)
                if r.status_code == 200:
                    html = r.text
                    v_ids = re.findall(r'"id":"(\d{18,20})"', html)
                    fol = int(re.search(r'"followerCount":(\d+)', html).group(1) or 0)
                    vid = int(re.search(r'"videoCount":(\d+)', html).group(1) or 0)
                    lik = int(re.search(r'"heartCount":(\d+)', html).group(1) or 0)
                    
                    # Tính tuổi acc
                    age = 0
                    if v_ids:
                        ts = int(min(v_ids)) >> 32
                        age = (datetime.now() - datetime.fromtimestamp(ts)).days

                    # Tỷ lệ tương tác (Engagement Rate)
                    ir = round((lik / fol * 100), 1) if fol > 0 else 0
                    
                    # Công thức chấm điểm nâng cao
                    score = min(100, vid*3 + age//10 + int(ir*2))
                    
                    results.append({'u': u, 'f': f"{fol:,}", 'v': vid, 'a': age, 'ir': ir, 's': score})
                    time.sleep(1) # Nghỉ 1s giữa mỗi lần quét để bảo vệ IP
                else:
                    results.append({'u': u, 'f': 'ERR', 'v': '0', 'a': '0', 'ir': '0', 's': 0})
            except:
                continue
                
    return render_template_string(HTML_TEMPLATE, results=results)

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
