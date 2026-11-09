# 자동 업데이트(11-02): 6시간마다 최신 릴리스 확인. 「자동 업데이트」 꺼짐(기본) = 새 버전 알림, 켜짐 = 받아서 해시 확인 후 교체·재시작
import hashlib
import importlib.machinery
import importlib.util
import json
import os
import pathlib
import sys
import tempfile

loader = importlib.machinery.SourceFileLoader("claude_mascot", sys.argv[1] if len(sys.argv) > 1 else os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "mascot", "claude_mascot.pyw"))
spec = importlib.util.spec_from_loader("claude_mascot", loader)
cm = importlib.util.module_from_spec(spec)
loader.exec_module(cm)
tmp = tempfile.mkdtemp()
cm.DATA_DIR, cm.USAGE_GLOB, cm.CONFIG_PATH = tmp, os.path.join(tmp, "usage-*.json"), os.path.join(tmp, "mascot.json")
cm.CHARACTERS_DIR = os.path.join(tmp, "characters")
cm.INBOX_DIR = os.path.join(tmp, "inbox")
cm.NOTIFY_PATH = os.path.join(tmp, "notify.json")
cm.SESSIONS_GLOB = os.path.join(tmp, "sessions", "*.json")
cm.Mascot.fetch_status = lambda self: None
cm.WALK_EVERY_MS = (600_000, 600_000)
cm.UPDATE_FIRST_MS = 10 ** 7
cm.UPDATE_RETRY_MS = 300
cm.GAME_TICK_MS = 10 ** 7
cm.DOWNLOAD_PREFIX = "file:"
with open(cm.CONFIG_PATH, "w", encoding="utf-8") as f:
    json.dump({"x": 1000, "birthdays": {}}, f)

app = os.path.join(tmp, "app")
os.makedirs(app)
exe = os.path.join(app, "ClaudeMascot.exe")
pathlib.Path(exe).write_bytes(b"old exe")
payload = os.path.join(tmp, "new.bin")
new_bytes = b"new exe " * 5000
pathlib.Path(payload).write_bytes(new_bytes)
digest = "sha256:" + hashlib.sha256(new_bytes).hexdigest()

cm.app_version = lambda: "v1.7.0"
cm.exe_path = lambda: exe
fetches = []
release = {}
cm.fetch_release = lambda: (fetches.append(1), release.get("info"))[1]
launched = []
cm.launch_updated = lambda path, tag: launched.append((path, tag))
quits = []
real_finish = cm.Mascot.finish_quit
cm.Mascot.finish_quit = lambda self: quits.append(1)
spoken = []
real_speak = cm.Mascot.speak


def speak(self, headline=None, body=None, duration=None, link=None, pose=None):
    spoken.append((body or headline or "", link))
    real_speak(self, headline, body, duration, link, pose)


cm.Mascot.speak = speak
real_greet = cm.Mascot.greet_on_start
cm.Mascot.greet_on_start = lambda self: None
m = cm.Mascot()
results = []


def check(name, ok, info=""):
    results.append(ok)
    print("PASS" if ok else "FAIL", name, info, flush=True)


def info(tag, good=True):
    return {"tag": tag, "page": f"https://example.invalid/{tag}", "url": pathlib.Path(payload).as_uri(),
            "size": len(new_bytes), "digest": digest if good else "sha256:" + "0" * 64}


def config():
    with open(cm.CONFIG_PATH, encoding="utf-8") as f:
        return json.load(f)


def quiet():
    if m.bubble is not None:
        m.stop_talking(m.bubble)


steps = []
step = lambda fn: (steps.append(fn), fn)[1]


@step
def s1():
    check("버전 비교 1.10.0 > 1.9.0", cm.parse_version("v1.10.0") > cm.parse_version("v1.9.0"))
    check("이상한 태그는 None", cm.parse_version("latest") is None)
    labels = [item.text for item in m.tray.menu.items]
    check("트레이에 「자동 업데이트」·「지금 업데이트 확인」", "자동 업데이트" in labels and "지금 업데이트 확인" in labels, labels)
    check("자동 업데이트는 기본 끔", m.auto_update is False)
    release["info"] = info("v1.8.0")
    m.check_update()


