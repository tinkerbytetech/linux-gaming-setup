#!/usr/bin/env python3
"""Original TinkerByteTech graphical gaming setup. Python standard library only."""
from __future__ import annotations
import argparse
import hashlib
import json
import os
from pathlib import Path
import platform
import secrets
import shlex
import shutil
import subprocess
import threading
import time
import webbrowser
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

TARGET = 'fedora'
VERSION = '0.1.0'
DISTROS = {'debian': 'Debian', 'ubuntu': 'Ubuntu', 'kubuntu': 'Kubuntu', 'fedora': 'Fedora'}
APPS = {
    'steam': ('Steam', 'com.valvesoftware.Steam', 'Your Steam library and Proton games'),
    'lutris': ('Lutris', 'net.lutris.Lutris', 'Manage games and Windows launchers'),
    'faugus': ('Faugus Launcher', 'io.github.Faugus.faugus-launcher', 'A lightweight launcher for Windows games'),
    'protonup': ('ProtonUp-Qt', 'net.davidotek.pupgui2', 'Manage compatibility-tool versions'),
}
NATIVE = {'wine': 'Wine', 'gamemode': 'GameMode', 'mangohud': 'MangoHud'}
FLATHUB = 'https://dl.flathub.org/repo/flathub.flatpakrepo'


def read_os_release(path=Path('/etc/os-release')):
    values = {}
    for line in path.read_text().splitlines():
        if '=' in line and not line.startswith('#'):
            key, value = line.split('=', 1)
            try:
                words = shlex.split(value)
                values[key] = words[0] if words else ''
            except ValueError:
                continue
    return values


def compatible(target, info, arch, atomic=False):
    expected = 'ubuntu' if target == 'kubuntu' else target
    if info.get('ID') != expected:
        return f"This download is for {DISTROS[target]}; detected {info.get('PRETTY_NAME', 'another distribution')}."
    if arch not in ('x86_64', 'amd64'):
        return 'This first version requires an x86-64 PC.'
    if atomic:
        return 'Use a Fedora Workstation or KDE installation for this download; Atomic editions use a different system-package workflow.'
    return ''


def validate_choices(values):
    if not isinstance(values, list) or not values or len(values) > 7:
        raise ValueError('Choose at least one tool.')
    if any(not isinstance(v, str) or v not in APPS and v not in NATIVE for v in values):
        raise ValueError('Unknown tool selection.')
    return list(dict.fromkeys(values))


def build_plan(target, values):
    choices = validate_choices(values)
    apps = [v for v in choices if v in APPS]
    native = [v for v in choices if v in NATIVE]
    packages = (['flatpak'] if apps else []) + [v for v in native if v != 'wine']
    if 'wine' in native:
        packages += ['wine'] if target == 'fedora' else ['wine', 'wine64', 'wine32:i386']
    steps = []
    def step(title, argv, admin=False, app=None):
        steps.append({'title': title, 'argv': argv, 'admin': admin, 'app': app})
    if target == 'fedora':
        step('Install selected system packages', ['dnf', '-y', 'install'] + packages, True)
    else:
        if 'wine' in native:
            step('Enable 32-bit package support for Wine', ['dpkg', '--add-architecture', 'i386'], True)
        step('Refresh package lists', ['apt-get', 'update'], True)
        step('Install selected system packages', ['apt-get', '-y', 'install'] + packages, True)
    if apps:
        step('Add Flathub for your user account', ['flatpak', '--user', 'remote-add', '--if-not-exists', 'flathub', FLATHUB])
        for key in apps:
            name, app_id, _ = APPS[key]
            step(f'Install {name}', ['flatpak', '--user', 'install', '--noninteractive', '-y', 'flathub', app_id], app=app_id)
    return steps


def plan_id(choices, steps):
    return hashlib.sha256(json.dumps([choices, steps], sort_keys=True).encode()).hexdigest()


