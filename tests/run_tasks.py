# 예약 작업(11-25): 오른쪽 클릭 「예약 작업」에 작업 스케줄러 최상위 폴더의 내가 만든 작업(작성자가 비었거나 나)을 한 줄씩 보이고, 누르면 말한다
import datetime
import importlib.machinery
import importlib.util
import json
import os
import sys
import tempfile
import threading

loader = importlib.machinery.SourceFileLoader("claude_mascot", sys.argv[1] if len(sys.argv) > 1 else os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "mascot", "claude_mascot.pyw"))
spec = importlib.util.spec_from_loader("claude_mascot", loader)
cm = importlib.util.module_from_spec(spec)
loader.exec_module(cm)
tmp = tempfile.mkdtemp()
cm.DATA_DIR, cm.USAGE_GLOB, cm.CONFIG_PATH = tmp, os.path.join(tmp, "usage-*.json"), os.path.join(tmp, "mascot.json")
cm.NOTIFY_PATH = os.path.join(tmp, "notify.json")
cm.CHARACTERS_DIR = os.path.join(tmp, "characters")
cm.INBOX_DIR = os.path.join(tmp, "inbox")
cm.ERROR_LOG = os.path.join(tmp, "mascot_error.log")
cm.Mascot.fetch_status = lambda self: None
cm.Mascot.greet_on_start = lambda self: None
cm.WALK_EVERY_MS = (600_000, 600_000)
cm.local_now = lambda: datetime.datetime(2026, 11, 25, 15, 12)
os.environ["USERNAME"] = "alice"
with open(cm.CONFIG_PATH, "w", encoding="utf-8") as f:
    json.dump({"x": 1000, "birthdays": {}}, f)

TASKS = [
    {"name": "B_Daily", "author": None, "description": "아침 일감 수집", "state": "Ready", "last": "2026-11-25T09:00:01", "result": 0, "next": "2026-11-26T09:00:00"},
    {"name": "A_Watch", "author": "", "description": "계정 감시", "state": "Ready", "last": "2026-11-25T15:11:09", "result": 0, "next": "2026-11-25T15:16:08"},
    {"name": "C_Broken", "author": "PC\\Alice", "description": "", "state": "Ready", "last": "2026-11-24T22:00:00", "result": 1, "next": ""},
    {"name": "D_New", "author": "", "description": None, "state": "Ready", "last": "1999-11-30T00:00:00", "result": 0x41303, "next": "2026-11-25T22:00:00"},
    {"name": "E_Running", "author": "", "description": "도는 중", "state": "Running", "last": "2026-11-25T15:10:00", "result": 0x41301, "next": ""},
    {"name": "OneDrive Update", "author": "Microsoft Corporation", "description": "", "state": "Ready", "last": "2026-11-25T09:00:00", "result": 0, "next": ""},
    {"name": "Bob Task", "author": "PC\\bob", "description": "", "state": "Ready", "last": "2026-11-25T09:00:00", "result": 0, "next": ""},
]
gate = threading.Event()  # 처음 읽기를 붙잡아 「불러오는 중」을 본다
raw = {"text": json.dumps(TASKS, ensure_ascii=False)}
reads = []


def fake_raw():
    reads.append(1)
    gate.wait(10)
    return raw["text"]


cm.read_tasks_raw = fake_raw  # 옛 코드엔 없는 이름 — 넣어 둬도 무해
spoken = []
cm.Mascot.speak = lambda self, **kw: spoken.append(kw)
m = cm.Mascot()
results = []


def check(name, ok, info=""):
    results.append(ok)
    print("PASS" if ok else "FAIL", name, info, flush=True)


def tasks_menu():
    # 「예약 작업」 하위 메뉴 (없으면 None). 펼칠 때처럼 postcommand 를 불러 채운다
    for i in range(m.menu.index("end") + 1):
        if m.menu.type(i) == "cascade" and m.menu.entrycget(i, "label") == "예약 작업":
            sub = m.root.nametowidget(m.menu.entrycget(i, "menu"))
            m.root.tk.eval(sub.cget("postcommand"))
            return sub
    return None


def labels(sub):
    return [sub.entrycget(i, "label") for i in range(sub.index("end") + 1)] if sub is not None and sub.index("end") is not None else []


def press(sub, name):
    for i in range(sub.index("end") + 1):
        if name in sub.entrycget(i, "label"):
            sub.invoke(i)
            return
    raise KeyError(name)


steps = []
step = lambda fn: (steps.append(fn), fn)[1]


