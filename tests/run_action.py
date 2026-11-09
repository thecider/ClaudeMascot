# 행동 메뉴(11-05): 「행동 > 걷기」로 기다리지 않고 바로 걷게 한다
import importlib.machinery
import importlib.util
import json
import os
import sys
import tempfile

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
    json.dump({"x": 1000, "y": 600, "walk": False, "birthdays": {}}, f)  # 저절로 걷기는 꺼 둔 사람

m = cm.Mascot()
results = []


def check(name, ok, info=""):
    results.append(ok)
    print("PASS" if ok else "FAIL", name, info, flush=True)


def walk_by_menu():
    m.action_menu.invoke(m.action_menu.index("걷기"))


def reset():
    m.stop_walk()
    m.stop_eat()
    m.working = None
    m.status = None
    if m.bubble is not None:
        m.stop_talking(m.bubble)


steps = []
step = lambda fn: (steps.append(fn), fn)[1]
x0 = []


@step
def s1():
    labels = [m.menu.entrycget(i, "label") for i in range(m.menu.index("end") + 1) if m.menu.type(i) != "separator"]
    check("메뉴: 식사 주기 다음에 「행동」", labels[labels.index("식사 주기") + 1] == "행동", labels)
    check("행동 > 걷기", hasattr(m, "action_menu") and[m.action_menu.entrycget(i, "label") for i in range(m.action_menu.index("end") + 1)] == ["걷기"])
    walk_by_menu()
    check("누르면 바로 걷는다(저절로 걷기를 꺼 두었어도)", m.walking is not None and m.shown.startswith("walk"), (m.walking, m.shown))
    x0[:] = [m.x]


@step
def s2():
    check("메뉴로 시킨 걸음은 계속 걷는다", m.x != x0[0] and m.walking is not None, (x0, m.x))
    reset()
    check("멈추면 시킨 걸음 표시도 풀린다", m.walk_asked is False)
    m.start_walk()
    check("저절로 걷기를 꺼 두었으면 저절로는 안 걷는다", m.walking is None)
    m.working = [0]
    m.show()
    walk_by_menu()
    check("작업 중 그림이어도 시키면 걷는다", m.walking is not None and m.shown.startswith("walk"), m.shown)
    reset()
    m.last_touch -= cm.SLEEP_MINUTES * 60 + 1
    m.show()
    walk_by_menu()
    check("자고 있으면 깨어서 걷는다", m.walking is not None, m.shown)
    reset()
    m.feed()
    walk_by_menu()
    check("먹던 중이면 그만 먹고 걷는다", m.eating is None and m.walking is not None)
    reset()
    m.speak(body="말하는 중", duration=10 ** 7)
    walk_by_menu()
    check("말하는 중이면 안 걷는다", m.walking is None and m.walk_asked is False)
    reset()
    m.status = {"status": {"indicator": "major"}}
    x = m.x
    walk_by_menu()
    check("장애(아픈 그림)면 한 걸음도 안 걷는다", m.walking is None and m.x == x and m.shown == "sick", (m.shown, m.x, x))
    reset()


def run(i=0):
    if i == len(steps):
        print("ALL", "PASS" if results and all(results) else "FAIL", flush=True)
        m.closing = True
        m.finish_quit()
        return
    try:
        steps[i]()
    except Exception as e:
        check(f"step {i} 예외", False, repr(e))
    m.root.after(1500, run, i + 1)


m.root.after(1500, run)
m.root.mainloop()
