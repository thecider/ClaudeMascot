# Claude Mascot: 바탕화면에 SD 캐릭터를 띄워 Claude 상태와 사용량에 반응한다 (Windows 전용).
# 데이터: ~/.claude/claude-status/usage-<계정>.json (Claude Code 플러그인 usage-status-bridge 가 쓴다, 없으면 상태만), status.claude.com 공개 API.
# 이미지(images/*.png, 투명 배경)는 Windows 레이어드 창으로 픽셀 단위 투명도를 살려 그린다(가장자리가 부드러운 그림이라 색 빼기 방식은 계단이 진다).
# 조작: 클릭 = 사용량 말하기(말풍선), 끌기 = 이동(위치 기억), 오른쪽 클릭 = 메뉴(사용량 말하기/장애 상세 열기/걷기/숨기기/완전히 종료).
# 걷기: 「걷기」가 체크돼 있으면(기본) 한가할 때 가끔 지금 높이에서 좌우로 몇 걸음 걷는다(walk_1~4, 왼쪽은 좌우 반전). 누르면 멈춘다.
# 트레이 아이콘(pystray): 클릭 = 보이기, 오른쪽 클릭 = 보이기/숨기기/캐릭터/Windows 시작 시 실행/완전히 종료. 완전히 끄는 길은 「완전히 종료」뿐이다.
# 이미지: 장애 sick > 점검 maintenance > 사용량 90% 이상 tired > 평상시 idle_* 무작위(30초마다). 말하는 동안은 talk(단, 장애·점검·피곤 이미지는 말하는 중에도 유지).
# 장애 알림: 장애 발생·새 사고·복구, 점검 시작·종료 때 클릭 없이 스스로 말풍선으로 알린다.
# 인터랙션: 머리 위에서 문지르기 = 쓰다듬기(pet, 아플 때는 sick_pet 또는 얼음주머니 애니메이션), 10분 안 건드리면 잠들기(sleep),
#   켜질 때·시간대 첫 클릭 = 인사, mascot.json 의 birthdays 에 오늘(MM-DD)이 있으면 생일 축하(birthday), 「완전히 종료」 = 잘자요(goodnight) 뒤 종료.
# 캐릭터: ~/.claude/claude-status/characters/<이름>/ 에 같은 이름의 PNG 를 넣고 트레이 「캐릭터」에서 고른다. 빠진 그림은 기본 그림으로 채운다.
# 장애 중 말풍선: 사고 제목·최근 공지(상태 시각 — 본문 앞부분)·장애 서비스 + 사용량, 평소보다 오래(OUTAGE_TALK_MS). 오른쪽 클릭 「장애 상세 열기」 = 브라우저로 사고 페이지.
import ctypes
import ctypes.wintypes as wt
import datetime
import glob
import json
import os
import random
import sys
import threading
import time
import tkinter as tk
import urllib.request
import webbrowser
import winreg

import pystray
from PIL import Image, ImageChops, ImageOps

# exe(PyInstaller)로 묶이면 그림은 실행 때 풀리는 임시 폴더(sys._MEIPASS)에 있다
IMAGE_DIR = os.path.join(getattr(sys, "_MEIPASS", os.path.dirname(os.path.abspath(__file__))), "images")
DATA_DIR = os.path.join(os.path.expanduser("~"), ".claude", "claude-status")
USAGE_GLOB = os.path.join(DATA_DIR, "usage-*.json")
CONFIG_PATH = os.path.join(DATA_DIR, "mascot.json")
CHARACTERS_DIR = os.path.join(DATA_DIR, "characters")  # 캐릭터마다 하위 폴더 하나, 안에 IMAGE_NAMES 와 같은 이름의 PNG
RUN_KEY = r"Software\Microsoft\Windows\CurrentVersion\Run"  # 「Windows 시작 시 실행」: 현재 사용자 시작 프로그램 목록
RUN_NAME = "ClaudeMascot"
STATUS_URL = "https://status.claude.com/api/v2/summary.json"
STATUS_PAGE = "https://status.claude.com"

