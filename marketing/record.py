"""Record the 엄마 몰래 폰겜 promo on a virtual clock. python3 record.py [preview|full]"""
import json, os, subprocess, sys
from playwright.sync_api import sync_playwright
HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, 'out'); os.makedirs(os.path.join(OUT, 'stills'), exist_ok=True)
MODE = sys.argv[1] if len(sys.argv) > 1 else 'preview'
FPS, DT = 30, 1000 / 30
CLOCK = open(os.path.join(HERE, '..', 'zoo_video', 'record.py')).read().split('CLOCK = r"""')[1].split('"""')[0]
events, t_ms = [], 0.0
def main():
    global t_ms
    with sync_playwright() as p:
        browser = p.chromium.launch(executable_path='/usr/bin/google-chrome')
        page = browser.new_page(viewport={'width': 360, 'height': 640}, device_scale_factor=3)
        page.on('pageerror', lambda e: print('PAGE EXCEPTION:', e))
        page.add_init_script(CLOCK)
        page.goto('file://' + os.path.join(HERE, 'rec.html')); page.wait_for_timeout(300)
        ev = lambda code: page.evaluate('c => window.__M.ev(c)', code)
        cap = lambda html: page.evaluate('h => document.getElementById("cap").innerHTML = h', html)
        finger = lambda on: page.evaluate('o => document.getElementById("finger").style.display = o ? "block" : "none"', on)
        ff = None
        if MODE == 'full':
            ff = subprocess.Popen(['ffmpeg', '-y', '-loglevel', 'error', '-f', 'image2pipe', '-framerate', str(FPS), '-c:v', 'mjpeg', '-i', '-',
                                   '-c:v', 'libx264', '-preset', 'veryfast', '-crf', '20', '-pix_fmt', 'yuv420p', '-r', str(FPS), os.path.join(OUT, 'promo_silent.tmp.mp4')], stdin=subprocess.PIPE)
        def frames(n, still=None):
            global t_ms
            for i in range(n):
                page.evaluate('() => window.__tick(%f)' % DT)
                if ff: ff.stdin.write(page.screenshot(type='jpeg', quality=92))
                elif still and i == n - 1: page.screenshot(path=os.path.join(OUT, 'stills', still + '.png'))
                t_ms += DT
        def mark(n): events.append([n, round(t_ms / 1000, 3)])
        def hold(): finger(True); ev("press(true)"); mark('press')
        def let_go(): finger(False); ev("press(false)"); mark('release')
        # freeze the random interference and pin phases by hand
        ev("""nick = '빵돌이'; $('start').hidden = true; submitScore = async () => {}; logPlay = () => {};
              window.pin = (st, ph, prog) => { stage = st; state = 'play'; $('intro').hidden = true; $('over').hidden = true; setPhase(ph, 99); progress = prog; evNext = 1e12; snitch = null; notif = null; adUntil = 0; texts = []; bubble = null; holding = false; lives = 3; musicOn = true; hud(); };""")
        ev("newRun(); pin(0, 'away', .35); lv = 3.4;")

        # S0 hook: caught red-handed
        cap('엄마 몰래 폰겜하다<br><em>걸리면 생기는 일</em>')
        hold(); frames(16)
        ev("setPhase('warn', 99); say('흠…?', 9999); sfx('warn')"); mark('warn'); frames(10)
        ev("setPhase('look', 99); caught(); texts = []; floatText('등짝 스매싱!!', 300, '#e0453a', 34, 1500); phaseEnd = now + 99e3"); mark('smack')
        frames(40, still='s0'); finger(False)

        # S1 hold = game, release = study
        cap('꾹 누르면 폰겜<br><em>떼면 공부하는 척</em>')
        ev("pin(0, 'away', .2); say('♪ 흥얼흥얼', 9999)")
        frames(6); hold(); frames(26, still='s1a'); let_go(); frames(24, still='s1b')

        # S2 release right before the turn: safe
        cap('돌아보기 직전에 떼면<br><em>아슬아슬 세이프</em>')
        ev("pin(0, 'away', .5)"); hold(); frames(14)
        ev("setPhase('warn', .5); fakeNext = false; say('흠…?', 600); sfx('warn')"); mark('warn'); frames(10)
        let_go(); frames(10); mark('safe'); frames(30, still='s2')

        # S3 the snitch
        cap('근데 동생이<br><em>고자질함</em> ㅋㅋ')
        ev("pin(0, 'away', .7)"); hold(); frames(10)
        ev("const sn = SNITCH.mom; snitch = {at: now, name: sn[0], line: sn[1], col: sn[2]}; sfx('snitch')"); mark('snitch'); frames(26)
        ev("setPhase('look', 99); caught(); phaseEnd = now + 99e3"); mark('smack'); frames(36, still='s3'); finger(False)

        # S4 five watchers, quick cuts
        cap('부장님·여친·할머니까지<br><em>5단계 눈치싸움</em>')
        for st in (1, 2, 3, 4):
            ev(f"pin({st}, 'look', .4); bubble = {{text: A().peek, at: now - 300, until: now + 9999}}"); mark('cut'); frames(15, still=f's4_{st}')

        # S5 grandma wins
        cap('할머니는<br><em>못 이김</em> ㅋㅋ')
        ev("pin(4, 'away', .8); lives = 1"); hold(); frames(6)
        ev("setPhase('look', 99); caught(); phaseEnd = now + 99e3"); mark('smack'); frames(18); finger(False)
        ev("gameOver(); $('goBig').textContent = '할머니 눈치 못 이김 ㅋㅋ'; $('goSub').textContent = '세뱃돈 동결';"); mark('over')
        frames(54, still='s5')

        cap('')
        ev("""$('over').hidden = true; $('endcard').hidden = false; const c = $('endFace').getContext('2d'); c.fillStyle = '#f6eee4'; c.beginPath(); c.arc(140, 140, 130, 0, 7); c.fill(); c.save(); c.beginPath(); c.arc(140, 140, 130, 0, 7); c.clip(); drawWatcher(c, 'mom', 'angry', 140, 130, 1000, 1.6); c.restore();""")
        mark('endcard'); frames(96, still='s6')
        if ff:
            ff.stdin.close(); code = ff.wait()
            if code == 0: os.replace(os.path.join(OUT, 'promo_silent.tmp.mp4'), os.path.join(OUT, 'promo_silent.mp4'))
            print('ffmpeg exit', code)
        json.dump({'duration': round(t_ms / 1000, 3), 'events': events}, open(os.path.join(OUT, 'events.json'), 'w'), indent=1)
        print('duration', round(t_ms / 1000, 2), events); browser.close()
main()
