# 알림함(11-02): ~/.claude/claude-status/inbox/*.json 을 다른 프로그램이 넣으면 마스코트가 말하고 지운다. 오른쪽 클릭 「스케줄 알림」으로 끈다
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
tmp = tempfile.mkdtemp()
cm.DATA_DIR, cm.USAGE_GLOB, cm.CONFIG_PATH = tmp, os.path.join(tmp, "usage-*.json"), os.path.join(tmp, "mascot.json")
cm.NOTIFY_PATH = os.path.join(tmp, "notify.json")
cm.CHARACTERS_DIR = os.path.join(tmp, "characters")
inbox = cm.INBOX_DIR = os.path.join(tmp, "inbox")  # 옛 코드엔 없는 이름 — 넣어 둬도 무해
os.makedirs(inbox)
cm.Mascot.fetch_status = lambda self: None
cm.Mascot.greet_on_start = lambda self: None
cm.WALK_EVERY_MS = (600_000, 600_000)
with open(cm.CONFIG_PATH, "w", encoding="utf-8") as f:
    json.dump({"x": 1000, "birthdays": {}}, f)


def drop(name, data, raw=None):
    with open(os.path.join(inbox, name), "w", encoding="utf-8") as f:
        f.write(raw if raw is not None else json.dumps(data, ensure_ascii=False))


# 켜기 전에 쌓인 알림도 말한다
drop("000_early.json", {"title": "켜기 전", "text": "쌓여 있던 알림"})

spoken = []
cm.Mascot.speak = lambda self, **kw: spoken.append(kw)  # 말풍선은 띄우지 않고 기록만 (bubble 은 None 그대로). 켜는 중에 말하는 것도 잡으려고 만들기 전에 바꾼다
m = cm.Mascot()
results = []


def check(name, ok, info=""):
    results.append(ok)
    print("PASS" if ok else "FAIL", name, info, flush=True)


def toggle():
    for i in range(m.menu.index("end") + 1):
        if m.menu.type(i) == "checkbutton" and m.menu.entrycget(i, "label") == "스케줄 알림":
            return i
    return None


def left():
    return sorted(os.listdir(inbox))


steps = []
step = lambda fn: (steps.append(fn), fn)[1]


@step
def s1():
    i = toggle()
    check("오른쪽 클릭 메뉴에 「스케줄 알림」 체크", i is not None)
    check("처음엔 켜져 있음", i is not None and m.root.getvar(m.menu.entrycget(i, "variable")) in (1, True, "1"))
    check("켜기 전에 쌓인 알림도 말한다", any("쌓여 있던 알림" in (s.get("body") or "") for s in spoken), spoken)
    spoken.clear()
    drop("a.json", {"title": "아침 일감", "text": "새 일감 2건: #1, #2", "kind": "info", "link": tmp})


@step
def s2():
    s = spoken[0] if spoken else {}
    check("넣으면 말한다(제목 + 내용)", "아침 일감" in (s.get("body") or "") and "#1, #2" in (s.get("body") or ""), spoken)
    check("링크를 넘긴다(누르면 열림)", s.get("link") == tmp, s.get("link"))
    check("info 는 평소 그림", s.get("pose") is None, s.get("pose"))
    check("읽은 파일은 지운다", left() == [], left())
    check("최근 알림에 남는다", bool(m.history) and "아침 일감" in m.history[0][0], m.history[:1])
    spoken.clear()
    drop("b1.json", {"title": "하나", "kind": "warn"})
    drop("b2.json", {"title": "둘", "kind": "error"})
    drop("b3.json", {"title": "셋"})
    drop("bad.json", None, raw="{깨진")
    drop("c.tmp", None, raw="쓰는 중")


@step
def s3():
    titles = [s.get("body") for s in spoken]
    check("여러 개면 이름 순서로 다 말한다", titles == ["하나", "둘", "셋"], titles)
    check("warn 은 대기 그림, error 는 아픈 그림", [s.get("pose") for s in spoken[:2]] == ["waiting", "sick"], [s.get("pose") for s in spoken])
    check("깨진 파일은 말하지 않고 지운다, .json 아닌 파일은 그대로", left() == ["c.tmp"], left())
    os.remove(os.path.join(inbox, "c.tmp"))
    spoken.clear()
    m.bubble = "열림"  # 말풍선이 떠 있으면
    drop("d.json", {"title": "기다림"})


@step
def s4():
    check("말풍선이 떠 있는 동안은 기다린다", not spoken and left() == ["d.json"], (spoken, left()))
    m.bubble = None


@step
def s5():
    check("말풍선이 닫히면 말한다", [s.get("body") for s in spoken] == ["기다림"], spoken)
    spoken.clear()
    i = toggle()
    m.menu.invoke(i)
    m.history = []
    drop("e.json", {"title": "꺼짐", "text": "말하면 안 됨"})


@step
def s6():
    check("끄면 말하지 않는다", not spoken, spoken)
    check("꺼져 있어도 읽고 지우며 최근 알림엔 남긴다", left() == [] and bool(m.history) and "꺼짐" in m.history[0][0], (left(), m.history[:1]))
    check("끈 상태가 저장된다", cm.load_json(cm.CONFIG_PATH).get("inbox_notify") is False, cm.load_json(cm.CONFIG_PATH))


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
    m.root.after(5000, run, i + 1)


m.root.after(3000, run)
m.root.mainloop()
