import os
from flask import Flask, render_template_string, request
import cloudscraper
import re
import time
from datetime import datetime

app = Flask(__name__)
scraper = cloudscraper.create_scraper(browser={'browser': 'chrome', 'platform': 'android', 'mobile': True})

# Lưu lịch sử trong bộ nhớ tạm (Sẽ reset khi restart server)
history_log = []

HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>Bot Check Acc</title>
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <style>
        body { background-color: #0d1117; color: #c9d1d9; font-family: sans-serif; margin: 0; padding: 0; }
        /* Header & Menu */
        .header { background: #161b22; padding: 15px; display: flex; align-items: center; border-bottom: 1px solid #30363d; }
        .menu-btn { font-size: 24px; cursor: pointer; margin-right: 15px; color: #ff0050; }
        .sidebar { height: 100%; width: 0; position: fixed; z-index: 1; top: 0; left: 0; background-color: #161b22; overflow-x: hidden; transition: 0.3s; padding-top: 60px; border-right: 1px solid #30363d; }
        .sidebar a { padding: 15px 25px; text-decoration: none; font-size: 18px; color: #c9d1d9; display: block; border-bottom: 1px solid #21262d; }
        .sidebar a:hover { background: #21262d; }
        .closebtn { position: absolute; top: 10px; right: 20px; font-size: 30px; color: #ff0050; text-decoration: none; }
        
        .container { padding: 20px; max-width: 600px; margin: auto; }
        textarea { width: 93%; height: 120px; padding: 12px; border-radius: 8px; border: 1px solid #30363d; background: #0d1117; color: white; margin-bottom: 15px; font-size: 14px; }
        .btn { width: 100%; padding: 12px; background: #ff0050; color: white; border: none; border-radius: 8px; font-weight: bold; cursor: pointer; font-size: 16px; }
        
        /* Table */
        .res-table { width: 100%; margin-top: 20px; border-collapse: collapse; font-size: 12px; }
        .res-table th { background: #21262d; padding: 10px; border: 1px solid #30363d; text-align: left; }
        .res-table td { padding: 10px; border: 1px solid #30363d; }
        .green { color: #3fb950; font-weight: bold; }
        .red { color: #f85149; }
    </style>
</head>
<body>

<div id="mySidebar" class="sidebar">
  <a href="javascript:void(0)" class="closebtn" onclick="closeNav()">&times;</a>
  <a href="/">CHECK ACC</a>
  <a href="/history">LỊCH SỬ CHECK</a>
</div>

<div class="header">
    <span class="menu-btn" onclick="openNav()">&#9776;</span>
    <b style="font-size: 18px;">BOT CHECK ACC</b>
</div>

<div class="container">
    {% if page == 'history' %}
        <h3 style="color:#ff0050;">LỊCH SỬ GẦN ĐÂY</h3>
        <table class="res-table">
            <thead>
                <tr>
                    <th>User</th>
                    <th>Thời gian</th>
                    <th>Score</th>
                </tr>
            </thead>
            <tbody>
                {% for h in history[::-1] %}
                <tr>
                    <td>@{{ h.u }}</td>
                    <td>{{ h.t }}</td>
                    <td class="green">{{ h.s }}%</td>
                </tr>
                {% endfor %}
            </tbody>
        </table>
    {% else %}
        <form method="POST">
            <textarea name="list" placeholder="Dán danh sách username (mỗi dòng 1 tên)..." required></textarea>
            <button type="submit" class="btn">CHECK</button>
        </form>

        {% if results %}
        <table class="res-table">
            <thead>
                <tr>
                    <th>User</th>
                    <th>Tuổi</th>
                    <th>View</th>
                    <th>Tim</th>
                    <th>Score</th>
                </tr>
            </thead>
            <tbody>
                {% for r in results %}
                <tr>
                    <td>@{{ r.u }}</td>
                    <td>{{ r.a }} ngày</td>
                    <td>{{ r.v }}</td>
                    <td>{{ r.l }}</td>
                    <td class="green">{{ r.s }}%</td>
                </tr>
                {% endfor %}
            </tbody>
        </table>
        {% endif %}
    {% endif %}
</div>

<script>
function openNav() { document.getElementById("mySidebar").style.width = "250px"; }
function closeNav() { document.getElementById("mySidebar").style.width = "0"; }
</script>

</body>
</html>
"""

@app.route('/', methods=['GET', 'POST'])
def index():
    results = []
    if request.method == 'POST':
        list_u = request.form.get('list', '')
        users = [u.strip().replace("@", "") for u in list_u.split('\n') if u.strip()]
        for u in users[:10]:
            try:
                r = scraper.get(f"https://www.tiktok.com/@{u}", timeout=10)
                if r.status_code == 200:
                    html = r.text
                    v_ids = re.findall(r'"id":"(\d{18,20})"', html)
                    v_match = re.search(r'"playCount":(\d+)', html)
                    l_match = re.search(r'"heartCount":(\d+)', html)
                    
                    view = int(v_match.group(1)) if v_match else 0
                    lik = int(l_match.group(1)) if l_match else 0
                    age = 0
                    if v_ids:
                        ts = int(min(v_ids)) >> 32
                        age = (datetime.now() - datetime.fromtimestamp(ts)).days
                    
                    score = min(100, (age // 10) + (lik // 500) + (view // 5000))
                    res_data = {'u': u, 'a': age, 'v': f"{view:,}", 'l': f"{lik:,}", 's': score}
                    results.append(res_data)
                    # Lưu vào lịch sử
                    history_log.append({'u': u, 's': score, 't': datetime.now().strftime('%H:%M:%S')})
                    time.sleep(1)
            except: continue
    return render_template_string(HTML_TEMPLATE, results=results, page='index')

@app.route('/history')
def history():
    return render_template_string(HTML_TEMPLATE, history=history_log, page='history')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))
