# 생일 축하 말풍선(10-28): 생일이 되면 스스로 「<이름> 생일 축하해요!」만 birthday 이미지로 말한다, 하루 한 번, 바쁠 때·숨김 중엔 미룬다
import datetime
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
json.dump({"x": 300, "y": 300, "birthdays": {}}, open(cm.CONFIG_PATH, "w"))
cm.Mascot.fetch_status = lambda self: None
cm.SESSIONS_GLOB = os.path.join(tempfile.mkdtemp(), '*.json')
cm.TALK_MS = cm.OUTAGE_TALK_MS = 800
clock = {"now": datetime.datetime(2026, 10, 28, 15, 0)}  # 시간대 인사 없는 시각
cm.local_now = lambda: clock["now"]

m = cm.Mascot()
results = []


def check(name, ok, info=""):
    results.append(ok)
    print("PASS" if ok else "FAIL", name, info, flush=True)


def text():
    return m.bubble.winfo_children()[0].cget("text") if m.bubble else ""


def click():
    m.root.event_generate("<ButtonPress-1>", x=80, y=100, rootx=m.x + 80, rooty=m.y + 100)
    m.root.event_generate("<ButtonRelease-1>", x=80, y=100, rootx=m.x + 80, rooty=m.y + 100)


def set_birthday(day):
    json.dump({"x": m.x, "y": m.y, "birthdays": {"Alice": day}}, open(cm.CONFIG_PATH, "w"))


steps = []
step = lambda fn: (steps.append(fn), fn)[1]


@step
def s1():
    m.hide_window()
    set_birthday("10-28")  # 켜 둔 채 생일을 넣는다
    m.poll_mood()
    check("숨김 중엔 생일 말풍선 안 띄움", m.bubble is None)
    m.show_window()
    m.speak("Claude 장애가 났어요")  # 다른 말풍선이 떠 있을 때
    m.poll_mood()
    check("다른 말풍선 중엔 생일 말풍선으로 덮지 않음", "장애" in text(), text().replace("\n", " / "))


@step
def s2():
    m.poll_mood()  # 한가해진 뒤 다음 확인
    check("생일 말풍선은 축하 한 줄만", text() == "Alice 생일 축하해요!", text().replace("\n", " / "))
    check("생일 말풍선 중 이미지는 birthday", m.shown == "birthday", m.shown)


@step
def s3():
    check("생일 말풍선 끝나도 평상시 birthday", m.shown == "birthday" and m.bubble is None, m.shown)
    m.poll_mood()
    check("하루 한 번: 다시 확인해도 안 띄움", m.bubble is None)
    click()
    check("그 뒤 클릭은 사용량(축하 반복 없음) + talk", "생일" not in text() and m.shown == "talk", (m.shown, text().replace("\n", " / ")))


@step
def s4():
    clock["now"] = datetime.datetime(2027, 10, 28, 15, 0)  # 다음 해 생일
    m.poll_mood()
    check("날짜가 바뀌면 다시 축하", text() == "Alice 생일 축하해요!", text().replace("\n", " / "))


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
    m.root.after(1300, run, i + 1)


m.root.after(1500, run)
m.root.mainloop()