HEIGHT = 160
IDLE_MS = 30_000
MOOD_POLL_MS = 20_000
STATUS_POLL_MS = 60_000
TALK_MS = 6_000
OUTAGE_TALK_MS = 12_000  # 장애·점검 중에는 읽을 내용이 많다
TIRED_PERCENT = 90
STALE_MINUTES = 30
CLICK_SLOP = 4  # 이 픽셀 안에서 떼면 끌기가 아니라 클릭으로 본다
SLEEP_MINUTES = 10  # 이만큼 안 건드리면 잠든다 (장애·점검·피곤일 때는 안 잔다)
PET_MS = 3_000
PET_HEAD = 0.45  # 위에서부터 이 비율까지가 머리: 여기서 문질러야 쓰다듬기
PET_STROKES = 3  # 좌우 방향을 이만큼 바꾸면 쓰다듬기
PET_WINDOW = 1.5  # 초. 이 안에 방향 전환이 모여야 한다
PET_LINES = ("헤헤, 기분 좋아요", "에헤헤~", "더 쓰다듬어 주세요!")
GOODNIGHT_MS = 1_800
WALK_FRAMES = ("walk_1", "walk_2", "walk_3", "walk_4")  # 오른쪽으로 걷는 그림. 왼쪽은 좌우 반전(이름 끝 _left)
WALK_EVERY_MS = (20_000, 60_000)  # 이 사이 무작위 간격으로 걸을지 본다
WALK_DISTANCE = (60, 200)  # 한 번에 걷는 거리(px) 범위
WALK_TICK_MS = 180  # 이 간격마다 한 프레임·WALK_STEP px (그림 보폭에 맞춘 값: 작으면 발이 미끄러져 보인다)
WALK_STEP = 10
IMAGE_NAMES = ("idle_1", "idle_2", "idle_3", "idle_4", "talk", "sick", "maintenance", "tired", "pet", "sleep", "birthday", "goodnight",
               "sick_pet", "sick_ice_1", "sick_ice_2", "sick_ice_3", "sick_ice_4") + WALK_FRAMES
# 그림이 없으면 같은 캐릭터의 이 그림으로 (사용자 캐릭터에 다른 캐릭터가 섞여 보이지 않게, 걷는 그림이 없으면 idle_1 로 미끄러지듯)
FALLBACK_IMAGES = {"sick_pet": "sick", "sick_ice_1": "sick", "sick_ice_2": "sick", "sick_ice_3": "sick", "sick_ice_4": "sick",
                   **{name: "idle_1" for name in WALK_FRAMES}}
# 아플 때 쓰다듬기: 보통은 sick_pet + 한마디, ICE_CHANCE 확률로 얼음주머니 갈아주기 애니메이션(그림, 보여 줄 ms)
SICK_PET_LINES = ("아프지만… 기분 좋아요", "헤헤… 조금 나아졌어요")
ICE_CHANCE = 1 / 3
ICE_FRAMES = (("sick_ice_1", 600), ("sick_ice_2", 700), ("sick_ice_3", 700), ("sick_ice_4", 1500))
ICE_LINE = "시원해요… 고마워요!"
DEFAULT_CHARACTER = "기본"  # 트레이 메뉴의 기본 캐릭터 이름. 설정에는 "" 로 저장한다
# 시간대 인사: (시작 시, 끝 시, 문구). 14~18시는 인사 없음
GREETINGS = ((5, 11, "좋은 아침이에요!"), (11, 14, "점심 맛있게 드세요"), (18, 24, "오늘도 수고했어요"))

user32 = ctypes.windll.user32
gdi32 = ctypes.windll.gdi32
user32.GetParent.argtypes = [wt.HWND]
user32.GetParent.restype = wt.HWND
user32.GetDC.argtypes = [wt.HWND]
user32.GetDC.restype = wt.HDC
user32.ReleaseDC.argtypes = [wt.HWND, wt.HDC]
user32.GetWindowLongW.argtypes = [wt.HWND, ctypes.c_int]
user32.SetWindowLongW.argtypes = [wt.HWND, ctypes.c_int, wt.LONG]
gdi32.CreateCompatibleDC.argtypes = [wt.HDC]
gdi32.CreateCompatibleDC.restype = wt.HDC
gdi32.CreateDIBSection.argtypes = [wt.HDC, ctypes.c_void_p, wt.UINT, ctypes.POINTER(ctypes.c_void_p), wt.HANDLE, wt.DWORD]
gdi32.CreateDIBSection.restype = wt.HBITMAP
gdi32.SelectObject.argtypes = [wt.HDC, wt.HGDIOBJ]
gdi32.SelectObject.restype = wt.HGDIOBJ
gdi32.DeleteObject.argtypes = [wt.HGDIOBJ]
gdi32.DeleteDC.argtypes = [wt.HDC]


class BITMAPINFOHEADER(ctypes.Structure):
    _fields_ = [("biSize", wt.DWORD), ("biWidth", wt.LONG), ("biHeight", wt.LONG), ("biPlanes", wt.WORD),
                ("biBitCount", wt.WORD), ("biCompression", wt.DWORD), ("biSizeImage", wt.DWORD),
                ("biXPelsPerMeter", wt.LONG), ("biYPelsPerMeter", wt.LONG), ("biClrUsed", wt.DWORD), ("biClrImportant", wt.DWORD)]


class BLENDFUNCTION(ctypes.Structure):
    _fields_ = [("BlendOp", ctypes.c_ubyte), ("BlendFlags", ctypes.c_ubyte), ("SourceConstantAlpha", ctypes.c_ubyte), ("AlphaFormat", ctypes.c_ubyte)]


user32.UpdateLayeredWindow.argtypes = [wt.HWND, wt.HDC, ctypes.POINTER(wt.POINT), ctypes.POINTER(wt.SIZE), wt.HDC,
                                       ctypes.POINTER(wt.POINT), wt.COLORREF, ctypes.POINTER(BLENDFUNCTION), wt.DWORD]
