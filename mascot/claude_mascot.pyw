# Claude Mascot: 바탕화면에 SD 캐릭터를 띄워 Claude 상태와 사용량에 반응한다 (Windows 전용).
# 데이터: ~/.claude/claude-status/usage-<계정>.json (Claude Code 플러그인 usage-status-bridge 가 쓴다, 없으면 상태만), status.claude.com 공개 API.
# 이미지(images/*.png, 투명 배경)는 Windows 레이어드 창으로 픽셀 단위 투명도를 살려 그린다(가장자리가 부드러운 그림이라 색 빼기 방식은 계단이 진다).
# 조작: 클릭 = 사용량 말하기(말풍선), 끌기 = 후드 뒷덜미를 잡혀 들린 drag 그림으로 이동(위치 기억), 오른쪽 클릭 = 메뉴(사용량 말하기/장애 상세 열기/식사 주기/게임하기/날씨/걷기/작업 알림/스케줄 알림/사용량 알림/최근 알림/숨기기/완전히 종료).
# 날씨: 오른쪽 클릭 「날씨 > 위치 정하기」로 도시를 찾아 후보 중 고르면(기본은 안 정함 = 날씨 안 말함) 하루 한 번 5시 이후 처음 켜질 때·처음 한가할 때 인사와 함께 오늘 날씨,
#   비·눈 확률이 높으면 우산 한마디. 「날씨 > 오늘 날씨」로 언제든 다시 묻는다. 날씨는 Open-Meteo(키 없음).
#   날씨를 말하는 동안은 우산(비)·눈사람(눈)·귀마개와 장갑(체감 한파)·선풍기(체감 폭염) 그림으로 말한다.
# 걷기: 「걷기」가 체크돼 있으면(기본) 한가할 때 가끔 지금 높이에서 좌우로 몇 걸음 걷는다(walk_1~4, 왼쪽은 좌우 반전). 누르면 멈춘다.
# 식사 주기: 오른쪽 클릭 「식사 주기 > 햄버거」를 누르면 햄버거를 먹는다(eat_1~6, 약 7초). 누르거나 말하면 멈춘다.
# 게임하기: 오른쪽 클릭 「게임하기」 = 별도 창에서 플래피 버드식 미니 게임(클릭·스페이스 = 날아오르기, Esc = 그만). 최고 점수는 mascot.json 의 game_best.
#   게임 중에는 본체를 숨기고, 알림(장애 포함)은 말풍선 없이 「최근 알림」에만 남긴다.
# 업데이트(릴리스 exe 만): 켜고 1분 뒤·6시간마다 GitHub 최신 릴리스를 본다. 트레이 「자동 업데이트」 꺼짐(기본) = 버전마다 한 번 「새 버전이 나왔어요」,
#   켜짐 = 받아서 크기·SHA-256 확인 → 한가할 때 exe 이름 바꿔치기 → 새 exe 로 다시 켜져 「업데이트했어요」. 「지금 업데이트 확인」으로 바로 확인.
# 트레이 아이콘(pystray): 클릭 = 보이기, 오른쪽 클릭 = 보이기/숨기기/캐릭터/Windows 시작 시 실행/자동 업데이트/지금 업데이트 확인/완전히 종료. 완전히 끄는 길은 「완전히 종료」뿐이다.
# 이미지: 장애 sick > 점검 maintenance > 사용량 90% 이상 tired > 평상시 idle_* 무작위(30초마다). 말하는 동안은 talk(단, 장애·점검·피곤 이미지는 말하는 중에도 유지).
# 장애 알림: 장애 발생·새 사고·복구, 점검 시작·종료 때 클릭 없이 스스로 말풍선으로 알린다.
# 사용량 알림: 5시간·주간 사용량이 75%·90% 를 넘는 순간, 경고했던 창이 초기화될 때 말한다. 오른쪽 클릭 「사용량 알림」으로 끈다.
# 스케줄 알림(알림함): 다른 프로그램(예약 작업 등)이 inbox/ 에 넣은 JSON 을 하나씩 말하고 지운다. 오른쪽 클릭 「스케줄 알림」으로 끈다.
# 작업 알림(브리지가 notify.json 을 씀): Claude Code 턴이 끝나면 「<프로젝트> 작업 완료했어요!」와 답변 첫 줄,
#   권한 확인·질문으로 사람의 답을 기다리면 waiting 그림으로 「<프로젝트> 확인이 필요해요!」, 오류로 끝나면 sick 그림으로 「작업이 실패했어요!」. 오른쪽 클릭 「작업 알림」으로 끈다.
#   브리지가 세션마다 쓰는 상태(sessions/*.json)를 보고, 작업 중인 세션이 있으면 노트북 두드리는 그림(working_1~4)을 되풀이하고, 클릭 말풍선 맨 위에 「작업 중 2 · 대기 1」을 붙인다.
#   Desktop 앱 세션이면 그 말풍선을 눌러 해당 세션을 연다(claude://code/continue?session=local_…). 「최근 알림」에 최근 10개가 남는다.
# 인터랙션: 머리 위에서 문지르기 = 쓰다듬기(pet, 아플 때는 sick_pet 또는 얼음주머니 애니메이션), 10분 안 건드리면 잠들기(sleep),
#   켜질 때·시간대 첫 클릭 = 인사, mascot.json 의 birthdays 에 오늘(MM-DD)이 있으면 생일 축하(birthday), 「완전히 종료」 = 잘자요(goodnight) 뒤 종료.
# 캐릭터: ~/.claude/claude-status/characters/<이름>/ 에 같은 이름의 PNG 를 넣고 트레이 「캐릭터」에서 고른다. 빠진 그림은 기본 그림으로 채운다.
# 장애 중 말풍선: 사고 제목·최근 공지(상태 시각 — 본문 앞부분)·장애 서비스 + 사용량, 평소보다 오래(OUTAGE_TALK_MS). 오른쪽 클릭 「장애 상세 열기」 = 브라우저로 사고 페이지.
import ctypes
import ctypes.wintypes as wt
import datetime
import glob
import hashlib
import json
import os
import random
import re
import subprocess
import sys
import threading
import time
import tkinter as tk
import urllib.parse
import urllib.request
import webbrowser
import winreg

import pystray
from PIL import Image, ImageChops, ImageOps, ImageTk

