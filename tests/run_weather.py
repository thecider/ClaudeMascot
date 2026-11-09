# 날씨(11-02, A안): 「날씨 > 위치 정하기」에서 이름으로 찾아 후보 중 고른다. 하루 한 번 5시 이후 처음 켜질 때·한가할 때 인사 + 오늘 날씨
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
cm.IMAGE_DIR = os.environ.get("MASCOT_IMAGES", cm.IMAGE_DIR)  # 변형 사본(RED 확인)은 리포 밖에 있어 그림 폴더를 따로 준다
tmp = tempfile.mkdtemp()
cm.DATA_DIR, cm.USAGE_GLOB, cm.CONFIG_PATH = tmp, os.path.join(tmp, "usage-*.json"), os.path.join(tmp, "mascot.json")
cm.CHARACTERS_DIR = os.path.join(tmp, "characters")
cm.INBOX_DIR = os.path.join(tmp, "inbox")
cm.NOTIFY_PATH = os.path.join(tmp, "notify.json")
cm.SESSIONS_GLOB = os.path.join(tmp, "sessions", "*.json")
cm.Mascot.fetch_status = lambda self: None
cm.WALK_EVERY_MS = (600_000, 600_000)
cm.MOOD_POLL_MS = 10 ** 7
cm.GAME_TICK_MS = 10 ** 7
cm.app_version = lambda: None
with open(cm.CONFIG_PATH, "w", encoding="utf-8") as f:
    json.dump({"x": 1000, "birthdays": {}}, f)

now = [datetime.datetime(2026, 11, 3, 8, 0)]
cm.local_now = lambda: now[0]
SUNNY = {"code": 0, "high": 13.4, "low": 5.6, "rain": 10, "now": 12.2}
RAINY = {"code": 63, "high": 15, "low": 9, "rain": 80, "now": 11}
weather = [SUNNY]
fetches = []
cm.fetch_weather = lambda place: (fetches.append(place["label"]), weather[0])[1]
SEONGNAM = {"label": "성남시, 경기도, 대한민국", "lat": 37.43861, "lon": 127.13778}
NORTH = {"label": "성남, 황해남도, 조선민주주의인민공화국", "lat": 37.96167, "lon": 126.2674}
real_search = cm.search_places  # 진짜 것은 cm.get_json 을 부르므로 그것만 바꿔 시험한다
cm.search_places = lambda name: [NORTH, SEONGNAM] if name == "성남" else []
spoken = []
real_speak = cm.Mascot.speak


def speak(self, headline=None, body=None, duration=None, link=None, pose=None):
    spoken.append("\n".join(filter(None, (headline, body))))
    real_speak(self, headline, body, duration, link, pose)


cm.Mascot.speak = speak
real_greet = cm.Mascot.greet_on_start
cm.Mascot.greet_on_start = lambda self: None
m = cm.Mascot()
cm.Mascot.greet_on_start = real_greet
results = []


def check(name, ok, info=""):
    results.append(ok)
    print("PASS" if ok else "FAIL", name, info, flush=True)


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
    labels = [m.menu.entrycget(i, "label") for i in range(m.menu.index("end") + 1) if m.menu.type(i) != "separator"]
    sub = [m.weather_menu.entrycget(i, "label") for i in range(m.weather_menu.index("end") + 1)]
    check("메뉴에 「날씨 > 오늘 날씨·위치 정하기…」", "날씨" in labels and sub == ["오늘 날씨", "위치 정하기…"], (labels, sub))
    text = cm.weather_speech(SEONGNAM, SUNNY)
    check("말: 이름·날씨·최저~최고·지금", text == "성남시 오늘 맑음, 6~13°C (지금 12°C)", text)
    check("비 확률 낮으면 우산 말 없음", "우산" not in text)
    check("비 확률 높으면 우산", "비 올 확률 80% — 우산 챙기세요!" in cm.weather_speech(SEONGNAM, RAINY))
    check("눈이면 「눈 올 확률」", "눈 올 확률" in cm.weather_speech(SEONGNAM, {**RAINY, "code": 73}))
    pose = cm.weather_pose
    check("그림: 비 확률 높으면 우산", pose(RAINY) == "weather_rain")
    check("그림: 눈이면 눈사람(한파여도 눈이 먼저)", pose({**RAINY, "code": 73, "feels_low": -15}) == "weather_snow")
    check("그림: 체감 -10 이하면 귀마개", pose({**SUNNY, "feels_low": -10, "feels_high": 0}) == "weather_cold")
    check("그림: 체감 33 이상이면 선풍기", pose({**SUNNY, "feels_low": 25, "feels_high": 33}) == "weather_hot")
    check("그림: 보통 날은 없음(talk)", pose({**SUNNY, "feels_low": -9.9, "feels_high": 32.9}) is None and pose(SUNNY) is None)
    check("날씨 그림이 없는 캐릭터는 talk 로", all(cm.FALLBACK_IMAGES.get(n) == "talk" for n in cm.WEATHER_FRAMES) and all(n in m.images for n in cm.WEATHER_FRAMES))
    real_get = cm.get_json
    cm.get_json = lambda url, params: {"results": [{"name": "성남시", "admin1": "경기도", "admin2": "성남시", "country": "대한민국", "latitude": 37.4, "longitude": 127.1},
                                                    {"name": "깨짐"}]}
    places = real_search("성남")
    check("후보 이름: 이름과 같은 칸은 빼고 도·나라를 붙인다, 좌표 없는 건 뺀다", places == [{"label": "성남시, 경기도, 대한민국", "lat": 37.4, "lon": 127.1}], places)
    cm.get_json = lambda url, params: None
    check("찾기 실패는 None", real_search("성남") is None)
    cm.get_json = real_get
    m.greet_on_start()