PAGE = r'''<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>TinkerByteTech Gaming Setup</title>
<style nonce="__NONCE__">
:root{color-scheme:dark;font-family:system-ui,sans-serif;color:#e9f4ed;background:#06100b}*{box-sizing:border-box}body{margin:0}main{max-width:1050px;margin:35px auto;padding:0 24px}.brand{color:#59ed80;font-size:22px;font-weight:750;letter-spacing:-.6px}.brand small{font-size:12px;font-weight:400;color:#94b29f;margin-left:12px}h1{font-size:38px;letter-spacing:-1px;margin:28px 0 10px}p{color:#abc2b3;line-height:1.65}.badge{display:inline-block;border:1px solid #355a43;padding:5px 12px;border-radius:20px;font-size:12px;color:#a2edb5}.layout{display:grid;grid-template-columns:1.1fr 1fr;gap:22px;margin-top:25px}.panel{background:#0c1b12;border:1px solid #294d36;border-radius:16px;padding:22px}h2{font-size:18px;margin:0 0 17px}.option{display:flex;gap:12px;align-items:center;padding:14px 0;border-bottom:1px solid #223a2a;cursor:pointer}.option:last-child{border:0}.option input{accent-color:#4cde73;width:18px;height:18px;flex-shrink:0}.option b{font-size:14px}.option small{display:block;color:#8eaa98;font-size:12px;margin-top:4px}.option:has(input:checked) b{color:#91f3ad}button{font:600 13px system-ui;cursor:pointer;padding:12px 18px;border-radius:9px;background:#183c26;border:1px solid #497c58;color:#daf7e3}button:hover{border-color:#74dc8c}button:disabled{opacity:.45;cursor:default}.primary{background:#49de70;color:#05210e;border-color:#65ee8a}.actions{display:flex;gap:10px;flex-wrap:wrap;margin:20px 0 0}pre{background:#06110a;border:1px solid #233e2c;border-radius:9px;padding:14px;font:12px/1.65 monospace;white-space:pre-wrap;overflow-wrap:anywhere;color:#b7dbc4;max-height:310px;overflow:auto}.status{padding:11px 13px;background:#07150b;border-radius:8px;color:#9adcae;font-size:13px;line-height:1.5;margin-bottom:16px}.status.error{color:#ffc1ac;border:1px solid #924e3b}.check{display:flex;gap:8px;align-items:center;margin-top:17px;font-size:13px;color:#abc2b3}.check input{accent-color:#4cde73}.hint{font-size:12px}progress{width:100%;height:8px;accent-color:#49de70;margin-top:14px}#plan{max-height:270px;overflow:auto}a{color:#91f3ad}:focus-visible{outline:2px solid #87ff9f;outline-offset:4px}@media(max-width:740px){main{padding:0 16px}.layout{grid-template-columns:1fr}h1{font-size:29px}.brand small{display:block;margin-left:0;margin-top:5px}}
</style><main><div class="brand">TinkerByteTech <small>Gaming Setup</small></div><h1 id="title">Set up your gaming tools</h1><span class="badge" id="distro">Detecting system…</span><p>Pick the tools you want. Review the setup, then install them together.</p><div class="layout"><section class="panel"><h2>Choose your tools</h2><div id="choices"></div><label class="check"><input id="dry" type="checkbox" checked>Preview only — show steps without installing</label><div class="actions"><button id="review">Review setup</button><button id="start" class="primary" disabled>Start setup</button></div><p class="hint">App downloads use Flathub. System packages use your distribution’s repositories. Your desktop may ask for administrator authentication.</p></section><section class="panel"><h2>Your setup</h2><div class="status" id="status" role="status">Ready to choose your tools.</div><div id="plan"></div><progress id="progress" max="100" value="0"></progress><pre id="output" aria-label="Setup progress">Progress will appear here.</pre><div class="actions"><button id="save" disabled>Save log</button><button id="close">Close installer</button></div></section></div></main>
<script nonce="__NONCE__">
const token=location.hash.slice(1)||sessionStorage.getItem('tbt-setup-token')||'';sessionStorage.setItem('tbt-setup-token',token);history.replaceState(null,'',location.pathname);let reviewed=null,busy=false,log='',demo=false;const $=id=>document.getElementById(id);
async function api(path,body){const r=await fetch('/api/'+path,{method:body?'POST':'GET',headers:{'X-Setup-Token':token,'Content-Type':'application/json'},body:body?JSON.stringify(body):undefined});const d=await r.json();if(!r.ok)throw Error(d.error||'Request failed');return d;}
function values(){return [...document.querySelectorAll('#choices input:checked')].map(n=>n.value)}
function reset(){reviewed=null;$('start').disabled=true;$('plan').replaceChildren()}
function message(text,error=false){$('status').textContent=text;$('status').classList.toggle('error',error)}
function controls(value){busy=value;document.querySelectorAll('#choices input,#review').forEach(n=>n.disabled=value);$('dry').disabled=value||demo;$('start').disabled=value||!reviewed;$('close').disabled=value}
$('review').onclick=async()=>{try{const d=await api('plan',{choices:values()});reviewed=d;$('plan').replaceChildren();d.steps.forEach(s=>{const p=document.createElement('p');p.className='hint';p.textContent=s.title;const code=document.createElement('pre');code.textContent=(s.admin?'Administrator: ':'')+s.argv.join(' ');$('plan').append(p,code)});$('start').disabled=false;$('start').textContent=$('dry').checked?'Run preview':'Install selected tools';message(d.blocked||'Setup reviewed. Ready to continue.',!!d.blocked);if(d.blocked&&!$('dry').checked)$('start').disabled=true;}catch(e){reset();message(e.message,true)}};
$('dry').onchange=reset;
$('start').onclick=async()=>{try{controls(true);await api('start',{choices:values(),plan:reviewed.id,dry_run:$('dry').checked});message($('dry').checked?'Running preview…':'Installing selected tools…');poll()}catch(e){controls(false);message(e.message,true)}};
async function poll(){try{const d=await api('state');log=d.log.join('\n');$('output').textContent=log||'Starting…';$('output').scrollTop=$('output').scrollHeight;$('progress').value=d.progress;$('save').disabled=!log;if(d.running){setTimeout(poll,700)}else{controls(false);message(d.message,d.failed);reset()}}catch(e){controls(false);message(e.message,true)}}
$('save').onclick=()=>{const a=document.createElement('a');a.href=URL.createObjectURL(new Blob([log],{type:'text/plain'}));a.download='tinkerbytetech-gaming-setup.log';a.click();setTimeout(()=>URL.revokeObjectURL(a.href),1000)};
$('close').onclick=async()=>{try{await api('close',{});message('Installer closed. You can close this tab.');document.querySelectorAll('button,input').forEach(n=>n.disabled=true)}catch(e){message(e.message,true)}};
api('info').then(d=>{demo=d.demo;$('title').textContent='Gaming setup for '+d.target;$('distro').textContent=d.detected;$('dry').checked=true;if(d.demo){$('dry').disabled=true;message('Interactive preview — no packages will be installed.')}else if(d.blocked)message(d.blocked,true);d.options.forEach(o=>{const label=document.createElement('label');label.className='option';const input=document.createElement('input');input.type='checkbox';input.value=o.key;input.checked=o.default;input.onchange=reset;const text=document.createElement('span'),b=document.createElement('b'),small=document.createElement('small');b.textContent=o.name;small.textContent=o.description;text.append(b,small);label.append(input,text);$('choices').append(label)})}).catch(e=>message(e.message,true));
</script></html>'''


