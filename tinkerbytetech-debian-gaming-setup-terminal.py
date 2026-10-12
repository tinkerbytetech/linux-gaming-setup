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

TARGET = 'debian'
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


# Original terminal interface, combined with our common planner by build.py.
import sys
from datetime import datetime

class TerminalSetup(Setup):
    def __init__(self, target, dry=False):
        super().__init__(target, dry)
        self.authorization = 'sudo'

    def append(self, message):
        super().append(message)
        print(message, flush=True)

    def command(self, step):
        if step['admin']:
            sudo = shutil.which('sudo', path='/usr/bin:/bin')
            if not sudo:
                raise RuntimeError('Install sudo through your distribution before running setup.')
            result = subprocess.run([sudo, '-v'])
            if result.returncode:
                raise RuntimeError('Administrator authentication was cancelled or refused.')
        super().command(step)


def terminal_choices(answer):
    numbers = list(APPS) + list(NATIVE)
    words = answer.replace(',', ' ').split()
    if not words:
        return ['steam', 'lutris', 'faugus']
    choices = []
    for word in words:
        if word.isdigit() and 1 <= int(word) <= len(numbers):
            choices.append(numbers[int(word)-1])
        else:
            raise ValueError('Choose tool numbers 1 through 7, separated by spaces.')
    return validate_choices(choices)


def terminal_main(argv=None):
    parser = argparse.ArgumentParser(description='TinkerByteTech '+DISTROS.get(TARGET,'Linux')+' interactive gaming setup')
    parser.add_argument('--dry-run', action='store_true', help='Print the setup without installing anything')
    parser.add_argument('--select', help='Comma-separated tool names, e.g. steam,lutris,faugus,wine')
    parser.add_argument('--yes', action='store_true', help='Install the reviewed command-line selection without the final prompt')
    args = parser.parse_args(argv)
    setup = TerminalSetup(TARGET, args.dry_run)
    print('\nTinkerByteTech | '+DISTROS[TARGET]+' Gaming Setup\n'+'─'*52)
    print('Detected: '+setup.info.get('PRETTY_NAME','Linux'))
    print('Tools: Steam · Lutris · Faugus Launcher · Wine\n')
    if args.select:
        try:
            choices = validate_choices([v.strip() for v in args.select.split(',')])
        except ValueError as exc:
            parser.error(str(exc))
    elif args.dry_run and not sys.stdin.isatty():
        choices = ['steam', 'lutris', 'faugus']
    else:
        if not sys.stdin.isatty():
            parser.error('Use --select with --dry-run or --yes when running without an interactive terminal.')
        print('Choose what to install:\n')
        for index, key in enumerate(list(APPS) + list(NATIVE), 1):
            name = APPS[key][0] if key in APPS else NATIVE[key]
            description = APPS[key][2] if key in APPS else 'Optional distribution package'
            print(f'  {index}. {name:<18} {description}')
        print('\nDefault: 1 2 3 (Steam, Lutris and Faugus)')
        while True:
            try:
                answer = input('Tool numbers, or Q to exit [1 2 3]: ').strip()
                if answer.lower() == 'q':
                    print('Setup cancelled.');return 0
                choices = terminal_choices(answer)
                break
            except ValueError as exc:
                print(str(exc))
            except (EOFError, KeyboardInterrupt):
                print('\nSetup cancelled.');return 0
    steps = build_plan(TARGET, choices)
    print('\nYOUR SETUP\n'+'─'*52)
    for index, step in enumerate(steps, 1):
        print(f'{index}. {step["title"]}')
        print('   '+('sudo ' if step['admin'] else '')+shlex.join(step['argv']))
    dry = args.dry_run
    if not dry and not args.yes:
        if not sys.stdin.isatty():
            parser.error('Use an interactive terminal, --dry-run, or --yes.')
        try:
            answer = input('\n[I] Install  [P] Preview  [Q] Quit [P]: ').strip().lower()
        except (EOFError, KeyboardInterrupt):
            print('\nSetup cancelled.');return 0
        if answer in ('', 'p'):
            dry = True
        elif answer != 'i':
            print('Setup cancelled.');return 0
    if setup.blocked and not dry:
        print('\n'+setup.blocked, file=sys.stderr);return 2
    if os.geteuid() == 0 and not dry:
        print('\nRun this script as your regular user, without sudo. It requests administrator access for individual system steps.',file=sys.stderr);return 2
    setup.demo = dry
    setup.start(choices, plan_id(choices,steps), dry)
    while setup.snapshot()['running']:
        try:
            time.sleep(.1)
        except KeyboardInterrupt:
            print('\nA setup step is running. Allow it to finish before closing the terminal.',flush=True)
    print('\n'+setup.message)
    if not dry:
        log_dir = Path.home()/'.local/state/tinkerbytetech/gaming-setup'
        try:
            log_dir.mkdir(parents=True, exist_ok=True)
            log_path = log_dir/(datetime.now().strftime('%Y%m%d-%H%M%S')+'.log')
            log_path.write_text('\n'.join(setup.log)+'\n')
            print('Log: '+str(log_path))
        except OSError as exc:
            print('Could not save log: '+str(exc),file=sys.stderr)
    return 1 if setup.failed else 0

if __name__ == '__main__':
    raise SystemExit(terminal_main())