@step
def s2():
    check("위치를 안 정했으면 날씨를 안 가져오고 인사만", fetches == [] and spoken[-1:] == ["좋은 아침이에요!"], (fetches, spoken[-1:]))
    quiet()
    m.tell_weather()
    check("위치 없이 「오늘 날씨」 = 위치 정하기 창", m.picker is not None)
    m.picker.entry.insert(0, "서울")
    m.picker.search()


@step
def s3():
    check("결과가 없으면 시·도·영어로 찾으라는 안내", m.picker.listbox.size() == 0 and "서울특별시" in m.picker.message.cget("text"), m.picker.message.cget("text"))
    m.picker.entry.delete(0, "end")
    m.picker.entry.insert(0, "성남")
    m.picker.search()


@step
def s4():
    items = list(m.picker.listbox.get(0, "end"))
    check("후보를 다 보여 준다", items == [NORTH["label"], SEONGNAM["label"]], items)
    m.picker.listbox.selection_clear(0, "end")
    m.picker.listbox.selection_set(1)
    m.picker.pick()


@step
def s5():
    check("고른 곳을 저장", config().get("weather_place") == SEONGNAM and m.picker is None, config().get("weather_place"))
    check("정하면 바로 그곳 날씨를 말한다", spoken[-1].startswith("성남시 오늘 맑음"), spoken[-1:])
    check("위치를 정한 것만으로는 오늘 아침 몫을 쓰지 않는다", "weather_day" not in config())
    quiet()
    m.greeted.clear()
    m.greet_on_start()


@step
def s6():
    check("아침 첫 인사에 날씨를 붙인다", spoken[-1] == "좋은 아침이에요!\n성남시 오늘 맑음, 6~13°C (지금 12°C)", spoken[-1:])
    check("보통 날은 talk 그림으로 말한다", m.shown == "talk", m.shown)
    check("오늘 말한 것을 기억", config().get("weather_day") == "2026-11-03")
    check("최근 알림에 날씨", m.history and m.history[0][0].startswith("08:00 날씨 — 성남시"), m.history[:1])
    quiet()
    check("같은 날 두 번 안 한다", m.daily_weather() is False)
    now[0] = datetime.datetime(2026, 11, 4, 4, 30)
    check("5시 전에는 안 한다", m.daily_weather() is False)
    now[0] = datetime.datetime(2026, 11, 4, 7, 0)
    m.hide_window()
    check("숨겨 두면 미룬다", m.daily_weather() is False)
    m.show_window()
    m.play_game()
    check("게임 중이면 미룬다", m.daily_weather() is False)
    m.game.close()
    quiet()
    weather[0] = None
    m.greeted.clear()
    m.greet_on_start()


@step
def s7():
    check("가져오지 못하면 인사만", spoken[-1] == "좋은 아침이에요!", spoken[-1:])
    check("못 가져온 날은 오늘 몫으로 치지 않는다", config().get("weather_day") == "2026-11-03")
    n = len(fetches)
    quiet()
    check("못 가져오면 바로 또 묻지 않는다(10분 뒤)", m.daily_weather() is False and len(fetches) == n)
    m.weather_retry = 0
    m.tell_weather()


@step
def s8():
    check("메뉴로 물었는데 실패하면 그렇다고 말한다", spoken[-1] == "날씨를 가져오지 못했어요", spoken[-1:])
    quiet()
    weather[0] = RAINY
    m.daily_weather()
    m.speak(body="장애 알림")  # 가져오는 사이 다른 말풍선이 떴다


@step
def s9():
    check("그 사이 말풍선이 떴으면 덮지 않고 최근 알림에만", spoken[-1] == "장애 알림" and m.history[0][1].startswith("성남시 오늘 비"), (spoken[-1:], m.history[:1]))
    check("그래도 오늘 몫은 끝", config().get("weather_day") == "2026-11-04")
    quiet()
    now[0] = datetime.datetime(2026, 11, 5, 9, 0)
    m.poll_mood()


@step
def s10():
    check("켜 둔 채 날이 바뀌면 한가할 때 아침 날씨", "우산 챙기세요" in spoken[-1] and config().get("weather_day") == "2026-11-05", spoken[-1:])
    check("비 오는 날은 우산 그림으로 말한다", m.shown == "weather_rain", m.shown)
    quiet()
    check("말이 끝나면 우산 그림도 내린다", m.shown != "weather_rain", m.shown)
    m.tell_weather()


@step
def s11():
    check("「오늘 날씨」는 몇 번이고 다시 말한다", spoken[-1].startswith("성남시 오늘 비"), spoken[-1:])


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
