# 날씨 실패 대응(11-16): 조회 실패 이유를 mascot_error.log 에 남기고(좌표는 빼고, 최근 50줄), 메뉴로 물었다가 실패하면 한 번 더 해 본다
import importlib.machinery
import importlib.util
import json
import os
import sys
import tempfile
import time
import urllib.error

loader = importlib.machinery.SourceFileLoader("claude_mascot", sys.argv[1] if len(sys.argv) > 1 else os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "mascot", "claude_mascot.pyw"))
spec = importlib.util.spec_from_loader("claude_mascot", loader)
cm = importlib.util.module_from_spec(spec)
loader.exec_module(cm)
cm.IMAGE_DIR = os.environ.get("MASCOT_IMAGES", cm.IMAGE_DIR)  # 변형 사본(RED 확인)은 리포 밖에 있어 그림 폴더를 따로 준다
tmp = tempfile.mkdtemp()
cm.DATA_DIR, cm.USAGE_GLOB, cm.CONFIG_PATH = tmp, os.path.join(tmp, "usage-*.json"), os.path.join(tmp, "mascot.json")
cm.CHARACTERS_DIR = os.path.join(tmp, "characters")
cm.INBOX_DIR = os.path.join(tmp, "inbox")
cm.NOTIFY_PATH = os.path.join(tmp, "notify.json")
cm.SESSIONS_GLOB = os.path.join(tmp, "sessions", "*.json")
cm.ERROR_LOG = os.path.join(tmp, "mascot_error.log")
cm.WEATHER_MANUAL_RETRY_S = 0
cm.Mascot.fetch_status = lambda self: None
cm.Mascot.greet_on_start = lambda self: None
cm.WALK_EVERY_MS = (600_000, 600_000)
cm.MOOD_POLL_MS = 10 ** 7
cm.app_version = lambda: None
SEOUL = {"label": "서울특별시, 대한민국", "lat": 37.566, "lon": 126.9784}
SUNNY = {"code": 0, "high": 13.4, "low": 5.6, "rain": 10, "now": 12.2}
with open(cm.CONFIG_PATH, "w", encoding="utf-8") as f:
    json.dump({"x": 1000, "birthdays": {}, "weather_place": SEOUL}, f)
results = []


def check(name, ok, info=""):
    results.append(ok)
    print("PASS" if ok else "FAIL", name, info, flush=True)


def log_lines():
    try:
        with open(cm.ERROR_LOG, encoding="utf-8") as f:
            return f.read().splitlines()
    except OSError:
        return []


# 조회 실패 기록
real_urlopen = cm.urllib.request.urlopen


def refuse(url, timeout=None):
    raise urllib.error.URLError("timed out")


cm.urllib.request.urlopen = refuse
check("조회 실패는 None", cm.get_json(cm.WEATHER_URL, {"latitude": 37.566, "longitude": 126.9784}) is None)
line = (log_lines() or [""])[-1]
check("실패 이유를 기록: 주소·오류 종류·메시지", cm.WEATHER_URL in line and "URLError" in line and "timed out" in line, line)
check("주소에서 좌표(쿼리)는 뺀다", "37.566" not in line and "?" not in line, line)
for _ in range(60):
    cm.get_json(cm.WEATHER_URL, {})
check("최근 50줄만 남긴다", len(log_lines()) == 50, len(log_lines()))
cm.urllib.request.urlopen = real_urlopen
real_get = cm.get_json
cm.get_json = lambda url, params: {"daily": {}}
check("응답 모양이 다르면 None", cm.fetch_weather(SEOUL) is None)
line = (log_lines() or [""])[-1]
check("응답 모양이 달라진 것도 기록", "응답 모양" in line and "KeyError" in line, line)
cm.get_json = real_get

# 메뉴로 물었을 때 한 번 더
answers, fetches, spoken = [], [], []
cm.fetch_weather = lambda place: (fetches.append(1), answers.pop(0))[1]
real_speak = cm.Mascot.speak


def speak(self, headline=None, body=None, duration=None, link=None, pose=None):
    spoken.append("\n".join(filter(None, (headline, body))))
    real_speak(self, headline, body, duration, link, pose)


cm.Mascot.speak = speak
m = cm.Mascot()


# 가져오기는 작업 스레드가 root.after 로 돌려준다: mainloop 가 돌아야 해서 단계마다 1초 간격으로 진행한다
def ask(manual, replies):
    answers[:], fetches[:], spoken[:] = replies, [], []
    if m.bubble is not None:
        m.stop_talking(m.bubble)
    m.weather_retry = 0
    m.request_weather(manual)


steps = [
    lambda: ask(True, [None, SUNNY]),
    lambda: check("메뉴: 처음 실패해도 다시 해서 성공하면 날씨를 말한다", len(fetches) == 2 and spoken[-1:] and spoken[-1].startswith("서울특별시 오늘 맑음"), (len(fetches), spoken)),
    lambda: ask(True, [None, None]),
    lambda: check("메뉴: 두 번 다 실패하면 그때 실패를 말한다", len(fetches) == 2 and spoken == ["날씨를 가져오지 못했어요"], (len(fetches), spoken)),
    lambda: ask(True, [SUNNY]),
    lambda: check("메뉴: 처음에 되면 한 번만 묻는다", len(fetches) == 1, len(fetches)),
    lambda: ask(False, [None]),
    lambda: check("아침 날씨는 바로 다시 묻지 않는다(10분 뒤)", len(fetches) == 1 and m.weather_retry > time.monotonic(), len(fetches)),
]


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
    m.root.after(1000, run, i + 1)


m.root.after(1000, run)
m.root.mainloop()