# exe(PyInstaller)로 묶이면 그림은 실행 때 풀리는 임시 폴더(sys._MEIPASS)에 있다
IMAGE_DIR = os.path.join(getattr(sys, "_MEIPASS", os.path.dirname(os.path.abspath(__file__))), "images")
DATA_DIR = os.path.join(os.path.expanduser("~"), ".claude", "claude-status")
USAGE_GLOB = os.path.join(DATA_DIR, "usage-*.json")
CONFIG_PATH = os.path.join(DATA_DIR, "mascot.json")
# 알림함: 아무 프로그램이나 *.json 하나 = 알림 하나 {title, text, kind(info/warn/error), link(파일·주소)} 를 넣는다.
# 쓰는 중인 파일을 읽지 않게 다른 확장자로 쓴 뒤 .json 으로 이름을 바꾼다. 파일 하나를 덮어쓰는 notify.json 과 달리 보내는 곳이 여럿이어도 잃지 않는다
INBOX_DIR = os.path.join(DATA_DIR, "inbox")
NOTIFY_PATH = os.path.join(DATA_DIR, "notify.json")  # usage-status-bridge 가 작업 알림마다 쓴다: {at, kind(done/waiting/failed), project, text, session}
SESSIONS_GLOB = os.path.join(DATA_DIR, "sessions", "*.json")  # 브리지가 세션마다 쓴다: {at, state(working/waiting/idle/ended), project, session}
SESSION_STALE_MINUTES = 15  # working·waiting 인데 이만큼 갱신이 없으면 비정상 종료로 보고 센다에서 뺀다
SESSION_FORGET_HOURS = 24  # 끝난(ended) 세션 파일과 이만큼 갱신이 없는 파일은 지운다
SESSION_LINK = "claude://code/continue?session="  # Claude 데스크톱 앱이 이 세션(local_…)을 연다
SESSION_ID = re.compile(r"local_[A-Za-z0-9-]{1,64}")  # 앱이 받는 세션 ID 모양. 파일에서 읽은 값이라 이 모양일 때만 연다
CHARACTERS_DIR = os.path.join(DATA_DIR, "characters")  # 캐릭터마다 하위 폴더 하나, 안에 IMAGE_NAMES 와 같은 이름의 PNG
RUN_KEY = r"Software\Microsoft\Windows\CurrentVersion\Run"  # 「Windows 시작 시 실행」: 현재 사용자 시작 프로그램 목록
RUN_NAME = "ClaudeMascot"
STATUS_URL = "https://status.claude.com/api/v2/summary.json"
STATUS_PAGE = "https://status.claude.com"
# 업데이트: GitHub 최신 릴리스(초안·미리보기 제외)를 본다. 받은 exe 는 릴리스가 알려 준 크기·SHA-256 과 같아야 쓴다
RELEASE_API = "https://api.github.com/repos/thecider/ClaudeMascot/releases/latest"
RELEASE_PAGE = "https://github.com/thecider/ClaudeMascot/releases/latest"
DOWNLOAD_PREFIX = "https://github.com/thecider/ClaudeMascot/releases/download/"  # 이 주소에서만 받는다
UPDATE_ASSET = "ClaudeMascot.exe"
UPDATE_FIRST_MS = 60_000  # 켜고 이만큼 뒤 첫 확인
UPDATE_EVERY_MS = 6 * 3_600_000
UPDATE_RETRY_MS = 60_000  # 받아 뒀는데 바쁘면(게임·말풍선·끌기·메뉴) 이만큼 뒤 다시
# 날씨: Open-Meteo(키·가입 없음). 위치는 「날씨 > 위치 정하기」에서 이름으로 찾아 후보 중 고른 좌표만 mascot.json 의 weather_place 에 둔다
# (이름 첫 결과를 그냥 쓰면 「성남」이 북한 성남으로 잡힌다)
GEOCODE_URL = "https://geocoding-api.open-meteo.com/v1/search"
WEATHER_URL = "https://api.open-meteo.com/v1/forecast"
WEATHER_FROM_HOUR = 5  # 이 시각부터 그날 처음 한가할 때 한 번 오늘 날씨를 말한다
WEATHER_RETRY_S = 600  # 가져오지 못했으면 이만큼 뒤 다시
RAIN_PERCENT = 50  # 비·눈 확률이 이 이상이면 우산 한마디
# WMO 날씨 코드 → 말
WEATHER_NAMES = {0: "맑음", 1: "대체로 맑음", 2: "구름 조금", 3: "흐림", 45: "안개", 48: "안개",
                 51: "이슬비", 53: "이슬비", 55: "이슬비", 56: "어는 이슬비", 57: "어는 이슬비",
                 61: "약한 비", 63: "비", 65: "강한 비", 66: "어는 비", 67: "어는 비",
                 71: "약한 눈", 73: "눈", 75: "많은 눈", 77: "싸락눈", 80: "소나기", 81: "소나기", 82: "강한 소나기",
                 85: "눈", 86: "많은 눈", 95: "뇌우", 96: "우박 뇌우", 99: "우박 뇌우"}
SNOW_CODES = {71, 73, 75, 77, 85, 86}
# 날씨를 말하는 동안 talk 대신 보여 줄 그림. 하루 하나: 눈 > 비 > 한파 > 폭염 (한파·폭염은 체감온도, 폭염주의보가 체감 33°C 기준)
WEATHER_FRAMES = ("weather_rain", "weather_snow", "weather_cold", "weather_hot")
COLD_FEELS = -10  # 체감 최저가 이 이하면 귀마개·장갑
HOT_FEELS = 33  # 체감 최고가 이 이상이면 선풍기

HEIGHT = 160
IDLE_MS = 30_000
MOOD_POLL_MS = 20_000
STATUS_POLL_MS = 60_000
NOTIFY_POLL_MS = 2_000  # Windows 작업 완료 알림과 거의 같이 말하게 짧게 본다
HISTORY_SIZE = 10  # 오른쪽 클릭 「최근 알림」에 남기는 개수 (메모리에만, 다시 켜면 비어 있다)
TALK_MS = 6_000
OUTAGE_TALK_MS = 12_000  # 장애·점검 중에는 읽을 내용이 많다
TIRED_PERCENT = 90
USAGE_LEVELS = (75, 90)  # 사용량이 이 값을 넘는 순간 한 번씩 말한다. 경고했던 창이 초기화되면 그것도 말한다
USAGE_WINDOWS = {"five_hour": "5시간", "seven_day": "주간"}
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
# 햄버거 먹기: 「식사 주기 > 햄버거」를 누를 때 한 번 (그림, 보여 줄 ms). 들고 → 한 입 → 오물오물 두 번 → 한 입 더 → 만족(다 먹고 2초 더 머문다)
EAT_FRAMES = ("eat_1", "eat_2", "eat_3", "eat_4", "eat_5", "eat_6")
EAT_SEQUENCE = (("eat_1", 800), ("eat_2", 450), ("eat_3", 350), ("eat_4", 350), ("eat_3", 350), ("eat_4", 350),
                ("eat_2", 450), ("eat_3", 350), ("eat_4", 350), ("eat_5", 700), ("eat_6", 3000))
# 작업 중: 메인 대화 턴이 도는 세션이 하나라도 있으면 평상시 그림 대신 이 순서를 되풀이한다(그림, 보여 줄 ms). 타닥타닥 → 빠르게 → 잠깐 쉬며 뿌듯
WORKING_FRAMES = ("working_1", "working_2", "working_3", "working_4")
WORKING_SEQUENCE = (("working_1", 300), ("working_2", 300), ("working_1", 300), ("working_2", 300), ("working_3", 250),
                    ("working_2", 300), ("working_3", 250), ("working_1", 300), ("working_2", 300), ("working_4", 1500))
IMAGE_NAMES = ("idle_1", "idle_2", "idle_3", "idle_4", "talk", "sick", "maintenance", "tired", "pet", "sleep", "birthday", "goodnight",
               "sick_pet", "sick_ice_1", "sick_ice_2", "sick_ice_3", "sick_ice_4", "drag", "waiting") + WALK_FRAMES + EAT_FRAMES + WORKING_FRAMES + WEATHER_FRAMES
# 그림이 없으면 같은 캐릭터의 이 그림으로 (사용자 캐릭터에 다른 캐릭터가 섞여 보이지 않게, 걷는 그림이 없으면 idle_1 로 미끄러지듯)
FALLBACK_IMAGES = {"sick_pet": "sick", "sick_ice_1": "sick", "sick_ice_2": "sick", "sick_ice_3": "sick", "sick_ice_4": "sick",
                   "drag": "idle_1", "waiting": "talk", **{name: "idle_1" for name in WALK_FRAMES + EAT_FRAMES + WORKING_FRAMES},
                   **{name: "talk" for name in WEATHER_FRAMES}}
# 끌기: drag 그림의 후드 뒷덜미 위치(그림 너비·높이 비율). 어디를 눌렀든 이 점이 커서 아래로 와서 뒷덜미를 집어 든 것처럼 보인다
DRAG_ANCHOR = (0.5, 0.08)
# 아플 때 쓰다듬기: 보통은 sick_pet + 한마디, ICE_CHANCE 확률로 얼음주머니 갈아주기 애니메이션(그림, 보여 줄 ms)
SICK_PET_LINES = ("아프지만… 기분 좋아요", "헤헤… 조금 나아졌어요")
ICE_CHANCE = 1 / 3
ICE_FRAMES = (("sick_ice_1", 600), ("sick_ice_2", 700), ("sick_ice_3", 700), ("sick_ice_4", 1500))
ICE_LINE = "시원해요… 고마워요!"
# 게임하기: 별도 창에서 클릭(스페이스)하면 날아오르고 안 누르면 떨어진다. 기둥 틈을 지나면 1점. 값은 한 칸(GAME_TICK_MS)당 px
GAME_SIZE = (360, 540)
GAME_TICK_MS = 16
GAME_GRAVITY = 0.45
GAME_FLAP = -7.2  # 클릭 때 위로 속도
GAME_SPEED = 2.6  # 기둥이 다가오는 속도 (끝까지 같다)
GAME_GAP = 170  # 위아래 기둥 사이 틈
GAME_PIPE_W = 58
GAME_PIPE_EVERY = 200  # 기둥 간격
GAME_FIRST_PIPE = 140  # 첫 기둥은 화면 밖 이만큼 더 멀리서: 시작하자마자 기둥이 오면 손이 안 풀린다
GAME_GROUND = 40
GAME_BIRD_X = 90  # 캐릭터 가운데 x
GAME_BIRD_H = 64
GAME_HITBOX = 0.7  # 충돌은 그림보다 작게 본다: 그림 가장자리 스침으로 죽으면 억울하다
GAME_RESTART_S = 0.5  # 게임 오버 직후 이 동안 클릭은 무시한다(연타하다 바로 다시 시작되지 않게)
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