class Setup:
    def __init__(self, target, demo=False):
        self.target, self.demo = target, demo
        self.authorization = 'pkexec'
        self.token, self.nonce = secrets.token_urlsafe(32), secrets.token_urlsafe(24)
        self.info = read_os_release()
        self.blocked = compatible(target, self.info, platform.machine(), Path('/run/ostree-booted').exists())
        self.lock = threading.Lock()
        self.running, self.failed, self.progress = False, False, 0
        self.message, self.log = 'Ready.', []
        self.origin = ''

    def snapshot(self):
        with self.lock:
            return dict(running=self.running, failed=self.failed, progress=self.progress,
                        message=self.message, log=list(self.log))

    def append(self, message):
        with self.lock:
            self.log.append(message)
            self.log = self.log[-1200:]

    def command(self, step):
        argv = list(step['argv'])
        if step.get('app'):
            flatpak = shutil.which('flatpak', path='/usr/bin:/bin')
            if flatpak:
                for scope in ('--user', '--system'):
                    existing = subprocess.run([flatpak, scope, 'info', step['app']], stdout=subprocess.DEVNULL,
                                              stderr=subprocess.DEVNULL, timeout=30)
                    if existing.returncode == 0:
                        self.append('Already installed ('+scope.removeprefix('--')+'); keeping it.')
                        return
        if argv[:3] == ['flatpak', '--user', 'remote-add']:
            flatpak = shutil.which('flatpak', path='/usr/bin:/bin')
            if flatpak:
                remotes = subprocess.run([flatpak, '--user', 'remotes', '--columns=name,url'],
                                         capture_output=True, text=True, timeout=30)
                if remotes.returncode:
                    raise RuntimeError('Could not inspect existing Flatpak repositories.')
                for line in remotes.stdout.splitlines():
                    fields = line.split()
                    if fields and fields[0] == 'flathub' and (len(fields) < 2 or fields[1].rstrip('/') not in
                       ('https://dl.flathub.org/repo', 'https://flathub.org/repo')):
                        raise RuntimeError('Your user Flathub remote has a different URL. Review it in your software manager before continuing.')
        binary = shutil.which(argv[0], path='/usr/sbin:/usr/bin:/sbin:/bin')
        if not binary:
            raise RuntimeError(f'{argv[0]} is unavailable. Check the previous step and your distribution packages.')
        argv[0] = binary
        if step['admin']:
            pkexec = shutil.which(self.authorization, path='/usr/bin:/bin')
            if not pkexec:
                raise RuntimeError('Administrator authentication needs '+self.authorization+'.')
            argv.insert(0, pkexec)
            if self.authorization == 'sudo':
                argv.insert(1, '-n')
        env = dict(os.environ, LC_ALL='C', LANG='C')
        process = subprocess.Popen(argv, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                                   stdin=subprocess.DEVNULL, text=True, errors='replace', env=env, start_new_session=True)
        timed_out = threading.Event()
        def expire():
            timed_out.set()
            process.terminate()
        timer = threading.Timer(3600, expire)
        timer.start()
        try:
            for line in process.stdout:
                self.append(line.rstrip()[:2000])
            code = process.wait()
        finally:
            timer.cancel()
        if timed_out.is_set():
            raise RuntimeError('This step exceeded one hour. Check the package manager before retrying.')
        if code:
            raise RuntimeError(f'{step["title"]} stopped (exit {code}). Details are in the log above.')

    def run(self, steps, dry):
        try:
            for index, step in enumerate(steps):
                self.append(f'\n[{index+1}/{len(steps)}] {step["title"]}')
                self.append(('[administrator] ' if step['admin'] else '') + shlex.join(step['argv']))
                if dry:
                    time.sleep(0.1)
                else:
                    self.command(step)
                with self.lock:
                    self.progress = round((index+1)*100/len(steps))
            with self.lock:
                self.message = 'Preview complete. No packages were installed.' if dry else 'Selected tools installed. Open them from your application menu; sign out and back in if new launchers do not appear.'
        except (OSError, subprocess.SubprocessError, RuntimeError) as exc:
            self.append(str(exc))
            with self.lock:
                self.failed, self.message = True, str(exc)
        finally:
            with self.lock:
                self.running = False

    def start(self, choices, identity, dry):
        if not isinstance(dry, bool):
            raise ValueError('Invalid preview setting.')
        steps = build_plan(self.target, choices)
        if identity != plan_id(choices, steps):
            raise ValueError('Review the selected setup before starting.')
        dry = dry or self.demo
        if self.blocked and not dry:
            raise ValueError(self.blocked)
        if os.geteuid() == 0 and not dry:
            raise ValueError('Run the installer as your regular desktop user, without sudo.')
        with self.lock:
            if self.running:
                raise ValueError('Setup is already running.')
            self.running, self.failed, self.progress = True, False, 0
            self.message, self.log = 'Starting…', []
        threading.Thread(target=self.run, args=(steps, dry), daemon=True).start()


