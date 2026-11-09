# 마스코트 인터랙션: 시간대 인사·생일·잠들기·쓰다듬기·끌 때 잘자요·설정 보존을 실제 창으로 확인한다
import ctypes
import datetime
import importlib.machinery
import importlib.util
import json
import os
import sys
import tempfile
import threading
import time

loader = importlib.machinery.SourceFileLoader("claude_mascot", sys.argv[1] if len(sys.argv) > 1 else os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "mascot", "claude_mascot.pyw"))
spec = importlib.util.spec_from_loader("claude_mascot", loader)
cm = importlib.util.module_from_spec(spec)
loader.exec_module(cm)
tmp = tempfile.mkdtemp()
cm.DATA_DIR, cm.USAGE_GLOB, cm.CONFIG_PATH = tmp, os.path.join(tmp, "usage-*.json"), os.path.join(tmp, "mascot.json")
json.dump({"x": 300, "y": 300, "birthdays": {"Alice": "10-28"}}, open(cm.CONFIG_PATH, "w"))
cm.Mascot.fetch_status = lambda self: None
cm.SESSIONS_GLOB = os.path.join(tempfile.mkdtemp(), '*.json')
cm.TALK_MS = cm.OUTAGE_TALK_MS = 800
cm.PET_MS = 800
cm.GOODNIGHT_MS = 1000
clock = {"now": datetime.datetime(2026, 10, 28, 8, 30)}
cm.local_now = lambda: clock["now"]  # 시간대·생일 판정용 시각을 고정한다

m = cm.Mascot()
results = []


def check(name, ok, info=""):
    results.append(ok)
    print("PASS" if ok else "FAIL", name, info, flush=True)


def bubble_text():
    return m.bubble.winfo_children()[0].cget("text") if m.bubble else ""


def click():
    m.root.event_generate("<ButtonPress-1>", x=80, y=100, rootx=m.x + 80, rooty=m.y + 100)
    m.root.event_generate("<ButtonRelease-1>", x=80, y=100, rootx=m.x + 80, rooty=m.y + 100)


def rub(y, xs=(60, 80, 60, 80, 60, 80)):
    for x in xs:
        m.root.event_generate("<Motion>", x=x, y=y, rootx=m.x + x, rooty=m.y + y)


def summary(indicator):
    return {"status": {"indicator": indicator, "description": "d"}, "components": [], "incidents": []}


steps = []
step = lambda fn: (steps.append(fn), fn)[1]


@step
def s1():
    t = bubble_text()
    check("켜질 때 생일 축하 한 줄 + birthday 이미지 (10-28 변경)", t == "Alice 생일 축하해요!" and m.shown == "birthday", (m.shown, t))


@step
def s2():
    check("생일엔 평상시 이미지 = birthday", m.shown == "birthday", m.shown)
    click()
    t = bubble_text()
    check("생일 축하에 밀린 아침 인사는 첫 클릭 때", t.startswith("좋은 아침이에요!") and "생일" not in t, t.replace("\n", " / "))


@step
def s2b():
    click()
    t = bubble_text()
    check("같은 시간대 두 번째 → 인사·생일 반복 안 함", "좋은 아침" not in t and "생일" not in t, t.replace("\n", " / "))


@step
def s3():
    clock["now"] = datetime.datetime(2026, 10, 28, 12, 10)
    click()
    t = bubble_text()
    check("점심 시간대 첫 클릭 → 점심 인사", t.startswith("점심 맛있게 드세요"), t.replace("\n", " / "))


@step
def s4():
    clock["now"] = datetime.datetime(2026, 10, 28, 15, 0)
    click()
    t = bubble_text()
    check("인사 없는 시간대(15시) → 인사 없음", "좋은 아침" not in t and "점심" not in t and "수고" not in t, t.replace("\n", " / "))


@step
def s5():
    m.last_touch = time.monotonic() - 11 * 60
    m.show()
    check("10분 넘게 안 건드리면 잠듦", m.shown == "sleep", m.shown)
    click()


@step
def s6():
    check("클릭하면 깨어남(말풍선 끝난 뒤 sleep 아님)", m.shown != "sleep", m.shown)
    m.set_status(summary("major"))
    m.last_touch = time.monotonic() - 11 * 60
    m.show()
    check("장애 중엔 잠들지 않음(sick)", m.shown == "sick", m.shown)


@step
def s7():
    m.set_status(summary("none"))


@step
def s8():
    rub(140)  # 다리 쪽에서 문지르기
    check("머리 아닌 곳 문지르기 → 반응 없음", m.shown != "pet" and m.bubble is None, m.shown)
    rub(30)  # 머리 위에서 문지르기
    t = bubble_text()
    check("머리 쓰다듬기 → pet 이미지 + 한마디", m.shown == "pet" and t in cm.PET_LINES, (m.shown, t))


@step
def s9():
    check("쓰다듬기 끝 → pet 해제", m.shown != "pet", m.shown)
    m.root.event_generate("<ButtonPress-1>", x=80, y=100, rootx=m.x + 80, rooty=m.y + 100)
    m.root.event_generate("<B1-Motion>", x=120, y=100, rootx=m.x + 120, rooty=m.y + 100)
    m.root.event_generate("<ButtonRelease-1>", x=120, y=100, rootx=m.x + 80 + 40, rooty=m.y + 100)
    saved = json.load(open(cm.CONFIG_PATH, encoding="utf-8"))
    check("끌어서 위치 저장해도 생일 목록 보존", saved.get("birthdays") == {"Alice": "10-28"} and saved.get("x") == m.x, saved)


@step
def s10():
    clock["now"] = datetime.datetime(2026, 10, 29, 19, 0)  # 다음 날 저녁, 생일 아님
    m.show()
    check("생일 지나면 평상시 idle", m.shown.startswith("idle"), m.shown)
    m.tray_hwnd = m.tray._hwnd
    m.tray_threads = [t for t in threading.enumerate() if getattr(t, "_target", None) == m.tray.run]
    m.quit()
    t = bubble_text()
    check("완전히 종료 → goodnight 이미지 + 잘자요", m.shown == "goodnight" and "잘자요" in t, (m.shown, t))
    check("잘자요 동안은 아직 안 꺼짐", m.root.winfo_exists() == 1)


def run(i=0):
    if i == len(steps):
        return
    try:
        steps[i]()
    except Exception as e:
        check(f"step {i} 예외", False, repr(e))
    m.root.after(1300, run, i + 1)


m.root.after(1500, run)
m.root.mainloop()

from pystray._util import win32 as pwin32


def tray_exists(icon, hwnd):
    data = pwin32.NOTIFYICONDATAW(cbSize=ctypes.sizeof(pwin32.NOTIFYICONDATAW), hWnd=hwnd, hID=id(icon), uFlags=pwin32.NIF_TIP, szTip="probe")
    try:
        return bool(pwin32.Shell_NotifyIcon(pwin32.NIM_MODIFY, ctypes.byref(data)))
    except Exception:
        return False


threads = getattr(m, "tray_threads", [])
for t in threads:
    t.join(timeout=3)
check("잘자요 뒤 종료 + 트레이 아이콘 삭제", len(threads) == 1 and not threads[0].is_alive() and not tray_exists(m.tray, m.tray_hwnd))
print("ALL", "PASS" if results and all(results) else "FAIL")