class MONITORINFO(ctypes.Structure):
    _fields_ = [("cbSize", wt.DWORD), ("rcMonitor", wt.RECT), ("rcWork", wt.RECT), ("dwFlags", wt.DWORD)]


user32.MonitorFromPoint.argtypes = [wt.POINT, wt.DWORD]
user32.MonitorFromPoint.restype = wt.HMONITOR
user32.GetMonitorInfoW.argtypes = [wt.HMONITOR, ctypes.POINTER(MONITORINFO)]
MONITOR_DEFAULTTONEAREST = 2
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


def app_version():
    # 릴리스 빌드(Actions)만 exe 안에 version.txt(태그 이름)를 넣는다. 로컬 빌드·.pyw 실행은 None 이고 업데이트를 확인하지 않는다
    if not getattr(sys, "frozen", False):
        return None
    try:
        with open(os.path.join(sys._MEIPASS, "version.txt"), encoding="utf-8") as f:
            return f.read().strip() or None
    except OSError:
        return None


def parse_version(tag):
    match = re.fullmatch(r"v?(\d+)\.(\d+)\.(\d+)", (tag or "").strip())
    return tuple(int(n) for n in match.groups()) if match else None


def exe_path():
    return sys.executable


def fetch_release():
    # 최신 릴리스 {tag, page, url, size, digest}. 조회 실패면 None
    request = urllib.request.Request(RELEASE_API, headers={"Accept": "application/vnd.github+json", "User-Agent": "ClaudeMascot"})
    try:
        with urllib.request.urlopen(request, timeout=15) as response:
            data = json.loads(response.read().decode("utf-8"))
    except (OSError, ValueError):
        return None
    if not isinstance(data, dict):
        return None
    asset = next((a for a in data.get("assets") or [] if isinstance(a, dict) and a.get("name") == UPDATE_ASSET), {})
    return {"tag": data.get("tag_name"), "page": data.get("html_url") or RELEASE_PAGE,
            "url": asset.get("browser_download_url"), "size": asset.get("size"), "digest": asset.get("digest")}


def download_update(info, dest):
    # dest 에 받고, 크기·SHA-256 이 릴리스 정보와 다르면 지운다. 쓸 수 있으면 True
    url, digest = info.get("url") or "", info.get("digest") or ""
    if not url.startswith(DOWNLOAD_PREFIX) or not digest.startswith("sha256:"):
        return False
    sha, size = hashlib.sha256(), 0
    try:
        with urllib.request.urlopen(url, timeout=60) as response, open(dest, "wb") as f:
            while chunk := response.read(1 << 16):
                f.write(chunk)
                sha.update(chunk)
                size += len(chunk)
        ok = size == info.get("size") and sha.hexdigest() == digest[len("sha256:"):]
    except OSError:
        ok = False
    if not ok:
        try:
            os.remove(dest)
        except OSError:
            pass
    return ok


def swap_exe(exe):
    # 실행 중인 exe 는 덮어쓸 수 없지만 이름은 바꿀 수 있다: 지금 것 → .old, 받은 .new → exe. 실패하면 되돌린다
    new, old = exe + ".new", exe + ".old"
    try:
        if os.path.exists(old):
            os.remove(old)
        os.rename(exe, old)
    except OSError:
        return False
    try:
        os.rename(new, exe)
    except OSError:
        try:
            os.rename(old, exe)
        except OSError:
            pass
        return False
    return True


def launch_updated(exe, tag):
    # 새 exe 를 따로 띄운다. 단일 exe(PyInstaller)는 환경 변수로 부모의 압축 푼 폴더를 물려받으므로 끊고 시작한다
    env = dict(os.environ, PYINSTALLER_RESET_ENVIRONMENT="1")
    subprocess.Popen([exe, "--updated", tag], env=env, close_fds=True, creationflags=subprocess.DETACHED_PROCESS)


def get_json(url, params):
    # 조회 실패면 None
    try:
        with urllib.request.urlopen(url + "?" + urllib.parse.urlencode(params), timeout=10) as response:
            return json.loads(response.read().decode("utf-8"))
    except (OSError, ValueError):
        return None


def search_places(name):
    # 이름으로 찾은 후보 [{label, lat, lon}]. 조회 실패면 None
    data = get_json(GEOCODE_URL, {"name": name, "count": 10, "language": "ko", "format": "json"})
    if not isinstance(data, dict):
        return None
    places = []
    for r in data.get("results") or []:
        if isinstance(r, dict) and isinstance(r.get("latitude"), (int, float)) and isinstance(r.get("longitude"), (int, float)):
            # 같은 이름이 많아서 도·시군·나라까지 붙여 보여 준다 (이름과 같은 칸은 뺀다)
            parts = [r.get("name")] + [r.get(k) for k in ("admin2", "admin1", "country") if r.get(k) and r.get(k) != r.get("name")]
            places.append({"label": ", ".join(str(p) for p in parts if p), "lat": r["latitude"], "lon": r["longitude"]})
    return places


def fetch_weather(place):
    # 오늘 날씨 {code, high, low, rain, now, feels_high, feels_low}. 조회 실패면 None
    data = get_json(WEATHER_URL, {"latitude": place["lat"], "longitude": place["lon"], "timezone": "auto", "forecast_days": 1,
                                  "current": "temperature_2m",
                                  "daily": "weather_code,temperature_2m_max,temperature_2m_min,precipitation_probability_max,"
                                           "apparent_temperature_max,apparent_temperature_min"})
    try:
        daily = data["daily"]
        return {"code": daily["weather_code"][0], "high": daily["temperature_2m_max"][0], "low": daily["temperature_2m_min"][0],
                "rain": daily["precipitation_probability_max"][0], "now": data["current"]["temperature_2m"],
                "feels_high": daily["apparent_temperature_max"][0], "feels_low": daily["apparent_temperature_min"][0]}
    except (TypeError, KeyError, IndexError):
        return None


def weather_pose(weather):
    # 말하는 동안 보여 줄 날씨 그림 이름, 해당 없으면 None (말풍선 우산 한마디와 같은 기준으로 비·눈)
    rain, low, high = weather.get("rain"), weather.get("feels_low"), weather.get("feels_high")
    if isinstance(rain, (int, float)) and rain >= RAIN_PERCENT:
        return "weather_snow" if weather.get("code") in SNOW_CODES else "weather_rain"
    if isinstance(low, (int, float)) and low <= COLD_FEELS:
        return "weather_cold"
    if isinstance(high, (int, float)) and high >= HOT_FEELS:
        return "weather_hot"
    return None


def weather_speech(place, weather):
    # 「성남시 오늘 맑음, 6~13°C (지금 12°C)」 + 비·눈 확률이 높으면 우산 한마디
    lines = [f"{place['label'].split(',')[0]} 오늘 {WEATHER_NAMES.get(weather['code'], '날씨 알 수 없음')}, "
             f"{round(weather['low'])}~{round(weather['high'])}°C (지금 {round(weather['now'])}°C)"]
    if isinstance(weather["rain"], (int, float)) and weather["rain"] >= RAIN_PERCENT:
        lines.append(f"{'눈' if weather['code'] in SNOW_CODES else '비'} 올 확률 {weather['rain']}% — 우산 챙기세요!")
    return "\n".join(lines)


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


def load_sessions(now):
    # 브리지가 쓴 세션 상태들. 끝났거나 오래 갱신이 없는 파일은 지우고, working·waiting 이 오래 멈춘 세션(비정상 종료)은 idle 로 본다
    sessions = []
    for path in glob.glob(SESSIONS_GLOB):
        session = load_json(path)
        at = parse_time(session.get("at") or "")
        age = (now - at).total_seconds() if at else None
        if session.get("state") == "ended" or age is None or age > SESSION_FORGET_HOURS * 3600:
            try:
                os.remove(path)
            except OSError:
                pass
            continue
        if session.get("state") in ("working", "waiting") and age > SESSION_STALE_MINUTES * 60:
            session["state"] = "idle"
        sessions.append(session)
    return sessions


