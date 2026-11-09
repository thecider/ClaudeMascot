# 말풍선 따라가기(11-03): 말하는 중에 클순이를 끌어 옮기면 말풍선도 따라온다
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
    json.dump({"x": 600, "y": 500, "birthdays": {}}, f)

m = cm.Mascot()
results = []


def check(name, ok, info=""):
    results.append(ok)
    print("PASS" if ok else "FAIL", name, info, flush=True)


def bubble_xy():
    m.root.update_idletasks()
    return m.bubble.winfo_x(), m.bubble.winfo_y()


def expected_x():
    left, _, right, _ = m.work_area()
    width = m.bubble.winfo_reqwidth()
    return max(left, min(m.x + (m.images["talk"].width - width) // 2, right - width))


ev = lambda x, y: types.SimpleNamespace(x_root=x, y_root=y)


def s1():
    m.speak(body="따라와요", duration=10 ** 7)
    m.root.update()
    x0, y0 = bubble_xy()
    check("말풍선은 클순이 위", x0 == expected_x() and y0 < m.y, (x0, y0, m.x, m.y))
    m.on_press(ev(700, 600))
    m.on_drag(ev(500, 650))
    m.root.update()
    x1, y1 = bubble_xy()
    check("끄는 동안 말풍선이 따라온다", x1 == expected_x() and x1 != x0 and y1 == m.y - m.bubble.winfo_reqheight() - 4, (x1, y1, m.x, m.y))
    left, top, right, bottom = m.work_area()
    m.on_drag(ev(right + 400, 650))  # 화면 밖까지 끌었다 놓으면 안으로 당겨진다
    m.on_release(ev(right + 400, 650))
    m.root.update()
    x2, _ = bubble_xy()
    check("놓아서 안으로 당겨지면 말풍선도 맞춘다", x2 == expected_x() and m.bubble is not None, (x2, m.x))


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
