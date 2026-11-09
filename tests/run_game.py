# 게임하기(11-02): 오른쪽 클릭 「게임하기」 = 별도 창의 플래피 버드식 미니 게임. 같은 속도, 게임 중 알림은 「최근 알림」에만
import importlib.machinery
import importlib.util
import json
import os
import sys
import tempfile
import time

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
cm.GAME_TICK_MS = 10 ** 7  # 테스트가 step() 으로 한 칸씩 진행한다
with open(cm.CONFIG_PATH, "w", encoding="utf-8") as f:
    json.dump({"x": 1000, "birthdays": {}}, f)

cm.Mascot.greet_on_start = lambda self: None
m = cm.Mascot()
results = []


def check(name, ok, info=""):
    results.append(ok)
    print("PASS" if ok else "FAIL", name, info, flush=True)


def game_entry():
    for i in range(m.menu.index("end") + 1):
        if m.menu.type(i) == "command" and m.menu.entrycget(i, "label") == "게임하기":
            return lambda: m.menu.invoke(i)
    return None


def config():
    with open(cm.CONFIG_PATH, encoding="utf-8") as f:
        return json.load(f)


steps = []
step = lambda fn: (steps.append(fn), fn)[1]


@step
def s1():
    check("오른쪽 클릭 메뉴에 「게임하기」", game_entry() is not None)
    game_entry()()
    g = m.game
    check("게임 창이 열린다", g is not None and g.win.winfo_exists())
    check("게임 중엔 본체를 숨긴다", m.root.state() == "withdrawn", m.root.state())
    game_entry()()
    check("두 번 눌러도 창은 하나", m.game is g)


@step
def s2():
    g = m.game
    y = g.y
    for _ in range(30):
        g.step()
    check("첫 클릭 전에는 떨어지지 않는다", g.y == y and not g.over, (y, g.y))
    g.flap()
    check("클릭하면 시작하고 위로", g.started and g.vy < 0, g.vy)
    ys = [g.y]
    for _ in range(40):
        g.step()
        ys.append(g.y)
    top = min(range(len(ys)), key=ys.__getitem__)
    check("올라갔다가 중력으로 떨어진다", 0 < top < len(ys) - 1 and ys[-1] > ys[top], (ys[0], ys[top], ys[-1]))
    check("올라갈 때는 drag, 떨어질 때는 idle_1 그림", g.sprite_name() == "idle_1", g.sprite_name())


@step
def s3():
    g = m.game
    for _ in range(2000):
        if g.over:
            break
        g.step()
    check("가만히 두면 땅에 닿아 게임 오버", g.over)
    check("부딪히면 sick 그림", g.sprite_name() == "sick", g.sprite_name())


def fresh():
    g = m.game
    g.reset()
    g.flap()
    g.vy = 0
    g.pipes = []
    return g


@step
def s4():
    g = fresh()
    x1, y1, x2, y2 = g.bird_box()
    g.pipes = [[x1, y2 + 40, False]]  # 틈이 새보다 아래: 위 기둥에 부딪힌다
    g.vy = -cm.GAME_GRAVITY  # 이번 칸에 높이가 그대로
    g.step()
    check("기둥에 닿으면 게임 오버", g.over)
    g = fresh()
    x1, y1, x2, y2 = g.bird_box()
    mid = (y1 + y2) / 2
    g.pipes = [[x1, mid - cm.GAME_GAP / 2, False]]
    g.vy = -cm.GAME_GRAVITY
    g.step()
    check("틈으로 지나가면 계속", not g.over)
    g = fresh()
    g.y = -200
    g.step()
    check("천장에 닿아도 게임 오버", g.over)


@step
def s5():
    g = fresh()
    g.y = cm.GAME_SIZE[1] / 2
    x1, y1, x2, y2 = g.bird_box()
    g.pipes = [[x1 - cm.GAME_PIPE_W + 1, (y1 + y2) / 2 - cm.GAME_GAP / 2, False]]  # 새가 틈 한가운데: 부딪히지 않는다
    for _ in range(3):
        g.vy = -cm.GAME_GRAVITY
        g.step()
    check("기둥을 지나면 1점, 한 번만", g.score == 1, g.score)


@step
def s6():
    g = m.game
    g.score = 3
    g.y = 10 ** 4
    g.step()
    check("게임 오버 때 최고 점수 저장", g.over and config().get("game_best") == 3, config().get("game_best"))
    check("기록을 깨면 표시", g.new_record)
    g.flap()
    check("게임 오버 직후 클릭은 무시(연타 방지)", g.over)
    g.over_at -= 1
    g.flap()
    check("잠시 뒤 클릭하면 다시 시작", not g.over and g.score == 0)
    g.score = 1
    g.y = 10 ** 4
    g.step()
    check("낮은 점수는 최고 점수를 덮지 않는다", config().get("game_best") == 3 and not g.new_record, config().get("game_best"))


@step
def s7():
    os.makedirs(cm.INBOX_DIR, exist_ok=True)
    with open(os.path.join(cm.INBOX_DIR, "a.json"), "w", encoding="utf-8") as f:
        json.dump({"title": "게임 중 알림", "text": "t"}, f)
    m.check_alert({"status": {"indicator": "major"}, "incidents": []})


@step
def s8():
    labels = [label for label, _, _ in m.history]
    check("게임 중엔 말풍선을 띄우지 않는다", m.bubble is None)
    check("게임 중 스케줄 알림은 최근 알림에", any("게임 중 알림" in l for l in labels), labels)
    check("게임 중 장애 알림도 최근 알림에", any("장애" in l for l in labels), labels)
    m.game.close()
    check("창을 닫으면 게임이 끝나고", m.game is None)
    check("본체가 다시 보인다", m.root.state() == "normal", m.root.state())


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
    m.root.after(2500, run, i + 1)


m.root.after(1500, run)
m.root.mainloop()