def sessions_line(sessions):
    # 「작업 중 2 · 대기 1」: 둘 다 0 이면 None
    counts = [(label, sum(s.get("state") == state for s in sessions)) for state, label in (("working", "작업 중"), ("waiting", "대기"))]
    parts = [f"{label} {n}" for label, n in counts if n]
    return " · ".join(parts) or None


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


class Game:
    # 게임하기 창. y = 캐릭터 가운데 높이, pipes = [기둥 왼쪽 x, 틈 위쪽 y, 점수 셌나]. 첫 클릭 전에는 멈춰 있다
    def __init__(self, mascot):
        self.mascot = mascot
        width, height = GAME_SIZE
        self.win = tk.Toplevel(mascot.root)
        self.win.title("게임하기")
        self.win.resizable(False, False)
        self.win.attributes("-topmost", True)
        # 마스코트 왼쪽에(자리가 없으면 오른쪽에) 띄우고 작업 영역 안으로 당긴다
        left, top, right, bottom = mascot.work_area()
        x = mascot.x - width - 16 if mascot.x - width - 16 >= left else mascot.x + mascot.images["idle_1"].width + 16
        x = max(left, min(x, right - width))
        y = max(top, min(mascot.y + HEIGHT - height, bottom - height - 40))
        self.win.geometry(f"{width}x{height}+{x}+{y}")
        self.canvas = tk.Canvas(self.win, width=width, height=height, highlightthickness=0, bg="#cdebf7")
        self.canvas.pack()
        self.sprites = {name: self.sprite(name) for name in ("idle_1", "drag", "sick")}
        # 그림 요소는 한 번만 만들고 매 칸 위치·내용만 바꾼다: 매번 지우고 새로 만들면 끊긴다.
        # 기둥은 화면에 동시에 나올 수 있는 수만큼 미리 만들고, 안 쓰는 것은 화면 밖에 둔다
        c = self.canvas
        self.pipe_items = [tuple(c.create_rectangle(-99, 0, -99, 0, fill="#f28c38", outline="#c0651f", width=2) for _ in range(2))
                           for _ in range((width + GAME_FIRST_PIPE + GAME_PIPE_W) // GAME_PIPE_EVERY + 2)]
        c.create_rectangle(-2, height - GAME_GROUND, width + 2, height + 2, fill="#e8c99b", outline="#c9a46e", width=2)
        self.bird_item = c.create_image(GAME_BIRD_X, 0)
        self.score_item = c.create_text(width / 2, 48, font=("Segoe UI", 28, "bold"), fill="#5a3a1a")
        self.message_item = c.create_text(width / 2, 0, font=("Segoe UI", 13, "bold"), fill="#5a3a1a", justify="center")
        self.win.bind("<ButtonPress-1>", lambda e: self.flap())
        self.win.bind("<space>", lambda e: self.flap())
        self.win.bind("<Escape>", lambda e: self.close())
        self.win.protocol("WM_DELETE_WINDOW", self.close)
        self.win.focus_force()
        self.closed = False
        self.reset()
        self.loop()

    def sprite(self, name):
        # 그림의 빈 여백을 잘라 GAME_BIRD_H 높이로
        image = open_image(name, self.mascot.character)
        image = image.crop(image.getchannel("A").point(lambda a: 255 if a > 128 else 0).getbbox())
        image = image.resize((round(image.width * GAME_BIRD_H / image.height), GAME_BIRD_H), Image.LANCZOS)
        return ImageTk.PhotoImage(image)

    def reset(self):
        self.y = GAME_SIZE[1] * 0.4
        self.vy = 0
        self.pipes = []
        self.score = 0
        self.started = self.over = self.new_record = False
        self.over_at = 0

    def flap(self):
        if self.over:
            if time.monotonic() - self.over_at >= GAME_RESTART_S:
                self.reset()
            return
        self.started = True
        self.vy = GAME_FLAP

    def bird_box(self):
        sprite = self.sprites[self.sprite_name()]
        half_w, half_h = sprite.width() * GAME_HITBOX / 2, sprite.height() * GAME_HITBOX / 2
        return GAME_BIRD_X - half_w, self.y - half_h, GAME_BIRD_X + half_w, self.y + half_h

    def sprite_name(self):
        return "sick" if self.over else "drag" if self.vy < 0 else "idle_1"

    def step(self):
        if not self.started or self.over:
            return
        width, height = GAME_SIZE
        self.vy += GAME_GRAVITY
        self.y += self.vy
        for pipe in self.pipes:
            pipe[0] -= GAME_SPEED
        self.pipes = [pipe for pipe in self.pipes if pipe[0] + GAME_PIPE_W > 0]
        if not self.pipes or self.pipes[-1][0] < width - GAME_PIPE_EVERY:
            self.pipes.append([width + (0 if self.pipes or self.score else GAME_FIRST_PIPE), random.uniform(60, height - GAME_GROUND - 60 - GAME_GAP), False])
        x1, y1, x2, y2 = self.bird_box()
        for pipe in self.pipes:
            if not pipe[2] and pipe[0] + GAME_PIPE_W < x1:
                pipe[2] = True
                self.score += 1
        hit = y1 < 0 or y2 > height - GAME_GROUND or any(
            pipe[0] < x2 and pipe[0] + GAME_PIPE_W > x1 and (y1 < pipe[1] or y2 > pipe[1] + GAME_GAP) for pipe in self.pipes)
        if hit:
            self.game_over()

    def game_over(self):
        self.over = True
        self.over_at = time.monotonic()
        self.best = (read_config() or {}).get("game_best", 0)
        self.new_record = self.score > self.best
        if self.new_record:
            self.best = self.score
            self.mascot.save_config(game_best=self.score)

    def draw(self):
        width, height = GAME_SIZE
        c = self.canvas
        for k, (top, bottom) in enumerate(self.pipe_items):
            if k < len(self.pipes):
                x, gap, _ = self.pipes[k]
                c.coords(top, x, -2, x + GAME_PIPE_W, gap)
                c.coords(bottom, x, gap + GAME_GAP, x + GAME_PIPE_W, height - GAME_GROUND)
            else:
                c.coords(top, -99, 0, -99, 0)
                c.coords(bottom, -99, 0, -99, 0)
        c.coords(self.bird_item, GAME_BIRD_X, self.y)
        c.itemconfigure(self.bird_item, image=self.sprites[self.sprite_name()])
        c.itemconfigure(self.score_item, text=str(self.score))
        if not self.started:
            message, at = "클릭(스페이스)하면 시작!\nEsc 로 그만하기", 0.62
        elif self.over:
            message, at = "\n".join(["앗! 부딪혔어요", f"점수 {self.score} · 최고 {self.best}"] + (["최고 기록!"] if self.new_record else []) + ["클릭하면 다시"]), 0.45
        else:
            message, at = "", 0.5
        c.coords(self.message_item, width / 2, height * at)
        c.itemconfigure(self.message_item, text=message)

    def loop(self):
        if self.closed:
            return
        self.step()
        self.draw()
        self.win.after(GAME_TICK_MS, self.loop)

    def close(self):
        if self.closed:
            return
        self.closed = True
        self.win.destroy()
        self.mascot.game = None
        self.mascot.show_window()


class PlacePicker:
    # 날씨 위치 정하기 창: 이름으로 찾고 → 후보 중 하나를 고른다. 찾기는 스레드에서(창이 멈추지 않게)
    def __init__(self, mascot):
        self.mascot = mascot
        self.places = []
        self.win = tk.Toplevel(mascot.root)
        self.win.title("날씨 위치 정하기")
        self.win.attributes("-topmost", True)
        self.win.resizable(False, False)
        self.win.configure(padx=12, pady=10)
        tk.Label(self.win, text="도시 이름 (예: 서울특별시, 성남시, Seoul)", font=("Segoe UI", 9)).pack(anchor="w")
        row = tk.Frame(self.win)
        row.pack(fill="x", pady=(4, 6))
        self.entry = tk.Entry(row, font=("Segoe UI", 10), width=30)
        self.entry.pack(side="left", fill="x", expand=True)
        self.find_button = tk.Button(row, text="찾기", command=self.search, width=6)
        self.find_button.pack(side="left", padx=(6, 0))
        self.listbox = tk.Listbox(self.win, font=("Segoe UI", 9), width=48, height=10, activestyle="none")
        self.listbox.pack(fill="both")
        self.message = tk.Label(self.win, text="", fg="#666", font=("Segoe UI", 9), justify="left", wraplength=340)
        self.message.pack(anchor="w", pady=(4, 4))
        tk.Button(self.win, text="이 위치로 정하기", command=self.pick).pack(anchor="e")
        self.entry.bind("<Return>", lambda e: self.search())
        self.listbox.bind("<Double-Button-1>", lambda e: self.pick())
        self.win.bind("<Escape>", lambda e: self.close())
        self.win.protocol("WM_DELETE_WINDOW", self.close)
        self.win.update_idletasks()
        left, top, right, bottom = mascot.work_area()
        width, height = self.win.winfo_reqwidth(), self.win.winfo_reqheight()
        self.win.geometry(f"+{(left + right - width) // 2}+{(top + bottom - height) // 2}")
        self.win.focus_force()
        self.entry.focus_set()

    def search(self):
        name = self.entry.get().strip()
        if not name:
            return
        self.find_button.configure(state="disabled")
        self.message.configure(text="찾는 중…")
        threading.Thread(target=lambda: self.mascot.root.after(0, self.found, search_places(name)), daemon=True).start()

    def found(self, places):
        if not self.win.winfo_exists():
            return
        self.find_button.configure(state="normal")
        self.places = places or []
        self.listbox.delete(0, "end")
        for place in self.places:
            self.listbox.insert("end", place["label"])
        if places is None:
            self.message.configure(text="찾지 못했어요. 인터넷 연결을 확인해 주세요")
        elif not places:
            # 짧은 한글 이름(서울·부산)은 안 나오거나 작은 마을이 나온다
            self.message.configure(text="결과가 없어요. 「서울특별시」「성남시」처럼 시·도까지 붙이거나 영어(Seoul)로 찾아보세요")
        else:
            self.listbox.selection_set(0)
            self.message.configure(text="맞는 곳을 골라 주세요. 원하는 곳이 없으면 「성남시」처럼 시·도까지 붙이거나 영어로 찾아보세요")

    def pick(self):
        chosen = self.listbox.curselection()
        if not chosen:
            return
        place = self.places[chosen[0]]
        self.close()
        self.mascot.set_weather_place(place)

    def close(self):
        self.win.destroy()
        self.mascot.picker = None


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
        self.dragging = False  # 누른 채 CLICK_SLOP 넘게 움직였으면 끌기(drag 그림)
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
        self.eating = None  # 먹는 중이면 [EAT_SEQUENCE 위치]
        self.sessions = []  # 브리지가 쓴 세션 상태들 (load_sessions)
        self.working = None  # 작업 중 그림을 돌리는 중이면 [WORKING_SEQUENCE 위치]
        self.notified = load_json(NOTIFY_PATH).get("at")  # 이미 말한 작업 알림. 켜기 전에 온 알림은 말하지 않는다
        self.history = []  # 최근 작업 알림, 새것이 앞: (메뉴 한 줄 "HH:MM 프로젝트 · 완료 — 한 줄", 말풍선 내용, 세션 링크 또는 None)
        self.pose = None  # 말하는 동안 talk 대신 보여 줄 그림(입력 대기 = waiting)
        self.usage_levels = {}  # (계정, 창) → (넘은 USAGE_LEVELS 단계(아직이면 0), 초기화 시각 문자열)
        self.game = None  # 게임하기 창이 열려 있으면 Game. 그동안 본체는 숨겨 두고 알림은 「최근 알림」에만 남긴다
        self.version = app_version()  # 릴리스 exe 의 태그(v1.8.0). None 이면 업데이트를 확인하지 않는다
        self.auto_update = bool((config or {}).get("auto_update", False))
        self.updating = False  # 새 exe 를 받는 중이거나 받아 두고 교체를 기다리는 중
        # 업데이트로 다시 켜졌으면 새 버전 태그 (launch_updated 가 「--updated <태그>」로 띄운다)
        self.updated_to = sys.argv[2] if len(sys.argv) > 2 and sys.argv[1] == "--updated" else None
        place = (config or {}).get("weather_place")
        self.weather_place = place if isinstance(place, dict) and {"label", "lat", "lon"} <= place.keys() else None  # 안 정했으면 날씨를 말하지 않는다
        self.weather_busy = False  # 날씨를 가져오는 중
        self.weather_retry = 0.0  # 아침 날씨를 못 가져왔으면 이 시각(monotonic)까지 다시 안 한다
        self.picker = None  # 열려 있는 위치 정하기 창

        self.root = tk.Tk()
        self.root.overrideredirect(True)
        self.root.attributes("-topmost", True)
        width, height = self.images["idle_1"].size
        # 저장 위치가 있는 모니터에 둔다(처음엔 주 모니터 — 주 모니터는 늘 (0,0) 을 포함). 모니터를 뺐거나 영역 밖이면 가장 가까운 모니터 안으로 끌어온다
        saved_x, saved_y = (config or {}).get("x"), (config or {}).get("y")
        left, top, right, bottom = self.work_area(saved_x or 0, saved_y or 0)
        self.x = max(left, min(right - width - 16 if saved_x is None else saved_x, right - width))
        self.y = max(top, min(bottom - height if saved_y is None else saved_y, bottom - height))
        self.root.geometry(f"{width}x{height}+{self.x}+{self.y}")
        self.root.update()
        # tk 의 최상위 프레임 창을 레이어드 창으로 바꾼다: 이후 그림은 tk 가 아니라 UpdateLayeredWindow 가 그린다
        self.hwnd = user32.GetParent(self.root.winfo_id())
        user32.SetWindowLongW(self.hwnd, GWL_EXSTYLE, user32.GetWindowLongW(self.hwnd, GWL_EXSTYLE) | WS_EX_LAYERED)

        self.menu = tk.Menu(self.root, tearoff=0)
        self.menu.add_command(label="사용량 말하기", command=self.speak_clicked)
        self.menu.add_command(label="장애 상세 열기", command=lambda: webbrowser.open(incident_url(self.status)))
        self.feed_menu = tk.Menu(self.menu, tearoff=0)
        self.feed_menu.add_command(label="햄버거", command=self.feed)
        self.menu.add_cascade(label="식사 주기", menu=self.feed_menu)
        self.menu.add_command(label="게임하기", command=self.play_game)
        self.weather_menu = tk.Menu(self.menu, tearoff=0)
        self.weather_menu.add_command(label="오늘 날씨", command=self.tell_weather)
        self.weather_menu.add_command(label="위치 정하기…", command=self.open_picker)
        self.menu.add_cascade(label="날씨", menu=self.weather_menu)
        self.walk_enabled = tk.BooleanVar(self.root, (config or {}).get("walk", True))
        self.menu.add_checkbutton(label="걷기", variable=self.walk_enabled, command=lambda: self.save_config(walk=self.walk_enabled.get()))
        self.notify_enabled = tk.BooleanVar(self.root, (config or {}).get("notify", True))
        self.menu.add_checkbutton(label="작업 알림", variable=self.notify_enabled, command=lambda: self.save_config(notify=self.notify_enabled.get()))
        self.inbox_enabled = tk.BooleanVar(self.root, (config or {}).get("inbox_notify", True))
        self.menu.add_checkbutton(label="스케줄 알림", variable=self.inbox_enabled, command=lambda: self.save_config(inbox_notify=self.inbox_enabled.get()))
        self.usage_enabled = tk.BooleanVar(self.root, (config or {}).get("usage_notify", True))
        self.menu.add_checkbutton(label="사용량 알림", variable=self.usage_enabled, command=lambda: self.save_config(usage_notify=self.usage_enabled.get()))
        self.history_menu = tk.Menu(self.menu, tearoff=0, postcommand=self.fill_history)
        self.menu.add_cascade(label="최근 알림", menu=self.history_menu)
        self.menu.add_command(label="숨기기", command=self.hide_window)
        self.menu.add_separator()
        self.menu.add_command(label="완전히 종료", command=self.quit)

        # 트레이 메뉴 동작은 pystray 스레드에서 불리므로 after 로 Tk 스레드에 넘긴다
        # 업데이트 메뉴는 버전을 아는 릴리스 exe 에만 보인다
        update_items = (pystray.MenuItem("자동 업데이트", self.toggle_auto_update, checked=lambda item: self.auto_update),
                        pystray.MenuItem("지금 업데이트 확인", lambda: self.root.after(0, self.check_update, True))) if self.version else ()
        self.tray = pystray.Icon("ClaudeMascot", tray_image(self.character), "Claude 마스코트", pystray.Menu(
            pystray.MenuItem("보이기", lambda: self.root.after(0, self.show_window), default=True),
            pystray.MenuItem("숨기기", lambda: self.root.after(0, self.hide_window)),
            pystray.MenuItem("캐릭터", pystray.Menu(self.character_items)),
            pystray.MenuItem("Windows 시작 시 실행", self.toggle_autostart, checked=lambda item: autostart_enabled()),
            *update_items,
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

        self.check_usage()  # 처음 보는 계정·창은 기억만 한다: 켤 때 이미 넘은 단계는 말하지 않는다
        self.show()
        self.rotate_idle()
        # 첫 poll_mood 는 타이머로: 바로 부르면 생일 축하가 시작 인사(1초 뒤)보다 먼저 끼어든다
        self.root.after(MOOD_POLL_MS, self.poll_mood)
        self.poll_status()
        self.poll_notify()
        self.keep_on_top()
        self.root.after(1000, self.greet_on_start)
        self.root.after(random.randint(*WALK_EVERY_MS), self.maybe_walk)
        if self.version:
            self.cleanup_update()
            self.root.after(5000, self.cleanup_update)  # 업데이트 직후면 옛 프로세스가 아직 .old 를 잡고 있을 수 있다
            self.root.after(UPDATE_FIRST_MS, self.poll_update)

    def work_area(self, x=None, y=None):
        # 클순이 몸 가운데가 있는 모니터의 작업 영역(어느 모니터에도 없으면 가장 가까운 모니터). x 가 None 이면 지금 위치
        if x is None:
            x, y = self.x, self.y
        info = MONITORINFO(cbSize=ctypes.sizeof(MONITORINFO))
        monitor = user32.MonitorFromPoint(wt.POINT(x + self.images["idle_1"].width // 2, y + HEIGHT // 2), MONITOR_DEFAULTTONEAREST)
        user32.GetMonitorInfoW(monitor, ctypes.byref(info))
        rect = info.rcWork
        return rect.left, rect.top, rect.right, rect.bottom

    # 그리기
    def current(self):
        # 우선순위: 잘자요 > 끌기 > 아플 때 쓰다듬기(얼음주머니·sick_pet) > 장애·점검·피곤 > 걷기 > 햄버거 먹기 > 쓰다듬기 > 생일 축하 말풍선 > 말하기 > 작업 중 > 잠 > 생일 > 평상시
        # 작업 중에는 평상시 그림이 아니라서 걷기가 시작되지 않고 잠들지도 않는다
        # 장애·점검·피곤 이미지는 말하는 중에도 유지한다: 아픈 모습이 바로 보여야 직관적이다. talk 는 평상시에 말할 때만
        # 끌기는 아플 때도 drag: 들려 가는 동안은 어미 고양이에게 물린 새끼처럼 평온한 얼굴로 보인다
        if self.closing:
            return "goodnight"
        if self.dragging:
            return "drag"
        mood = pick_mood(self.status["status"]["indicator"] if self.status else None, load_accounts(), datetime.datetime.now(datetime.timezone.utc))
        if mood == "sick" and self.petting:
            return self.ice_frame or "sick_pet"
        if mood:
            return mood
        if self.walking:
            direction, _, frame = self.walking
            return WALK_FRAMES[frame] + ("_left" if direction < 0 else "")
        if self.eating:
            return EAT_SEQUENCE[self.eating[0]][0]
        if self.petting:
            return "pet"
        if self.celebrating:
            return "birthday"
        if self.talking:
            return self.pose or "talk"
        if self.working:
            return WORKING_SEQUENCE[self.working[0]][0]
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
        if self.bubble is not None:
            return
        if self.updated_to:
            self.speak(body=f"{self.updated_to} 버전으로 업데이트했어요!")
            return
        if self.greet_birthday():
            return
        greeting = self.take_greeting()
        if self.daily_weather(greeting):  # 오늘 처음이면 인사에 날씨를 붙여 말한다(가져온 뒤)
            return
        if greeting:
            self.speak(greeting)

    # 날씨
    def daily_weather(self, greeting=None):
        # 위치를 정했고 WEATHER_FROM_HOUR 이후 오늘 아직 안 말했으면 가져와서 말한다. 숨김·게임·종료 중이면 보일 때까지 미룬다. 시작했으면 True
        now = local_now()
        if (self.weather_place is None or self.weather_busy or now.hour < WEATHER_FROM_HOUR or time.monotonic() < self.weather_retry
                or (read_config() or {}).get("weather_day") == f"{now:%Y-%m-%d}"
                or self.game is not None or self.closing or self.root.state() == "withdrawn"):
            return False
        self.request_weather(False, greeting)
        return True

    def tell_weather(self):
        if self.weather_place is None:
            self.open_picker()
        elif not self.weather_busy:
            self.request_weather(True)

    def request_weather(self, manual, greeting=None):
        self.weather_busy = True
        place = self.weather_place
        threading.Thread(target=lambda: self.root.after(0, self.got_weather, place, fetch_weather(place), manual, greeting), daemon=True).start()

    def got_weather(self, place, weather, manual, greeting):
        # 메뉴로 물었으면 늘 말한다. 아침 날씨는 말풍선이 떠 있거나 숨겨졌으면 「최근 알림」에만 남긴다(오늘 몫은 끝)
        self.weather_busy = False
        if weather is None:
            if manual:
                self.speak(body="날씨를 가져오지 못했어요")
                return
            self.weather_retry = time.monotonic() + WEATHER_RETRY_S
            if greeting:
                self.speak(greeting)
            return
        text = weather_speech(place, weather)
        if not manual:
            self.save_config(weather_day=f"{local_now():%Y-%m-%d}")
        self.history = [(f"{local_now():%H:%M} 날씨 — {text.splitlines()[0]}", text, None)] + self.history[:HISTORY_SIZE - 1]
        if manual or (self.bubble is None and self.game is None and not self.closing and self.root.state() != "withdrawn"):
            self.speak(headline=greeting, body=text, pose=weather_pose(weather))

    def open_picker(self):
        if self.picker is not None:
            self.picker.win.lift()
            self.picker.win.focus_force()
            return
        self.picker = PlacePicker(self)

    def set_weather_place(self, place):
        # 위치를 정하면 바로 그곳 날씨를 말한다
        self.weather_place = place
        self.save_config(weather_place=place)
        self.request_weather(True)

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
        self.check_usage()
        if self.bubble is None:  # 켜 둔 채 날이 바뀌었거나 숨겨 뒀다 다시 보이면 그때 아침 날씨
            self.daily_weather()
        self.root.after(MOOD_POLL_MS, self.poll_mood)

    def check_usage(self):
        # 계정·창(5시간/주간)마다 넘은 단계를 기억해, 단계가 오르면 「75% 넘었어요」, 경고했던 창이 초기화되면 「초기화됐어요」.
        # 처음 보는 계정·창은 기억만 한다. 「최근 알림」에는 늘 남기고, 말풍선은 사용량 알림이 꺼져 있거나 숨겨져 있거나 종료 중이면 넘긴다
        now = datetime.datetime.now(datetime.timezone.utc)
        lines = []
        for usage in load_accounts():
            name = (usage.get("account") or "--").split("@")[0]
            for kind, label in USAGE_WINDOWS.items():
                window = usage["windows"].get(kind)
                if not window:
                    continue
                percent = effective_percent(window, now)
                level = max((l for l in USAGE_LEVELS if percent >= l), default=0)
                resets = window.get("resetsAt") or ""
                key = (usage.get("account"), kind)
                previous = self.usage_levels.get(key)
                self.usage_levels[key] = (level, resets)
                if previous is None:
                    continue
                was, was_resets = previous
                # 초기화: 경고했던 창이 0% 가 됐거나(초기화 시각이 지남) 새 창으로 넘어갔다(초기화 시각이 30분 넘게 뒤로. 몇 초 흔들림은 무시)
                old_at, new_at = parse_time(was_resets), parse_time(resets)
                moved = old_at is not None and new_at is not None and new_at - old_at > datetime.timedelta(minutes=30)
                if was and (percent == 0 or moved):
                    lines.append(f"{name} {label} 사용량이 초기화됐어요! 다시 쓸 수 있어요")
                elif level > was:
                    at = parse_time(resets)
                    when = f" (초기화 {at.astimezone():{'%H:%M' if kind == 'five_hour' else '%m/%d %H:%M'}})" if at else ""
                    lines.append(f"{name} {label} 사용량 {level}% 넘었어요{when}")
        if not lines:
            return
        body = "\n".join(lines)
        self.history = [(f"{local_now():%H:%M} 사용량 — {lines[0]}", body, None)] + self.history[:HISTORY_SIZE - 1]
        if self.usage_enabled.get() and not self.closing and self.root.state() != "withdrawn":
            self.speak(body=body)

    def poll_status(self):
        threading.Thread(target=self.fetch_status, daemon=True).start()
        self.root.after(STATUS_POLL_MS, self.poll_status)

    def poll_notify(self):
        # notify.json 이 바뀌었으면: 턴이 끝남(kind done) = 「<프로젝트> 작업 완료했어요!」, 사람의 답을 기다림(waiting) = 「<프로젝트> 확인이 필요해요!」 + 한 줄.
        # 「최근 알림」에는 늘 남기고, 말풍선은 알림이 꺼져 있거나 숨겨져 있거나 종료 중이면 넘긴다
        # (꺼져 있어도 본 것으로 친다: 다시 켰을 때 지난 알림을 뒤늦게 말하지 않게)
        self.poll_sessions()
        note = load_json(NOTIFY_PATH)
        at = note.get("at")
        if at and at != self.notified:
            self.notified = at
            kind = note.get("kind")
            waiting = kind == "waiting"
            project = note.get("project") or "Claude"
            headline = f"{project} {'확인이 필요해요' if waiting else '작업이 실패했어요' if kind == 'failed' else '작업 완료했어요'}!"
            body = "\n".join(filter(None, (headline, note.get("text"))))
            # Desktop 앱 세션이면 말풍선을 눌러 그 세션으로 간다(CLI 세션은 session 이 없어 그냥 닫힌다)
            session = note.get("session")
            link = SESSION_LINK + session if isinstance(session, str) and SESSION_ID.fullmatch(session) else None
            label = f"{local_now():%H:%M} {project} · {'대기' if waiting else '실패' if kind == 'failed' else '완료'}" + (f" — {note['text']}" if note.get("text") else "")
            self.history = [(label, body, link)] + self.history[:HISTORY_SIZE - 1]
            if self.notify_enabled.get() and not self.closing and self.root.state() != "withdrawn":
                self.speak(body=body, link=link, pose="waiting" if waiting else "sick" if kind == "failed" else None)
        self.poll_inbox()
        self.root.after(NOTIFY_POLL_MS, self.poll_notify)

    def poll_inbox(self):
        # 알림함을 이름 순서로 읽고 지운다. 말풍선이 떠 있으면 닫힐 때까지 다음 것은 남겨 둔다(켜기 전에 쌓인 것도 말한다).
        # 꺼져 있거나 숨겨져 있으면 말하지 않고 「최근 알림」에만 남긴다. 깨진 파일은 말없이 지운다
        try:
            names = sorted(n for n in os.listdir(INBOX_DIR) if n.endswith(".json"))
        except OSError:
            return
        for name in names:
            speaking = self.inbox_enabled.get() and not self.closing and self.root.state() != "withdrawn"
            if speaking and self.bubble is not None:
                return
            path = os.path.join(INBOX_DIR, name)
            note = load_json(path)
            try:
                os.remove(path)
            except OSError:
                continue
            if not isinstance(note, dict) or not (note.get("title") or note.get("text")):
                continue
            title, text = str(note.get("title") or ""), str(note.get("text") or "")
            body = "\n".join(filter(None, (title, text)))
            link = note.get("link") if isinstance(note.get("link"), str) else None
            pose = {"warn": "waiting", "error": "sick"}.get(note.get("kind"))
            label = f"{local_now():%H:%M} " + " — ".join(filter(None, (title, text.splitlines()[0] if text else "")))
            self.history = [(label, body, link)] + self.history[:HISTORY_SIZE - 1]
            if speaking:
                self.speak(body=body, link=link, pose=pose)

    def poll_sessions(self):
        # 세션 상태를 다시 읽어, 작업 중인 세션이 생기면 작업 중 그림을 돌리기 시작하고 다 끝나면 멈춘다
        self.sessions = load_sessions(datetime.datetime.now(datetime.timezone.utc))
        busy = any(s.get("state") == "working" for s in self.sessions)
        if busy and self.working is None:
            self.working = [0]
            self.show()
            self.root.after(WORKING_SEQUENCE[0][1], self.work_tick, self.working)
        elif not busy and self.working is not None:
            self.working = None
            self.show()

    def work_tick(self, working):
        if working is not self.working:  # 그 사이 작업이 끝났다(다시 시작했으면 그 타이머가 따로 돈다)
            return
        working[0] = (working[0] + 1) % len(WORKING_SEQUENCE)
        self.show()
        self.root.after(WORKING_SEQUENCE[working[0]][1], self.work_tick, working)

    def fill_history(self):
        # 「최근 알림」을 펼칠 때마다 새로 채운다. 누르면 세션 링크가 있으면 그 세션을 열고, 없으면 그 알림을 다시 말한다
        self.history_menu.delete(0, "end")
        if not self.history:
            self.history_menu.add_command(label="(아직 없음)", state="disabled")
        for label, body, link in self.history:
            self.history_menu.add_command(label=label, command=lambda body=body, link=link: os.startfile(link) if link else self.speak(body=body))

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
            headline = "Claude 장애가 났어요"
        elif state == "down" and incidents - self.seen_incidents:
            headline = "새 사고가 생겼어요"
        elif state == "maintenance" and self.state != "maintenance":
            headline = "Claude 점검 중이에요"
        elif state == "ok" and self.state == "down":
            headline = "Claude 복구됐어요!"
        elif state == "ok" and self.state == "maintenance":
            headline = "점검이 끝났어요"
        else:
            headline = None
        # 숨겨 둬도 장애는 말하지만, 게임 중에는 「최근 알림」에만 남긴다
        if headline and self.game is not None:
            self.history = [(f"{local_now():%H:%M} {headline}", headline, None)] + self.history[:HISTORY_SIZE - 1]
        elif headline:
            self.speak(headline)
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

    # 업데이트: 켜짐 = 받아서 해시 확인 → 한가할 때 교체·재시작, 꺼짐(기본) = 버전마다 한 번 「새 버전이 나왔어요」(누르면 릴리스 페이지)
    def toggle_auto_update(self):
        # pystray 스레드에서 불린다
        self.auto_update = not self.auto_update
        self.root.after(0, lambda: self.save_config(auto_update=self.auto_update))
        self.tray.update_menu()
        if self.auto_update:
            self.root.after(0, self.check_update)

    def poll_update(self):
        self.check_update()
        self.root.after(UPDATE_EVERY_MS, self.poll_update)

    def check_update(self, manual=False):
        if not self.version:
            return
        threading.Thread(target=lambda: self.root.after(0, self.got_release, fetch_release(), manual), daemon=True).start()

    def got_release(self, info, manual):
        latest, mine = parse_version((info or {}).get("tag")), parse_version(self.version)
        if not (latest and mine and latest > mine):
            if manual:
                self.speak(body="업데이트를 확인하지 못했어요" if info is None else f"최신 버전이에요 ({self.version})")
            return
        if self.updating:
            return
        if self.auto_update:
            self.updating = True
            threading.Thread(target=lambda: self.root.after(0, self.downloaded, info, download_update(info, exe_path() + ".new")), daemon=True).start()
            return
        self.notify_update(info, manual)

    def downloaded(self, info, ok):
        if not ok:
            self.updating = False
            self.notify_update(info, True)
            return
        self.apply_update(info)

    def apply_update(self, info):
        if self.closing:
            return
        if self.game is not None or self.bubble is not None or self.press is not None or self.menu_open:
            self.root.after(UPDATE_RETRY_MS, self.apply_update, info)
            return
        exe = exe_path()
        if not swap_exe(exe):
            self.updating = False
            self.notify_update(info, True)
            return
        try:
            launch_updated(exe, info["tag"])
        except OSError:
            # 교체는 됐다: 다음에 켤 때 새 버전으로 뜬다
            self.updating = False
            self.speak(body=f"{info['tag']} 버전을 받아 뒀어요. 다시 켜면 바뀌어요")
            return
        self.closing = True
        self.finish_quit()

    def notify_update(self, info, force):
        # 같은 버전은 한 번만 (force = 지금 확인을 눌렀거나 자동 교체에 실패했을 때)
        tag = info["tag"]
        if not force and (read_config() or {}).get("update_notified") == tag:
            return
        self.save_config(update_notified=tag)
        body = f"새 버전이 나왔어요! ({tag})\n누르면 받는 곳을 열어요"
        self.history = [(f"{local_now():%H:%M} 새 버전 {tag}", body, info.get("page"))] + self.history[:HISTORY_SIZE - 1]
        if self.game is None and not self.closing and self.root.state() != "withdrawn":
            self.speak(body=body, link=info.get("page"))

    def cleanup_update(self):
        # 지난 업데이트가 남긴 옛 exe 와 덜 받은 파일을 치운다
        for path in (exe_path() + ".old", exe_path() + ".new"):
            try:
                os.remove(path)
            except OSError:
                pass

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

    def play_game(self):
        # 이미 열려 있으면 그 창을 앞으로. 게임 중에는 본체를 숨긴다(게임 창 안에 있다)
        if self.game is not None:
            self.game.win.lift()
            self.game.win.focus_force()
            return
        self.stop_eat()
        self.hide_window()
        self.game = Game(self)

    def show_window(self):
        if self.game is not None:  # 트레이 「보이기」: 게임 중이면 게임 창을 앞으로
            self.play_game()
            return
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
    def speak(self, headline=None, body=None, duration=None, link=None, pose=None):
        # body 가 없으면 장애 내용 + 사용량을 말한다. headline 은 그 위 첫 줄. link 가 있으면 말풍선을 누를 때 그 주소를 연다. pose 는 talk 대신 보여 줄 그림
        self.stop_walk()
        self.stop_eat()
        self.ice_frame = None
        self.pose = pose
        self.petting = self.celebrating = False  # 쓰다듬기·생일 한마디 중에 다른 말풍선이 뜨면 pet·birthday 가 남지 않게 푼다
        # 클릭으로 말할 때(body 없음)는 맨 위에 세션 현황(「작업 중 2 · 대기 1」)을 붙인다
        text = body or "\n".join(filter(None, (sessions_line(self.sessions),
                                               usage_speech(self.status, load_accounts(), datetime.datetime.now(datetime.timezone.utc)))))
        if headline:
            text = headline + "\n" + text
        if self.bubble is not None:
            self.bubble.destroy()
        bubble = self.bubble = tk.Toplevel(self.root)
        bubble.overrideredirect(True)
        bubble.attributes("-topmost", True)
        bubble.configure(bg="#3a3a3a", padx=1, pady=1)
        tk.Label(bubble, text=text, bg="white", fg="#222", font=("Segoe UI", 9), justify="left", wraplength=340, padx=10, pady=6,
                 cursor="hand2" if link else "").pack()
        bubble.bind("<ButtonRelease-1>", lambda e: (link and os.startfile(link), self.stop_talking(bubble)))
        bubble.update_idletasks()
        self.place_bubble()
        self.talking = True
        self.show()
        # 타이머는 root 에 건다: 말풍선에 걸면 클릭으로 먼저 닫을 때 destroy 가 콜백까지 지워 talk 에 멈춘다
        outage = self.status is not None and self.status["status"]["indicator"] != "none"
        self.root.after(duration or (OUTAGE_TALK_MS if outage else TALK_MS), self.stop_talking, bubble)

    def place_bubble(self):
        # 클순이 머리 위(넘치면 발밑)에 둔다. 말하는 중에 끌어 옮기면 다시 불러 따라오게 한다
        bubble = self.bubble
        if bubble is None:
            return
        left, top, right, _ = self.work_area()
        width, height = bubble.winfo_reqwidth(), bubble.winfo_reqheight()
        x = max(left, min(self.x + (self.images["talk"].width - width) // 2, right - width))
        y = self.y - height - 4
        if y < top:
            y = self.y + HEIGHT + 4
        bubble.geometry(f"+{x}+{y}")

    def stop_talking(self, bubble):
        bubble.destroy()
        if bubble is self.bubble:
            self.bubble = None
            self.talking = False
            self.petting = self.celebrating = False
            self.ice_frame = None
            self.pose = None
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

    # 식사 주기(햄버거): EAT_SEQUENCE 를 한 번 돈다. 걷던 중이면 멈추고, 먹던 중이면 처음부터. 누르거나 말하면 멈춘다
    def feed(self):
        self.stop_walk()
        self.eating = [0]
        self.show()
        self.root.after(EAT_SEQUENCE[0][1], self.eat_tick, self.eating)

    def eat_tick(self, eating):
        if eating is not self.eating:  # 그 사이 멈췄다
            return
        eating[0] += 1
        if eating[0] == len(EAT_SEQUENCE):
            self.stop_eat()
            return
        self.show()
        if self.shown != EAT_SEQUENCE[eating[0]][0]:  # 장애·점검·피곤 등 먹는 그림보다 앞서는 상태가 됐다
            self.stop_eat()
            return
        self.root.after(EAT_SEQUENCE[eating[0]][1], self.eat_tick, eating)

    def stop_eat(self):
        if self.eating is None:
            return
        self.eating = None
        self.show()

    # 조작: 조금만 움직이고 떼면 클릭(말하기), 그 이상이면 끌기(이동, 뒷덜미를 잡힌 drag 그림)
    def on_press(self, event):
        self.stop_walk()
        self.stop_eat()
        self.last_touch = time.monotonic()
        self.press = (event.x_root, event.y_root)

    def on_drag(self, event):
        if self.press is None:
            return
        sx, sy = self.press
        if not self.dragging:
            if abs(event.x_root - sx) <= CLICK_SLOP and abs(event.y_root - sy) <= CLICK_SLOP:
                return
            self.dragging = True
        image = self.images["drag"]
        self.x = event.x_root - round(image.width * DRAG_ANCHOR[0])
        self.y = event.y_root - round(HEIGHT * DRAG_ANCHOR[1])
        self.root.geometry(f"+{self.x}+{self.y}")
        self.place_bubble()
        self.show()

    def on_release(self, event):
        if self.press is None:
            return
        self.press = None
        if not self.dragging:
            self.speak_clicked()
            return
        self.dragging = False
        left, top, right, bottom = self.work_area()
        self.x = max(left, min(self.x, right - self.images["idle_1"].width))
        self.y = max(top, min(self.y, bottom - HEIGHT))
        self.root.geometry(f"+{self.x}+{self.y}")
        self.place_bubble()
        self.show()
        self.save_config(x=self.x, y=self.y)


kernel32 = ctypes.windll.kernel32
kernel32.CreateMutexW.restype = wt.HANDLE
kernel32.CloseHandle.argtypes = [wt.HANDLE]


def single_instance(name, wait_s):
    # 이름 있는 뮤텍스를 처음 만든 프로세스만 돈다. 잡으면 핸들(프로세스가 끝날 때 풀린다), wait_s 초 안에 못 잡으면 None
    deadline = time.monotonic() + wait_s
    while True:
        handle = kernel32.CreateMutexW(None, False, name)
        if kernel32.GetLastError() != 183:  # ERROR_ALREADY_EXISTS
            return handle
        kernel32.CloseHandle(handle)
        if time.monotonic() >= deadline:
            return None
        time.sleep(0.25)


def main():
    # 이미 떠 있으면 바로 끝낸다. 업데이트로 켜졌으면 옛 프로세스가 아직 끝나는 중일 수 있어 잠깐 기다린다
    if single_instance("Local\\ClaudeStatusMascot", 10 if "--updated" in sys.argv else 0) is None:
        return
    Mascot().root.mainloop()


if __name__ == "__main__":
    main()