def make_handler(setup):
    class Handler(BaseHTTPRequestHandler):
        def log_message(self, *_):
            pass

        def send(self, code, value, kind='application/json'):
            body = value.encode() if isinstance(value, str) else json.dumps(value).encode()
            self.send_response(code)
            self.send_header('Content-Type', kind + '; charset=utf-8')
            self.send_header('Content-Length', str(len(body)))
            self.send_header('Cache-Control', 'no-store')
            self.send_header('X-Content-Type-Options', 'nosniff')
            self.send_header('Referrer-Policy', 'no-referrer')
            self.send_header('Content-Security-Policy', f"default-src 'none'; script-src 'nonce-{setup.nonce}'; style-src 'nonce-{setup.nonce}'; connect-src 'self'; img-src blob:; base-uri 'none'; frame-ancestors 'none'; form-action 'none'")
            self.end_headers()
            self.wfile.write(body)

        def valid_host(self):
            return self.headers.get('Host') == setup.origin.removeprefix('http://')

        def authorized(self):
            token = self.headers.get('X-Setup-Token', '')
            return secrets.compare_digest(token, setup.token)

        def do_GET(self):
            if not self.valid_host():
                return self.send(403, {'error': 'Invalid host.'})
            if self.path == '/':
                return self.send(200, PAGE.replace('__NONCE__', setup.nonce), 'text/html')
            if not self.authorized():
                return self.send(403, {'error': 'Open the installer using its printed link.'})
            if self.path == '/api/info':
                options = [dict(key=k, name=v[0], description=v[2], default=k != 'protonup') for k, v in APPS.items()]
                options += [dict(key=k, name=v, description={'wine': 'Windows applications through distribution packages', 'gamemode': 'Optional game performance helper', 'mangohud': 'Optional performance overlay'}[k], default=False) for k, v in NATIVE.items()]
                return self.send(200, dict(target=DISTROS[setup.target], detected=('Preview for '+DISTROS[setup.target]) if setup.demo else setup.info.get('PRETTY_NAME','Linux'), blocked='' if setup.demo else setup.blocked, demo=setup.demo, options=options))
            if self.path == '/api/state':
                return self.send(200, setup.snapshot())
            return self.send(404, {'error': 'Not found.'})

        def do_POST(self):
            if not self.valid_host() or not self.authorized() or self.headers.get('Origin') != setup.origin:
                return self.send(403, {'error': 'Request refused.'})
            try:
                size = int(self.headers.get('Content-Length', '0'))
                if size <= 0 or size > 8192:
                    raise ValueError('Invalid request size.')
                data = json.loads(self.rfile.read(size))
                if not isinstance(data, dict):
                    raise ValueError('Invalid request.')
                if self.path == '/api/close':
                    if setup.snapshot()['running']:
                        raise ValueError('Wait for the current setup to finish before closing.')
                    self.send(200, {'closed': True})
                    threading.Thread(target=self.server.shutdown, daemon=True).start()
                    return
                choices = validate_choices(data.get('choices'))
                steps = build_plan(setup.target, choices)
                if self.path == '/api/plan':
                    return self.send(200, dict(id=plan_id(choices, steps), steps=steps, blocked='' if setup.demo else setup.blocked))
                if self.path == '/api/start':
                    setup.start(choices, data.get('plan'), data.get('dry_run'))
                    return self.send(202, {'started': True})
                return self.send(404, {'error': 'Not found.'})
            except (ValueError, json.JSONDecodeError) as exc:
                return self.send(400, {'error': str(exc)})
    return Handler