@step
def s1():
    sub = tasks_menu()
    check("오른쪽 클릭 메뉴에 「예약 작업」 하위 메뉴", sub is not None)
    names = [m.menu.entrycget(i, "label") for i in range(m.menu.index("end") + 1) if m.menu.type(i) in ("cascade", "command", "checkbutton")]
    check("「최근 알림」 바로 위", "예약 작업" in names and names.index("예약 작업") + 1 == names.index("최근 알림"), names)
    check("읽는 동안은 「불러오는 중」", labels(sub) == ["(불러오는 중…)"], labels(sub))
    check("켤 때 한 번 읽는다", len(reads) == 1, len(reads))
    gate.set()


@step
def s2():
    got = labels(tasks_menu())
    check("내가 만든 작업만 이름 순서로 (작성자 없음·빈칸·나는 대소문자 무시)", [l.split()[1] for l in got] == ["A_Watch", "B_Daily", "C_Broken", "D_New", "E_Running"], got)
    check("성공 줄: ✓ 이름  마지막 → 다음", "✓ A_Watch  15:11 → 15:16" in got, got)
    check("다음이 내일이면 「내일」", "✓ B_Daily  09:00 → 내일 09:00" in got, got)
    check("실패는 ✗, 어제는 「어제」, 다음이 없으면 -", "✗ C_Broken  어제 22:00 → -" in got, got)
    check("아직 안 돈 것은 ·, 마지막은 -", "· D_New  - → 22:00" in got, got)
    check("실행 중은 …", "… E_Running  15:10 → -" in got, got)
    spoken.clear()
    sub = tasks_menu()
    press(sub, "A_Watch")
    press(sub, "C_Broken")
    press(sub, "D_New")
    press(sub, "E_Running")


@step
def s3():
    bodies = [s.get("body") for s in spoken]
    check("누르면 이름·설명·마지막·다음을 말한다", bodies[:1] == ["A_Watch\n계정 감시\n마지막 15:11 성공 · 다음 15:16"], bodies)
    check("성공은 평소 그림", spoken and spoken[0].get("pose") is None, spoken[:1])
    check("실패는 결과 코드와 아픈 그림 (설명이 비면 줄 없음)", len(spoken) > 1 and spoken[1].get("body") == "C_Broken\n마지막 어제 22:00 실패(0x1) · 다음 없음" and spoken[1].get("pose") == "sick", spoken[1:2])
    check("아직 안 돈 것", bodies[2:3] == ["D_New\n아직 안 돌았어요 · 다음 22:00"], bodies[2:3])
    check("실행 중", bodies[3:4] == ["E_Running\n도는 중\n지금 도는 중이에요 (15:10 시작) · 다음 없음"], bodies[3:4])
    raw["text"] = json.dumps(TASKS[1], ensure_ascii=False)  # 작업이 하나면 PowerShell 은 배열이 아니라 객체 하나를 낸다
    m.menu.tk_popup = lambda x, y: None  # 오른쪽 클릭: 메뉴는 띄우지 않고 다시 읽는지만 본다
    m.popup_menu(type("E", (), {"x_root": 0, "y_root": 0})())


@step
def s4():
    check("오른쪽 클릭하면 다시 읽는다", len(reads) == 2, len(reads))
    check("작업이 하나여도 보인다", labels(tasks_menu()) == ["✓ A_Watch  15:11 → 15:16"], labels(tasks_menu()))
    raw["text"] = ""
    m.refresh_tasks()


@step
def s5():
    check("하나도 없으면 「없음」", labels(tasks_menu()) == ["(없음)"], labels(tasks_menu()))
    raw["text"] = None
    m.refresh_tasks()


@step
def s6():
    check("읽지 못하면 「불러오지 못했어요」", labels(tasks_menu()) == ["(불러오지 못했어요)"], labels(tasks_menu()))
    raw["text"] = "{깨진"
    m.refresh_tasks()


@step
def s7():
    check("깨진 출력도 「불러오지 못했어요」", labels(tasks_menu()) == ["(불러오지 못했어요)"], labels(tasks_menu()))
    gate.clear()
    raw["text"] = json.dumps(TASKS, ensure_ascii=False)
    reads_before[0] = len(reads)
    m.refresh_tasks()
    m.refresh_tasks()
    gate.set()


reads_before = [0]


@step
def s8():
    check("읽는 중에 또 부르면 한 번만 읽는다", len(reads) == reads_before[0] + 1, (reads_before[0], len(reads)))
    check("다시 읽으면 목록이 돌아온다", len(labels(tasks_menu())) == 5, labels(tasks_menu()))


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