@step
def s2():
    text, link = spoken[-1] if spoken else ("", None)
    check("꺼짐: 새 버전을 말한다", "새 버전" in text and "v1.8.0" in text, spoken[-1:])
    check("말풍선을 누르면 릴리스 페이지", link == "https://example.invalid/v1.8.0", link)
    check("최근 알림에도", any("v1.8.0" in label for label, _, _ in m.history))
    check("꺼짐이면 exe 는 그대로", pathlib.Path(exe).read_bytes() == b"old exe" and not launched)
    quiet()
    m.count = len(spoken)
    m.check_update()


@step
def s3():
    check("같은 버전은 한 번만 말한다", len(spoken) == m.count, spoken[m.count:])
    release["info"] = info("v1.7.0")
    m.check_update(True)


@step
def s4():
    check("지금 확인: 최신이면 최신이라고", "최신" in spoken[-1][0], spoken[-1:])
    quiet()
    release["info"] = None
    m.check_update(True)


@step
def s5():
    check("지금 확인: 조회 실패를 말한다", "확인하지 못했어요" in spoken[-1][0], spoken[-1:])
    quiet()
    m.toggle_auto_update()


@step
def s6():
    check("자동 업데이트 켜기 저장", config().get("auto_update") is True and m.auto_update)
    quiet()
    release["info"] = info("v1.9.0", good=False)
    m.check_update()


@step
def s7():
    check("해시가 다르면 교체하지 않는다", pathlib.Path(exe).read_bytes() == b"old exe" and not launched and not os.path.exists(exe + ".new"))
    check("교체 못 하면 새 버전 알림으로", "v1.9.0" in spoken[-1][0], spoken[-1:])
    quiet()
    release["info"] = info("v1.9.0")
    m.play_game()
    m.check_update()


@step
def s8():
    check("게임 중에는 받아 두고 기다린다", os.path.exists(exe + ".new") and not launched and pathlib.Path(exe).read_bytes() == b"old exe")
    m.game.close()
    quiet()


@step
def s9():
    check("한가해지면 교체한다", pathlib.Path(exe).read_bytes() == new_bytes, pathlib.Path(exe).read_bytes()[:10])
    check("옛 exe 는 .old 로", pathlib.Path(exe + ".old").read_bytes() == b"old exe")
    check("새 exe 를 띄우고", launched == [(exe, "v1.9.0")], launched)
    check("지금 것은 끈다", quits == [1], quits)
    pathlib.Path(exe).write_bytes(b"only")
    check("받은 파일이 없으면 교체 실패, exe 는 그대로", not cm.swap_exe(exe) and pathlib.Path(exe).read_bytes() == b"only")
    m.closing = False
    m.cleanup_update()
    check("다음 실행 때 .old·.new 를 치운다", not os.path.exists(exe + ".old") and not os.path.exists(exe + ".new"))
    m.updated_to = "v1.9.0"
    cm.Mascot.greet_on_start = real_greet
    m.greet_on_start()
    check("업데이트 뒤 켜지면 말한다", "v1.9.0" in spoken[-1][0] and "업데이트" in spoken[-1][0], spoken[-1:])
    quiet()
    m.version = None
    n = len(fetches)
    m.check_update(True)
    check("버전 없는 실행(.pyw·로컬 빌드)은 확인하지 않는다", len(fetches) == n)


def run(i=0):
    if i == len(steps):
        print("ALL", "PASS" if results and all(results) else "FAIL", flush=True)
        m.closing = True
        real_finish(m)
        return
    try:
        steps[i]()
    except Exception as e:
        check(f"step {i} 예외", False, repr(e))
    m.root.after(1500, run, i + 1)


m.root.after(1500, run)
m.root.mainloop()