def main(argv=None):
    parser = argparse.ArgumentParser(description='TinkerByteTech '+DISTROS.get(TARGET,'Gaming')+' graphical setup')
    parser.add_argument('--demo', action='store_true', help='Interactive preview; installation is disabled')
    parser.add_argument('--no-browser', action='store_true', help='Print the local interface link without opening it')
    parser.add_argument('--port', type=int, default=0, help='Local interface port (default: choose an available port)')
    args = parser.parse_args(argv)
    if TARGET not in DISTROS:
        parser.error('Use one of the individual distro downloads.')
    setup = Setup(TARGET, args.demo)
    with ThreadingHTTPServer(('127.0.0.1', args.port), make_handler(setup)) as server:
        setup.origin = f'http://127.0.0.1:{server.server_port}'
        url = setup.origin+'/#'+setup.token
        print('TinkerByteTech '+DISTROS[TARGET]+' Gaming Setup '+VERSION, flush=True)
        print('Open: '+url, flush=True)
        print('Press Ctrl+C to close the installer.', flush=True)
        if not args.no_browser:
            webbrowser.open(url)
        while True:
            try:
                server.serve_forever()
                break
            except KeyboardInterrupt:
                if setup.snapshot()['running']:
                    print('Setup is still running. Let it finish, then close the installer.', flush=True)
                    continue
                break
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
