# 서브 모니터(11-05): 클순이를 다른 모니터로 끌어 놓으면 거기 남는다. 전제: 주 0~2560, 서브 2560~5120 (둘 다 작업 영역 높이 1392)
import importlib.machinery
import importlib.util
import json
import os
import sys
import tempfile
import types

loader = importlib.machinery.SourceFileLoader("claude_mascot", sys.argv[1] if len(sys.argv) > 1 else os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "mascot", "claude_mascot.pyw"))
spec = importlib.util.spec_from_loader("claude_mascot", loader)
cm = importlib.util.module_from_spec(spec)
loader.exec_module(cm)
cm.IMAGE_DIR = os.environ.get("MASCOT_IMAGES", cm.IMAGE_DIR)
tmp = tempfile.mkdtemp()
cm.DATA_DIR, cm.USAGE_GLOB, cm.CONFIG_PATH = tmp, os.path.join(tmp, "usage-*.json"), os.path.join(tmp, "mascot.json")
cm.CHARACTERS_DIR = os.path.join(tmp, "characters")
cm.INBOX_DIR = os.path.join(tmp, "inbox")
cm.NOTIFY_PATH = os.path.join(tmp, "notify.json")
cm.SESSIONS_GLOB = os.path.join(tmp, "sessions", "*.json")
cm.Mascot.fetch_status = lambda self: None
cm.Mascot.greet_on_start = lambda self: None
cm.WALK_EVERY_MS = (600_000, 600_000)
cm.MOOD_POLL_MS = 10 ** 7
cm.GAME_TICK_MS = 10 ** 7
cm.app_version = lambda: None
with open(cm.CONFIG_PATH, "w", encoding="utf-8") as f:
    json.dump({"x": 3200, "y": 600, "birthdays": {}}, f)  # 서브 모니터에 저장된 위치로 켠다

m = cm.Mascot()
results = []


def check(name, ok, info=""):
    results.append(ok)
    print("PASS" if ok else "FAIL", name, info, flush=True)


ev = lambda x, y: types.SimpleNamespace(x_root=x, y_root=y)


def s1():
    if m.work_area(3200, 600) != (2560, 0, 5120, 1392):
        print("SKIP 모니터 배치가 다름(주 0~2560, 서브 2560~5120 이 아님)", m.work_area(3200, 600), flush=True)
        results.append(True)
        return
    check("서브 모니터에 저장된 위치로 켜진다", (m.x, m.y) == (3200, 600), (m.x, m.y))
    check("작업 영역 = 클순이가 있는 모니터", m.work_area() == (2560, 0, 5120, 1392), m.work_area())
    m.on_press(ev(1000, 700))
    m.on_drag(ev(1500, 700))
    m.on_release(ev(1500, 700))
    check("주 모니터로 끌어 놓으면 주 모니터", m.x < 2560 and m.work_area() == (0, 0, 2560, 1392), (m.x, m.work_area()))
    m.on_press(ev(1500, 700))
    m.on_drag(ev(3500, 700))
    m.on_release(ev(3500, 700))
    check("서브 모니터로 끌어 놓으면 거기 남는다", 2560 <= m.x < 5120 - m.images["idle_1"].width, m.x)
    with open(cm.CONFIG_PATH, encoding="utf-8") as f:
        check("서브 모니터 위치를 저장", json.load(f)["x"] == m.x)
    m.on_press(ev(3500, 700))
    m.on_drag(ev(5110, 700))  # 서브 모니터 오른쪽 끝 밖으로 걸치게 놓으면 서브 모니터 안으로 당긴다
    m.on_release(ev(5110, 700))
    check("서브 모니터 끝에 걸치면 그 모니터 안으로", m.x == 5120 - m.images["idle_1"].width, m.x)
    check("걷기 범위도 서브 모니터 기준", m.walk_room(-1) == m.x - 2560, m.walk_room(-1))


def run():
    try:
        s1()
    except Exception as e:
        check("예외", False, repr(e))
    print("ALL", "PASS" if results and all(results) else "FAIL", flush=True)
    m.closing = True
    m.finish_quit()


m.root.after(1500, run)
m.root.mainloop()
