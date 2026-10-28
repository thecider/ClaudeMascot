# Claude Mascot

[한국어](#한국어) · [English](#english)

Windows 바탕화면에 사는 작은 캐릭터가 Claude 서비스 상태와 내 사용량을 알려 줍니다.
A tiny desktop character for Windows that tells you Claude's service status and your usage.

---

## 한국어

### 할 수 있는 것
- **상태 표시**: Claude 장애면 아픈 모습, 점검이면 점검 모습, 사용량이 90% 이상이면 지친 모습으로 바뀝니다. 장애가 나거나 복구되면 스스로 말풍선으로 알려 줍니다.
- **클릭**: 말풍선으로 계정별 5시간·주간 사용량(사용량 브리지 설치 시)과 장애 내용을 보여 줍니다.
- **끌기**: 후드 뒷덜미를 잡혀 들린 채 원하는 곳으로 옮겨집니다. 위치는 기억합니다.
- **쓰다듬기**: 버튼을 누르지 않은 채 머리 위에서 좌우로 문지르면 좋아합니다. 아플 때 쓰다듬으면 가끔 얼음주머니를 갈아 줍니다.
- **걷기**: 가만히 두면 가끔 좌우로 몇 걸음 걷습니다. 클릭하면 멈추고, 오른쪽 클릭 → **걷기** 체크를 풀면 걷지 않습니다.
- **잠들기·인사·생일**: 10분 동안 안 건드리면 잠들고, 아침·점심·저녁에 인사하고, 생일을 축하해 줍니다.
- **트레이 메뉴**: 보이기 / 숨기기 / 캐릭터 / Windows 시작 시 실행 / 완전히 종료

### 설치
1. [Releases](https://github.com/thecider/ClaudeMascot/releases)에서 `ClaudeMascot.exe` 를 받아 아무 폴더에 두고 실행합니다.
   - 서명이 없는 exe 라 「Windows의 PC 보호」 창이 뜰 수 있습니다. **추가 정보 → 실행** 을 누르세요.
2. 로그인할 때 자동으로 켜려면 트레이 아이콘 오른쪽 클릭 → **Windows 시작 시 실행** 을 체크합니다. (exe 를 옮기면 다시 체크하세요)
3. (선택) 사용량까지 보려면 **Claude Code** 에 사용량 브리지 플러그인을 설치합니다. Claude Code 프롬프트에서:
   ```
   /plugin install usage-status-bridge --marketplace thecider/ClaudeMascot
   ```
   마켓플레이스를 추가할지 물으면 `y`, 범위는 원하는 것을 고릅니다. 설치 뒤 Claude Code 세션을 한 번 쓰면 사용량이 나타납니다.
   설치하지 않으면 사용량 없이 상태만 보여 줍니다.

### 캐릭터 바꾸기
1. 트레이 → **캐릭터 → 캐릭터 폴더 열기** (`%USERPROFILE%\.claude\claude-status\characters`)
2. 그 안에 새 폴더(폴더 이름 = 캐릭터 이름)를 만들고 아래 이름의 PNG 를 넣습니다. **투명 배경**, 정사각형(예: 512x512) 권장. 높이 160px 로 맞춰 그립니다.
3. 트레이 → **캐릭터** 에서 고릅니다 (20초 안에 메뉴에 나타납니다).

| 파일 | 언제 |
|---|---|
| `idle_1.png` ~ `idle_4.png` | 평상시 (30초마다 무작위). `idle_1` 의 머리 부분이 트레이 아이콘이 됩니다 |
| `talk.png` | 말할 때 |
| `sick.png` | Claude 장애 |
| `maintenance.png` | 점검 중 |
| `tired.png` | 사용량 90% 이상 |
| `pet.png` | 쓰다듬을 때 |
| `sleep.png` | 10분 동안 안 건드렸을 때 |
| `birthday.png` | 생일 |
| `goodnight.png` | 완전히 종료할 때 |
| `sick_pet.png` | 아플 때 쓰다듬으면 (없으면 그 캐릭터의 `sick.png`) |
| `sick_ice_1.png` ~ `sick_ice_4.png` | 아플 때 쓰다듬으면 가끔 나오는 얼음주머니 애니메이션 (없으면 `sick.png`). 네 장의 캐릭터 위치·크기를 똑같이 |
| `walk_1.png` ~ `walk_4.png` | 오른쪽으로 걷는 4프레임. 왼쪽으로 걸을 땐 좌우를 뒤집어 씁니다 (없으면 그 캐릭터의 `idle_1.png` 로 미끄러지듯 걷습니다) |
| `drag.png` | 끌 때. 후드 뒷덜미를 잡혀 들린 모습(그림 위쪽 가운데가 커서 위치). 없으면 그 캐릭터의 `idle_1.png` |

빠진 파일은 기본 캐릭터 그림으로 채웁니다. 그래서 `idle_1.png` 하나만 넣어도 동작합니다.

### 생일
`%USERPROFILE%\.claude\claude-status\mascot.json` 의 `birthdays` 에 넣습니다:
```json
"birthdays": {"이름": "MM-DD"}
```

### 직접 빌드
Python 3.13 이상에서:
```
pip install pyinstaller pystray pillow
build.bat
```
`dist\ClaudeMascot.exe` 가 만들어집니다. 빌드 없이 실행하려면 `pythonw mascot\claude_mascot.pyw`.

### 알아 둘 것
- Windows 전용입니다.
- 계정 구분은 Claude Code 가 세션에 넘기는 환경변수 `CLAUDE_CODE_USER_EMAIL` 을 씁니다(공식 문서에 없는 값). Claude Code 가 바뀌면 계정 이름이 안 나올 수 있습니다.
- 상태는 [status.claude.com](https://status.claude.com) 공개 API 에서 1분마다 가져옵니다. 토큰이나 대화 내용은 다루지 않습니다.
- 기본 캐릭터 그림은 ChatGPT 로 생성했습니다.

---

## English

### What it does
- **Status**: looks sick during a Claude outage, shows a maintenance pose during maintenance, and looks tired at 90%+ usage. It speaks up on its own when an outage starts or ends.
- **Click**: a speech bubble with per-account 5-hour / weekly usage (with the usage bridge installed) and incident details.
- **Drag**: pick it up by the back of its hood and move it anywhere; the position is remembered.
- **Pet**: rub left and right over its head without pressing a button. Pet it while it's sick and it sometimes gets a fresh ice bag.
- **Walk**: when left alone it sometimes takes a few steps left or right. Click to stop it; uncheck right-click → **걷기** (Walk) to turn walking off.
- **Sleep, greetings, birthdays**: falls asleep after 10 idle minutes, greets you in the morning / at lunch / in the evening, and celebrates birthdays.
- **Tray menu**: Show / Hide / Character / Run at Windows startup / Quit. (The UI text is Korean.)

### Install
1. Download `ClaudeMascot.exe` from [Releases](https://github.com/thecider/ClaudeMascot/releases), put it in any folder and run it.
   - The exe is unsigned, so Windows SmartScreen may warn you. Click **More info → Run anyway**.
2. To start it at login, right-click the tray icon → check **Windows 시작 시 실행** (Run at Windows startup). Re-check it if you move the exe.
3. (Optional) To see usage, install the usage bridge plugin in **Claude Code**. At the Claude Code prompt:
   ```
   /plugin install usage-status-bridge --marketplace thecider/ClaudeMascot
   ```
   Answer `y` to add the marketplace and pick a scope. Usage appears after you use a Claude Code session once.
   Without it, the mascot shows status only.

### Custom characters
1. Tray → **캐릭터 → 캐릭터 폴더 열기** (Character → Open character folder): `%USERPROFILE%\.claude\claude-status\characters`
2. Create a folder there (folder name = character name) and put PNGs with the names in the table above. **Transparent background**, square (e.g. 512x512) recommended; images are scaled to 160 px high.
3. Pick it from Tray → **캐릭터** (it shows up in the menu within 20 seconds).

Missing files fall back to the default character, so even a single `idle_1.png` works. `sick_pet` and `sick_ice_1..4` fall back to that character's own `sick.png`. Keep the character at the same position and size in all four `sick_ice` frames.
`walk_1..4` are a 4-frame walk facing right (mirrored for walking left); without them the character slides using its own `idle_1.png`.
`drag.png` is shown while dragging: the character lifted by the back of its hood (the top center of the image follows the cursor); without it, that character's `idle_1.png` is used.

### Birthdays
Add to `birthdays` in `%USERPROFILE%\.claude\claude-status\mascot.json`:
```json
"birthdays": {"Name": "MM-DD"}
```

### Build it yourself
With Python 3.13+:
```
pip install pyinstaller pystray pillow
build.bat
```
This creates `dist\ClaudeMascot.exe`. To run without building: `pythonw mascot\claude_mascot.pyw`.

### Notes
- Windows only.
- Accounts are told apart with `CLAUDE_CODE_USER_EMAIL`, an undocumented variable Claude Code passes to sessions; account names may stop showing if Claude Code changes it.
- Status is fetched every minute from the public [status.claude.com](https://status.claude.com) API. No tokens or conversation content are touched.
- The default character art was generated with ChatGPT.

## License
MIT
