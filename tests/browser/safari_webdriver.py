"""Real Safari checks via Apple's WebDriver, intended for ephemeral macOS CI only."""
import base64
import hashlib
import json
import os
from pathlib import Path
import platform
import subprocess
import tempfile
import time
import traceback
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


def request(method, path, body=None):
    data=None if body is None else json.dumps(body).encode()
    try:
        with urlopen(Request('http://127.0.0.1:4444'+path,data=data,method=method,
                             headers={'Content-Type':'application/json'}),timeout=30) as response:
            value=json.load(response).get('value')
    except HTTPError as error:
        raise RuntimeError(error.read().decode()) from error
    if isinstance(value,dict) and value.get('error'):
        raise RuntimeError(str(value))
    return value


def main():
    output=Path(os.environ['PLAINTRACE_BROWSER_RESULTS']).resolve()
    checkout=Path(__file__).resolve().parents[2]
    if output.is_relative_to(checkout):
        raise ValueError('Browser results must stay outside checkout')
    output.mkdir(parents=True,exist_ok=True)
    with tempfile.TemporaryDirectory(prefix='plaintrace-safari-') as folder:
        server=subprocess.Popen(['python','-I','-m','plaintrace.ui','--port','8771'],cwd=folder,
                                stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
        driver=subprocess.Popen(['/usr/bin/safaridriver','-p','4444'],cwd=folder,
                                stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
        session=None
        record={'os':platform.platform(),'machine':platform.machine(),'python':platform.python_version(),
                'sha':os.environ.get('GITHUB_SHA'),'run':os.environ.get('GITHUB_RUN_ID'),
                'attempt':os.environ.get('GITHUB_RUN_ATTEMPT'),'image':os.environ.get('ImageVersion'),
                'checks':[],'status':'failed'}
        try:
            for _ in range(60):
                try:
                    with urlopen('http://127.0.0.1:8771/',timeout=1) as response:
                        assert response.status==200
                    request('GET','/status')
                    break
                except (OSError,URLError):
                    time.sleep(.5)
            created=request('POST','/session',{'capabilities':{'alwaysMatch':{'browserName':'safari'}}})
            session=created['sessionId'];record['capabilities']=created['capabilities']
            assert record['capabilities']['browserName'].lower()=='safari'
            prefix='/session/'+session
            def execute(script,*args):
                return request('POST',prefix+'/execute/sync',{'script':script,'args':list(args)})
            def find(css):
                return request('POST',prefix+'/element',{'using':'css selector','value':css})['element-6066-11e4-a52e-4f735466cecf']
            def click(css):
                request('POST',prefix+'/element/'+find(css)+'/click',{})
            def wait(script):
                for _ in range(50):
                    if execute('return '+script):return
                    time.sleep(.1)
                raise AssertionError(script)
            def check(name,script):
                wait(script);record['checks'].append(name)
            def capture(name):
                (output/name).write_bytes(base64.b64decode(request('GET',prefix+'/screenshot')))
            request('POST',prefix+'/url',{'url':'http://127.0.0.1:8771/'})
            check('S-01 empty workspace',"!document.querySelector('#empty-workspace').hidden && document.querySelector('#save-report').disabled")
            click('#help-button');check('S-02 native help modal',"document.querySelector('#help-dialog').open")
            click('[data-close="help-dialog"]');wait("!document.querySelector('#help-dialog').open")
            click('#demo-button')
            check('S-03 demo source and record rendering',"document.querySelectorAll('.source-item').length===3 && document.querySelectorAll('#record-list tr').length===3")
            click('[data-filter="windows"]')
            check('S-04 source format filtering',"document.querySelectorAll('.source-item').length===2")
            click('[data-view="timeline"]')
            check('S-05 explicit-field timeline',"document.querySelectorAll('#timeline-list > li').length===5")
            click('[data-view="evidence"]');click('[data-filter="all"]');click('#source-list .source-item');click('#record-list .row-open')
            check('S-06 raw values and source references',"document.querySelector('#record-dialog').open && document.querySelector('#raw-content').textContent.includes('visits:41')")
            click('[data-close="record-dialog"]')
            wait("document.activeElement===document.querySelector('#record-list .row-open')")
            for theme in ['light','dark']:
                execute("const s=document.querySelector('#theme');s.value=arguments[0];s.dispatchEvent(new Event('change',{bubbles:true}));",theme)
                wait("document.documentElement.dataset.theme==='"+theme+"'")
                time.sleep(.25);capture(theme+'.png')
            check('S-07 theme switching',"document.documentElement.dataset.theme==='dark'")
            click('#clear-button')
            check('S-08 clear removes report DOM and raw cache',"!document.querySelector('#empty-workspace').hidden && !document.querySelector('#source-list').childElementCount && !document.querySelector('#raw-content').textContent && document.querySelector('#save-report').disabled")
            request('POST',prefix+'/url',{'url':'http://127.0.0.1:8771/'})
            check('S-09 no automatic report persistence',"!document.querySelector('#empty-workspace').hidden && localStorage.length===0 && sessionStorage.length===0 && document.cookie===''")
            record['user_agent']=execute('return navigator.userAgent')
            record['status']='passed'
        except Exception:
            record['error']=traceback.format_exc()
            if session:
                try:(output/'failure.png').write_bytes(base64.b64decode(request('GET','/session/'+session+'/screenshot')))
                except Exception:pass
        finally:
            if session:
                try:request('DELETE','/session/'+session)
                except Exception:pass
            for process in [driver,server]:
                process.terminate()
                try:process.wait(timeout=10)
                except subprocess.TimeoutExpired:process.kill();process.wait()
            record['screenshots']={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in output.glob('*.png')}
            (output/'safari-result.json').write_text(json.dumps(record,indent=2),encoding='utf-8')
            print(json.dumps(record,indent=2))
    return 0 if record['status']=='passed' else 1


if __name__=='__main__':
    raise SystemExit(main())