GWL_EXSTYLE = -20
WS_EX_LAYERED = 0x80000
ULW_ALPHA = 2


def paint_layered(hwnd, image, x, y):
    # UpdateLayeredWindow 는 알파를 미리 곱한(premultiplied) BGRA 를 받는다
    r, g, b, a = image.split()
    r, g, b = (ImageChops.multiply(c, a) for c in (r, g, b))
    data = Image.merge("RGBA", (b, g, r, a)).tobytes()
    width, height = image.size
    screen = user32.GetDC(None)
    memory = gdi32.CreateCompatibleDC(screen)
    header = BITMAPINFOHEADER(ctypes.sizeof(BITMAPINFOHEADER), width, -height, 1, 32, 0, 0, 0, 0, 0, 0)  # 음수 높이 = 위에서 아래로
    bits = ctypes.c_void_p()
    bitmap = gdi32.CreateDIBSection(memory, ctypes.byref(header), 0, ctypes.byref(bits), None, 0)
    ctypes.memmove(bits, data, len(data))
    old = gdi32.SelectObject(memory, bitmap)
    user32.UpdateLayeredWindow(hwnd, screen, ctypes.byref(wt.POINT(x, y)), ctypes.byref(wt.SIZE(width, height)), memory,
                               ctypes.byref(wt.POINT(0, 0)), 0, ctypes.byref(BLENDFUNCTION(0, 0, 255, 1)), ULW_ALPHA)
    gdi32.SelectObject(memory, old)
    gdi32.DeleteObject(bitmap)
    gdi32.DeleteDC(memory)
    user32.ReleaseDC(None, screen)


def open_image(name, character=""):
    # 고른 캐릭터 폴더에 그 그림(없으면 대신할 그림)이 있고 열리면 그것, 아니면 기본 그림. 일부만 바꾼 캐릭터도 쓸 수 있게 한 장씩 채운다
    folders = ([os.path.join(CHARACTERS_DIR, character)] if character else []) + [IMAGE_DIR]
    for folder in folders:
        for candidate in filter(None, (name, FALLBACK_IMAGES.get(name))):
            try:
                return Image.open(os.path.join(folder, f"{candidate}.png")).convert("RGBA")
            except (OSError, ValueError):
                pass
    raise FileNotFoundError(name)


def load_image(name, character=""):
    image = open_image(name, character)
    return image.resize((round(image.width * HEIGHT / image.height), HEIGHT), Image.LANCZOS)


def load_images(character=""):
    images = {name: load_image(name, character) for name in IMAGE_NAMES}
    images.update({f"{name}_left": ImageOps.mirror(images[name]) for name in WALK_FRAMES})
    return images


def list_characters():
    try:
        return sorted(n for n in os.listdir(CHARACTERS_DIR) if os.path.isdir(os.path.join(CHARACTERS_DIR, n)) and n != DEFAULT_CHARACTER)
    except OSError:
        return []


def tray_image(character=""):
    # 전신은 트레이 크기에서 안 보인다: 그림이 있는 영역의 위쪽(머리)을 정사각형으로 잘라 쓴다.
    image = open_image("idle_1", character)
    left, top, right, _ = image.getchannel("A").point(lambda a: 255 if a > 128 else 0).getbbox()
    side = int((right - left) * 0.95)
    center = (left + right) // 2
    return image.crop((center - side // 2, top, center + side // 2, top + side)).resize((64, 64), Image.LANCZOS)


def launch_command():
    # exe 로 묶였으면 exe 자신, 아니면 콘솔 없는 pythonw 로 이 스크립트
    if getattr(sys, "frozen", False):
        return f'"{sys.executable}"'
    pythonw = os.path.join(os.path.dirname(sys.executable), "pythonw.exe")
    return f'"{pythonw}" "{os.path.abspath(__file__)}"'


def autostart_enabled():
    try:
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, RUN_KEY) as key:
            winreg.QueryValueEx(key, RUN_NAME)
        return True
    except OSError:
        return False


def set_autostart(enabled):
    with winreg.CreateKey(winreg.HKEY_CURRENT_USER, RUN_KEY) as key:
        if enabled:
            winreg.SetValueEx(key, RUN_NAME, 0, winreg.REG_SZ, launch_command())
        else:
            try:
                winreg.DeleteValue(key, RUN_NAME)
            except OSError:
                pass


def local_now():
    # 시간대 인사·생일 판정용 현재 시각 (테스트가 바꿔 끼운다)
    return datetime.datetime.now()


def read_config():
    # 파일이 없으면 {}, 있는데 JSON 이 깨졌으면 None. 손으로 생일을 넣다 깨진 파일을 저장으로 덮어 지우지 않으려고 둘을 구분한다
    if not os.path.exists(CONFIG_PATH):
        return {}
    try:
        with open(CONFIG_PATH, encoding="utf-8-sig") as f:
            return json.load(f)
    except (OSError, ValueError):
        return None


def load_json(path):
    try:
        with open(path, encoding="utf-8-sig") as f:
            return json.load(f)
    except (OSError, ValueError):
        return {}


def parse_time(text):
    try:
        return datetime.datetime.fromisoformat(text.replace("Z", "+00:00"))
    except (AttributeError, ValueError):
        return None


def load_accounts():
    # 오래된 기록부터
    accounts = [load_json(path) for path in glob.glob(USAGE_GLOB)]
    return sorted((a for a in accounts if a.get("windows")), key=lambda a: a.get("updatedAt", ""))


def effective_percent(window, now):
    # 초기화 시각이 지났으면 새 응답 전이라도 0 으로 본다
    resets_at = parse_time(window.get("resetsAt") or "")
    return 0 if resets_at and resets_at <= now else window.get("percent", 0)


def pick_mood(indicator, accounts, now):
    # 조회 실패(indicator None)는 장애로 보지 않는다
    if indicator in ("minor", "major", "critical"):
        return "sick"
    if indicator == "maintenance":
        return "maintenance"
    for usage in accounts:
        if any(effective_percent(w, now) >= TIRED_PERCENT for w in usage["windows"].values()):
            return "tired"
    return None


UPDATE_STATUS = {"investigating": "조사 중", "identified": "원인 파악", "monitoring": "모니터링", "resolved": "해결"}


def latest_update(incident):
    # 사고의 최근 공지(incident_updates 는 최신이 앞)를 「상태 시각」으로. 공지가 없으면 None
    updates = incident.get("incident_updates") or []
    created = parse_time(updates[0].get("created_at") or "") if updates else None
    if created is None:
        return None
    return f"{UPDATE_STATUS.get(updates[0].get('status'), updates[0].get('status'))} {created.astimezone():%H:%M}"


def incident_url(status):
    # 첫 사고의 상태 페이지, 사고가 없으면 상태 페이지 첫 화면
    incidents = (status or {}).get("incidents") or []
    return (incidents[0].get("shortlink") if incidents else None) or STATUS_PAGE


def usage_speech(status, accounts, now):
    lines = []
    if status is not None and status["status"]["indicator"] != "none":
        lines.append(f"Claude 상태: {status['status']['description']}")
        for incident in status.get("incidents", [])[:2]:
            lines.append(f"! {incident['name']}")
            update = latest_update(incident)
            if update:
                body = incident["incident_updates"][0].get("body") or ""
                lines.append(f"  {update} — {body[:100]}" + ("…" if len(body) > 100 else ""))
        down = [c["name"] for c in status.get("components", []) if c.get("status") != "operational"]
        if down:
            lines.append("장애: " + ", ".join(down))
    for usage in accounts:
        updated = parse_time(usage.get("updatedAt", ""))
        is_stale = updated is None or (now - updated).total_seconds() > STALE_MINUTES * 60
        name = (usage.get("account") or "--").split("@")[0]
        parts = []
        for kind, label in (("five_hour", "5h"), ("seven_day", "주")):
            window = usage["windows"].get(kind)
            if window:
                parts.append(f"{label} {effective_percent(window, now):.0f}%")
        lines.append(f"{name}: " + " · ".join(parts) + (" (오래된 기록)" if is_stale else ""))
    if lines:
        return "\n".join(lines)
    # 사용량 기록이 없으면(브리지 미설치) 상태만 말한다
    return "Claude 상태를 확인하지 못했어요" if status is None else "Claude 정상이에요"


class Mascot:
    def __init__(self):
        config = read_config()
        # 고른 캐릭터 폴더가 지워졌으면 기본으로
        self.character = (config or {}).get("character") or ""
        if self.character not in list_characters():
            self.character = ""
        self.images = load_images(self.character)
        self.idle = "idle_1"
        self.talking = False
        self.status = None  # summary.json, 조회 실패 시 None
        self.shown = None
        self.press = None
        self.bubble = None
        self.menu_open = False
        self.state = "ok"  # 마지막으로 받은 서비스 상태: ok / maintenance / down (알림 판정용)
        self.seen_incidents = set()
        self.last_touch = time.monotonic()  # 마지막으로 클릭·끌기·쓰다듬기 한 때 (잠들기 판정)
        self.petting = False
        self.celebrating = False  # 생일 축하 말풍선 중: talk 대신 birthday 이미지
        self.ice_frame = None  # 얼음주머니 애니메이션 중 보여 줄 프레임
        self.stroke = None  # 쓰다듬기 판정: (마지막 x, 마지막 방향, 방향 전환 수, 시작 시각)
        self.greeted = set()  # 이미 한 인사: (날짜, 시간대 문구 또는 "birthday")
        self.closing = False
        self.tray_characters = []  # 트레이 메뉴를 만들 때 본 캐릭터 폴더 목록
        self.walking = None  # 걷는 중이면 [방향(1 오른쪽, -1 왼쪽), 남은 px, 프레임 번호]

        self.root = tk.Tk()
        self.root.overrideredirect(True)
        self.root.attributes("-topmost", True)
        width, height = self.images["idle_1"].size
        left, top, right, bottom = self.work_area()
        # 저장 위치가 모니터 구성 변경 등으로 작업 영역 밖이면 안으로 끌어온다
        self.x = max(left, min((config or {}).get("x", right - width - 16), right - width))
        self.y = max(top, min((config or {}).get("y", bottom - height), bottom - height))
        self.root.geometry(f"{width}x{height}+{self.x}+{self.y}")
        self.root.update()
        # tk 의 최상위 프레임 창을 레이어드 창으로 바꾼다: 이후 그림은 tk 가 아니라 UpdateLayeredWindow 가 그린다
        self.hwnd = user32.GetParent(self.root.winfo_id())
        user32.SetWindowLongW(self.hwnd, GWL_EXSTYLE, user32.GetWindowLongW(self.hwnd, GWL_EXSTYLE) | WS_EX_LAYERED)

        self.menu = tk.Menu(self.root, tearoff=0)
        self.menu.add_command(label="사용량 말하기", command=self.speak_clicked)
        self.menu.add_command(label="장애 상세 열기", command=lambda: webbrowser.open(incident_url(self.status)))
        self.walk_enabled = tk.BooleanVar(self.root, (config or {}).get("walk", True))
        self.menu.add_checkbutton(label="걷기", variable=self.walk_enabled, command=lambda: self.save_config(walk=self.walk_enabled.get()))
        self.menu.add_command(label="숨기기", command=self.hide_window)
        self.menu.add_separator()
        self.menu.add_command(label="완전히 종료", command=self.quit)

        # 트레이 메뉴 동작은 pystray 스레드에서 불리므로 after 로 Tk 스레드에 넘긴다
        self.tray = pystray.Icon("ClaudeMascot", tray_image(self.character), "Claude 마스코트", pystray.Menu(
            pystray.MenuItem("보이기", lambda: self.root.after(0, self.show_window), default=True),
            pystray.MenuItem("숨기기", lambda: self.root.after(0, self.hide_window)),
            pystray.MenuItem("캐릭터", pystray.Menu(self.character_items)),
            pystray.MenuItem("Windows 시작 시 실행", self.toggle_autostart, checked=lambda item: autostart_enabled()),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem("완전히 종료", lambda: self.root.after(0, self.quit)),
        ))
        threading.Thread(target=self.tray.run, daemon=True).start()
        self.root.bind("<ButtonPress-1>", self.on_press)
        self.root.bind("<B1-Motion>", self.on_drag)
        self.root.bind("<ButtonRelease-1>", self.on_release)
        self.root.bind("<Button-3>", self.popup_menu)
        self.root.bind("<Motion>", self.on_motion)
        # 생일 목록 자리를 만들어 둔다: 사용자가 mascot.json 에 「"이름": "MM-DD"」를 직접 넣는다
        if config is not None and "birthdays" not in config:
            self.save_config(birthdays={})

        self.show()
        self.rotate_idle()
        # 첫 poll_mood 는 타이머로: 바로 부르면 생일 축하가 시작 인사(1초 뒤)보다 먼저 끼어든다
        self.root.after(MOOD_POLL_MS, self.poll_mood)
        self.poll_status()
        self.keep_on_top()
        self.root.after(1000, self.greet_on_start)
        self.root.after(random.randint(*WALK_EVERY_MS), self.maybe_walk)

    def work_area(self):
        rect = wt.RECT()
        user32.SystemParametersInfoW(0x0030, 0, ctypes.byref(rect), 0)  # SPI_GETWORKAREA
        return rect.left, rect.top, rect.right, rect.bottom

    # 그리기
    def current(self):
        # 우선순위: 잘자요 > 아플 때 쓰다듬기(얼음주머니·sick_pet) > 장애·점검·피곤 > 걷기 > 쓰다듬기 > 생일 축하 말풍선 > 말하기 > 잠 > 생일 > 평상시
        # 장애·점검·피곤 이미지는 말하는 중에도 유지한다: 아픈 모습이 바로 보여야 직관적이다. talk 는 평상시에 말할 때만
        if self.closing:
            return "goodnight"
        mood = pick_mood(self.status["status"]["indicator"] if self.status else None, load_accounts(), datetime.datetime.now(datetime.timezone.utc))
        if mood == "sick" and self.petting:
            return self.ice_frame or "sick_pet"
        if mood:
            return mood
        if self.walking:
            direction, _, frame = self.walking
            return WALK_FRAMES[frame] + ("_left" if direction < 0 else "")
        if self.petting:
            return "pet"
        if self.celebrating:
            return "birthday"
        if self.talking:
            return "talk"
        if time.monotonic() - self.last_touch >= SLEEP_MINUTES * 60:
            return "sleep"
        return "birthday" if self.birthday_names() else self.idle

    # 설정·인사
    def save_config(self, **values):
        # 기존 설정(생일 목록 등)을 지우지 않게 읽어서 덮는다. 파일이 깨져 있으면 쓰지 않는다(고치려던 내용이 사라진다)
        config = read_config()
        if config is None:
            return
        config.update(values)
        os.makedirs(DATA_DIR, exist_ok=True)
        with open(CONFIG_PATH, "w", encoding="utf-8") as f:
            json.dump(config, f, ensure_ascii=False, indent=1)

    def birthday_names(self):
        today = f"{local_now():%m-%d}"
        return [name for name, day in ((read_config() or {}).get("birthdays") or {}).items() if day == today]

    def take_greeting(self):
        # 지금 시간대에서 처음이면 시간대 인사. 한 번 한 인사는 다시 안 한다
        now = local_now()
        for start, end, text in GREETINGS:
            if start <= now.hour < end and (now.date(), text) not in self.greeted:
                self.greeted.add((now.date(), text))
                return text
        return None

    def greet_birthday(self):
        # 생일이 된 뒤 처음으로 한가할 때(말풍선 없음·보이는 중) birthday 이미지로 축하 한마디만 한다. 하루 한 번
        # 바쁘면 건너뛰고 다음 poll_mood 에서 다시 본다. 말했으면 True
        names = self.birthday_names()
        today = local_now().date()
        if not names or (today, "birthday") in self.greeted or self.bubble is not None or self.closing or self.root.state() == "withdrawn":
            return False
        self.greeted.add((today, "birthday"))
        self.speak(body="\n".join(f"{name} 생일 축하해요!" for name in names))
        self.celebrating = True
        self.show()
        return True

    def greet_on_start(self):
        # 이미 말풍선(장애 알림 등)이 떠 있으면 건너뛴다: take_greeting 을 부르지 않아야 그 인사가 첫 클릭으로 넘어간다
        # 생일이면 생일 축하가 먼저다. 시간대 인사는 첫 클릭으로 넘어간다
        if self.bubble is not None or self.greet_birthday():
            return
        greeting = self.take_greeting()
        if greeting:
            self.speak(greeting)

    def speak_clicked(self):
        self.last_touch = time.monotonic()
        self.speak(self.take_greeting())

    def show(self):
        name = self.current()
        if name != self.shown:
            self.shown = name
            paint_layered(self.hwnd, self.images[name], self.x, self.y)

    def rotate_idle(self):
        self.idle = random.choice([n for n in ("idle_1", "idle_2", "idle_3", "idle_4") if n != self.idle])
        self.show()
        self.root.after(IDLE_MS, self.rotate_idle)

    def poll_mood(self):
        self.show()
        # 캐릭터 폴더를 새로 넣으면 트레이 메뉴에 나오게 한다 (Windows 트레이 메뉴는 update_menu 때 다시 만들어진다)
        if self.tray_characters != list_characters():
            self.tray.update_menu()
        self.greet_birthday()
        self.root.after(MOOD_POLL_MS, self.poll_mood)

    def poll_status(self):
        threading.Thread(target=self.fetch_status, daemon=True).start()
        self.root.after(STATUS_POLL_MS, self.poll_status)

    def fetch_status(self):
        try:
            with urllib.request.urlopen(STATUS_URL, timeout=10) as response:
                status = json.loads(response.read().decode("utf-8"))
        except (OSError, ValueError):
            status = None
        self.root.after(0, self.set_status, status)

    def set_status(self, status):
        self.status = status
        self.show()
        # 조회 실패(None)는 알림 판정에 넣지 않는다: 망 순단마다 말하면 소음이다
        if status is not None:
            self.check_alert(status)

    def check_alert(self, status):
        # 시작 때는 ok 에서 출발하므로 이미 장애·점검이면 한 번 말한다
        indicator = status["status"]["indicator"]
        incidents = {incident["id"] for incident in status.get("incidents", [])}
        state = "ok" if indicator == "none" else "maintenance" if indicator == "maintenance" else "down"
        if state == "down" and self.state != "down":
            self.speak("Claude 장애가 났어요")
        elif state == "down" and incidents - self.seen_incidents:
            self.speak("새 사고가 생겼어요")
        elif state == "maintenance" and self.state != "maintenance":
            self.speak("Claude 점검 중이에요")
        elif state == "ok" and self.state == "down":
            self.speak("Claude 복구됐어요!")
        elif state == "ok" and self.state == "maintenance":
            self.speak("점검이 끝났어요")
        self.state = state
        self.seen_incidents = incidents

    # 캐릭터: 트레이 「캐릭터」 하위 메뉴에서 고른다
    def character_items(self):
        self.tray_characters = list_characters()
        items = [pystray.MenuItem(name, self.character_picked, radio=True,
                                  checked=lambda item: self.character == ("" if item.text == DEFAULT_CHARACTER else item.text))
                 for name in [DEFAULT_CHARACTER] + self.tray_characters]
        return items + [pystray.Menu.SEPARATOR, pystray.MenuItem("캐릭터 폴더 열기", lambda: self.root.after(0, self.open_characters_dir))]

    def character_picked(self, icon, item):
        # pystray 스레드에서 불린다
        name = "" if item.text == DEFAULT_CHARACTER else item.text
        self.root.after(0, self.set_character, name)

    def set_character(self, name):
        self.character = name
        self.images = load_images(name)
        self.tray.icon = tray_image(name)
        self.save_config(character=name)
        self.tray.update_menu()
        self.shown = None
        self.show()

    def toggle_autostart(self):
        # pystray 스레드에서 불린다. 레지스트리만 바꾸므로 Tk 스레드로 넘길 필요가 없다. 체크 표시는 메뉴를 다시 만들어야 바뀐다
        set_autostart(not autostart_enabled())
        self.tray.update_menu()

    def open_characters_dir(self):
        os.makedirs(CHARACTERS_DIR, exist_ok=True)
        os.startfile(CHARACTERS_DIR)

    def hide_window(self):
        self.stop_walk()
        if self.bubble is not None:
            self.stop_talking(self.bubble)
        self.root.withdraw()

    def show_window(self):
        self.root.deiconify()
        # 다시 보일 때 그림을 새로 넣는다: 숨김 동안 바뀐 상태도 반영된다
        self.shown = None
        self.show()
        self.root.lift()

    def quit(self):
        # 보이는 중이면 잘자요 인사를 하고 GOODNIGHT_MS 뒤에 끈다. 숨겨 둔 상태면 바로 끈다
        if self.closing:
            return
        self.closing = True
        if self.root.state() == "withdrawn":
            self.finish_quit()
            return
        self.speak(body="잘자요! 내일 또 봐요", duration=GOODNIGHT_MS)
        self.root.after(GOODNIGHT_MS, self.finish_quit)

    def finish_quit(self):
        # 트레이 아이콘을 먼저 내린다: 그냥 끝내면 아이콘이 트레이에 남는다
        self.tray.stop()
        self.root.destroy()

    def popup_menu(self, event):
        # tk_popup 은 메뉴가 닫힐 때까지 돌아오지 않지만 타이머는 계속 돈다: 그동안 keep_on_top 이 마스코트를 메뉴 위로 올리지 않게 막는다
        self.menu_open = True
        try:
            self.menu.tk_popup(event.x_root, event.y_root)
        finally:
            self.menu_open = False

    def keep_on_top(self):
        if self.root.state() != "withdrawn" and not self.menu_open:
            self.root.lift()
        self.root.after(2000, self.keep_on_top)

    # 말풍선
    def speak(self, headline=None, body=None, duration=None):
        # body 가 없으면 장애 내용 + 사용량을 말한다. headline 은 그 위 첫 줄
        self.stop_walk()
        self.ice_frame = None
        self.petting = self.celebrating = False  # 쓰다듬기·생일 한마디 중에 다른 말풍선이 뜨면 pet·birthday 가 남지 않게 푼다
        text = body or usage_speech(self.status, load_accounts(), datetime.datetime.now(datetime.timezone.utc))
        if headline:
            text = headline + "\n" + text
        if self.bubble is not None:
            self.bubble.destroy()
        bubble = self.bubble = tk.Toplevel(self.root)
        bubble.overrideredirect(True)
        bubble.attributes("-topmost", True)
        bubble.configure(bg="#3a3a3a", padx=1, pady=1)
        tk.Label(bubble, text=text, bg="white", fg="#222", font=("Segoe UI", 9), justify="left", wraplength=340, padx=10, pady=6).pack()
        bubble.bind("<ButtonRelease-1>", lambda e: self.stop_talking(bubble))
        bubble.update_idletasks()
        left, top, right, _ = self.work_area()
        width, height = bubble.winfo_reqwidth(), bubble.winfo_reqheight()
        x = max(left, min(self.x + (self.images["talk"].width - width) // 2, right - width))
        y = self.y - height - 4
        if y < top:
            y = self.y + HEIGHT + 4
        bubble.geometry(f"+{x}+{y}")
        self.talking = True
        self.show()
        # 타이머는 root 에 건다: 말풍선에 걸면 클릭으로 먼저 닫을 때 destroy 가 콜백까지 지워 talk 에 멈춘다
        outage = self.status is not None and self.status["status"]["indicator"] != "none"
        self.root.after(duration or (OUTAGE_TALK_MS if outage else TALK_MS), self.stop_talking, bubble)

    def stop_talking(self, bubble):
        bubble.destroy()
        if bubble is self.bubble:
            self.bubble = None
            self.talking = False
            self.petting = self.celebrating = False
            self.ice_frame = None
            self.show()

    # 쓰다듬기: 버튼을 안 누른 채 머리 위에서 좌우로 문지르면
    def on_motion(self, event):
        if self.petting or self.closing or event.y > HEIGHT * PET_HEAD:
            self.stroke = None
            return
        now = time.monotonic()
        if self.stroke is None or now - self.stroke[3] > PET_WINDOW:
            self.stroke = (event.x, 0, 0, now)
            return
        last_x, last_direction, turns, started = self.stroke
        if abs(event.x - last_x) < 3:
            return
        direction = 1 if event.x > last_x else -1
        if last_direction and direction != last_direction:
            turns += 1
        self.stroke = (event.x, direction, turns, started)
        if turns >= PET_STROKES:
            self.stroke = None
            self.last_touch = now
            sick = self.current() == "sick"
            if sick and random.random() < ICE_CHANCE:
                self.speak(body=ICE_LINE, duration=sum(ms for _, ms in ICE_FRAMES))
                self.petting = True
                self.play_ice(self.bubble, 0)
                return
            self.speak(body=random.choice(SICK_PET_LINES if sick else PET_LINES), duration=PET_MS)
            self.petting = True
            self.show()

    def play_ice(self, bubble, index):
        # 얼음주머니 프레임을 차례로. 그 사이 말풍선이 바뀌거나 닫혔으면(bubble 이 달라짐) 멈춘다
        if bubble is not self.bubble or index == len(ICE_FRAMES):
            return
        name, ms = ICE_FRAMES[index]
        self.ice_frame = name
        self.show()
        self.root.after(ms, self.play_ice, bubble, index + 1)

    # 걷기: 한가할 때(평상시 그림, 말풍선·메뉴·누르기 없음, 보이는 중)만 걷기 시작하고, 걷는 중 그런 일이 생기면 멈춘다
    def maybe_walk(self):
        self.start_walk()
        self.root.after(random.randint(*WALK_EVERY_MS), self.maybe_walk)

    def can_walk(self):
        return (self.walk_enabled.get() and not self.closing and self.bubble is None and self.press is None
                and not self.menu_open and self.root.state() != "withdrawn")

    def start_walk(self):
        if self.walking or not self.can_walk() or self.current() != self.idle:
            return
        # 작업 영역 끝에 붙어 있으면 반대로, 아니면 무작위 방향. 걷다 끝에 닿으면 돌아서서 남은 거리를 마저 걷는다(walk_tick)
        direction = random.choice([d for d in (1, -1) if self.walk_room(d) >= WALK_STEP] or [1])
        self.walking = [direction, random.randint(*WALK_DISTANCE), 0]
        self.show()
        self.root.after(WALK_TICK_MS, self.walk_tick, self.walking)

    def walk_tick(self, walking):
        if walking is not self.walking:  # 그 사이 멈췄다(다시 걷기 시작했으면 그 걸음의 타이머가 따로 돈다)
            return
        direction, remaining, frame = walking
        if remaining <= 0 or not self.can_walk():
            self.stop_walk()
            return
        if self.walk_room(direction) <= 0:  # 모서리: 돌아선다
            direction = walking[0] = -direction
        step = min(WALK_STEP, remaining, self.walk_room(direction))
        if step <= 0:  # 양쪽 다 막혔다(작업 영역이 캐릭터보다 좁다)
            self.stop_walk()
            return
        self.x += direction * step
        walking[1:] = [remaining - step, (frame + 1) % len(WALK_FRAMES)]
        self.root.geometry(f"+{self.x}+{self.y}")
        self.shown = None  # 같은 그림이어도 위치가 바뀌었으니 다시 그린다
        self.show()
        if not self.shown.startswith("walk"):  # 장애·점검·피곤 등 걷는 그림보다 앞서는 상태가 됐다
            self.stop_walk()
            return
        self.root.after(WALK_TICK_MS, self.walk_tick, walking)

    def walk_room(self, direction):
        # 그 방향으로 작업 영역 끝까지 남은 px
        left, _, right, _ = self.work_area()
        return right - self.images["idle_1"].width - self.x if direction > 0 else self.x - left

    def stop_walk(self):
        if self.walking is None:
            return
        self.walking = None
        self.save_config(x=self.x, y=self.y)
        self.show()

    # 조작: 조금만 움직이고 떼면 클릭(말하기), 그 이상이면 끌기(이동)
    def on_press(self, event):
        self.stop_walk()
        self.last_touch = time.monotonic()
        self.press = (event.x_root, event.y_root, self.x, self.y)

    def on_drag(self, event):
        if self.press is None:
            return
        sx, sy, wx, wy = self.press
        self.x, self.y = wx + event.x_root - sx, wy + event.y_root - sy
        self.root.geometry(f"+{self.x}+{self.y}")

    def on_release(self, event):
        if self.press is None:
            return
        sx, sy, _, _ = self.press
        self.press = None
        if abs(event.x_root - sx) <= CLICK_SLOP and abs(event.y_root - sy) <= CLICK_SLOP:
            self.speak_clicked()
            return
        left, top, right, bottom = self.work_area()
        self.x = max(left, min(self.x, right - self.images["idle_1"].width))
        self.y = max(top, min(self.y, bottom - HEIGHT))
        self.root.geometry(f"+{self.x}+{self.y}")
        self.save_config(x=self.x, y=self.y)


def main():
    # 이미 떠 있으면 바로 끝낸다
    ctypes.windll.kernel32.CreateMutexW(None, False, "Local\\ClaudeStatusMascot")
    if ctypes.windll.kernel32.GetLastError() == 183:  # ERROR_ALREADY_EXISTS
        return
    Mascot().root.mainloop()


if __name__ == "__main__":
    main()
