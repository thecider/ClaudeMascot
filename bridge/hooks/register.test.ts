import { expect, test } from 'claude-code/testing'

const LIMITS = [
  { kind: 'five_hour', percentUsed: 42.5, resetsAt: '2026-10-26T15:00:00Z' },
  { kind: 'seven_day', percentUsed: 12, resetsAt: '2026-10-30T00:00:00Z' },
]

function engine(on: any, written: Array<{ path: string; text: string }>, env: Record<string, string> = {}) {
  const vars: Record<string, string> = { USERPROFILE: 'C:\\Users\\Tester', ...env }
  on('env.get', (_: any, e: any) => ({ value: vars[e.name] }))
  on('session.cwd', () => ({ value: 'F:\\Work\\MyGame' }))
  on('session.id', () => ({ value: 'b78fb4d3-c411-45df-9979-191f34278741' }))
  on('fs.read', () => ({ value: JSON.stringify({ oauthAccount: { emailAddress: 'tester@example.com' } }) }))
  on('fs.write', (_: any, e: any) => {
    written.push({ path: e.path, text: e.text })
    return { value: undefined }
  })
  return vars
}

test('a rate-limit measurement writes usage and the account', async ($, on) => {
  const written: Array<{ path: string; text: string }> = []
  engine(on, written)
  on('session.measure', (_, e) => ({ changed: e.changed }))

  await $.session.measure({ context: { window: 200000 } as any, rateLimits: LIMITS, changed: ['rateLimits'] })

  expect(written.length).toBe(1)
  expect(written[0].path.replaceAll('\\', '/')).toBe('C:/Users/Tester/.claude/claude-status/usage-tester@example.com.json')
  const out = JSON.parse(written[0].text)
  expect(out.account).toBe('tester@example.com')
  expect(out.windows.five_hour.percent).toBe(42.5)
  expect(out.windows.seven_day.resetsAt).toBe('2026-10-30T00:00:00Z')
})

test('a measurement without rate limits leaves the file alone', async ($, on) => {
  const written: Array<{ path: string; text: string }> = []
  engine(on, written)
  on('session.measure', (_, e) => ({ changed: e.changed }))

  await $.session.measure({ context: { window: 200000 } as any, rateLimits: [], changed: ['context'] })

  expect(written.length).toBe(0)
})

test('a Desktop session labels the usage with its own account, not the CLI login', async ($, on) => {
  const written: Array<{ path: string; text: string }> = []
  engine(on, written, { CLAUDE_CODE_USER_EMAIL: 'desktop@example.com' })
  on('session.measure', (_, e) => ({ changed: e.changed }))

  await $.session.measure({ context: { window: 200000 } as any, rateLimits: LIMITS, changed: ['rateLimits'] })

  expect(JSON.parse(written[0].text).account).toBe('desktop@example.com')
})

test('each account writes its own file, so one account never overwrites another', async ($, on) => {
  const written: Array<{ path: string; text: string }> = []
  const vars = engine(on, written, { CLAUDE_CODE_USER_EMAIL: 'personal@example.com' })
  on('session.measure', (_, e) => ({ changed: e.changed }))

  await $.session.measure({ context: { window: 200000 } as any, rateLimits: LIMITS, changed: ['rateLimits'] })
  delete vars.CLAUDE_CODE_USER_EMAIL
  await $.session.measure({ context: { window: 200000 } as any, rateLimits: LIMITS, changed: ['rateLimits'] })

  expect(written.map((w) => w.path.replaceAll('\\', '/').split('/').pop())).toEqual([
    'usage-personal@example.com.json',
    'usage-tester@example.com.json',
  ])
})

// 작업 알림 파일(notify.json)에 쓴 것만: 세션 상태 파일(sessions/)도 같이 써진다
function notes(written: Array<{ path: string; text: string }>) {
  return written.filter((w) => w.path.endsWith('notify.json'))
}

const TURN = { answer: '', durationMs: 5000, isAborted: false, turnId: 't1', reason: 'answer' as const }

test('a finished turn tells the mascot the project and the first line of the answer', async ($, on) => {
  const written: Array<{ path: string; text: string }> = []
  engine(on, written)
  on('turn.complete', (_, e) => ({ text: e.answer }))

  await $.turn.complete({ ...TURN, answer: '\n**끌기 기능을 `main`에 커밋했습니다**(1f0bdb6).\n\n세부 내용' })

  expect(notes(written).length).toBe(1)
  expect(notes(written)[0].path.replaceAll('\\', '/')).toBe('C:/Users/Tester/.claude/claude-status/notify.json')
  const out = JSON.parse(notes(written)[0].text)
  expect(out.project).toBe('MyGame')
  expect(out.text).toBe('끌기 기능을 main에 커밋했습니다(1f0bdb6).')
  expect(typeof out.at).toBe('string')
  expect(out.session).toBe(null)
  expect(out.kind).toBe('done')
})

const DESKTOP = { CLAUDE_CODE_HOST_SESSION_ID: 'local_68b6aad6-d739-4e95-9871-21cf43a7acb3' }

test('a question waiting for the person tells the mascot to come and answer', async ($, on) => {
  const written: Array<{ path: string; text: string }> = []
  engine(on, written, DESKTOP)
  on('classic.Notification', () => ({}))

  await $.classic.Notification({ message: 'Claude needs your permission to use AskUserQuestion', notification_type: 'permission_prompt' })

  expect(notes(written).length).toBe(1)
  const out = JSON.parse(notes(written)[0].text)
  expect(out.kind).toBe('waiting')
  expect(out.project).toBe('MyGame')
  expect(out.text).toBe('질문에 답해 주세요')
  expect(out.session).toBe(DESKTOP.CLAUDE_CODE_HOST_SESSION_ID)
})

test('a permission prompt names the tool waiting for a yes', async ($, on) => {
  const written: Array<{ path: string; text: string }> = []
  engine(on, written)
  on('classic.Notification', () => ({}))

  await $.classic.Notification({ message: 'Claude needs your permission to use Bash', notification_type: 'permission_prompt' })

  expect(notes(written).length).toBe(1)
  expect(JSON.parse(notes(written)[0].text).text).toBe('Bash 사용 허락이 필요해요')
})

test('other notifications tell the mascot nothing', async ($, on) => {
  const written: Array<{ path: string; text: string }> = []
  engine(on, written)
  on('classic.Notification', () => ({}))

  await $.classic.Notification({ message: 'Claude is waiting for your input', notification_type: 'idle_prompt' })

  expect(notes(written).length).toBe(0)
})

test('a Desktop session leaves its session id so the bubble can open it', async ($, on) => {
  const written: Array<{ path: string; text: string }> = []
  engine(on, written, { CLAUDE_CODE_HOST_SESSION_ID: 'local_68b6aad6-d739-4e95-9871-21cf43a7acb3' })
  on('turn.complete', (_, e) => ({ text: e.answer }))

  await $.turn.complete({ ...TURN, answer: '완료' })

  expect(notes(written).length).toBe(1)
  expect(JSON.parse(notes(written)[0].text).session).toBe('local_68b6aad6-d739-4e95-9871-21cf43a7acb3')
})

test('a long first line is cut short for the speech bubble', async ($, on) => {
  const written: Array<{ path: string; text: string }> = []
  engine(on, written)
  on('turn.complete', (_, e) => ({ text: e.answer }))

  await $.turn.complete({ ...TURN, answer: '가'.repeat(100) })

  expect(notes(written).length).toBe(1)
  expect(JSON.parse(notes(written)[0].text).text).toBe('가'.repeat(40) + '…')
})

test('a subagent, an interrupted or an empty turn tells the mascot nothing', async ($, on) => {
  const written: Array<{ path: string; text: string }> = []
  engine(on, written)
  on('turn.complete', (_, e) => ({ text: e.answer }))

  await $.turn.complete({ ...TURN, answer: '조사 결과', agentId: 'a1' })
  await $.turn.complete({ ...TURN, answer: '중단됨', reason: 'aborted', isAborted: true })
  await $.turn.complete({ ...TURN, answer: '' })

  expect(notes(written).length).toBe(0)
})

// 세션 상태 파일: sessions/<세션>.json 의 state
function sessionStates(written: Array<{ path: string; text: string }>): string[] {
  return written.filter((w) => w.path.replaceAll('\\', '/').includes('/claude-status/sessions/')).map((w) => JSON.parse(w.text).state)
}

test('a turn marks the session working, then idle when it answers', async ($, on) => {
  const written: Array<{ path: string; text: string }> = []
  engine(on, written, DESKTOP)
  on('turn.start', (_, e) => ({ turnId: e.turnId }))
  on('turn.complete', (_, e) => ({ text: e.answer }))

  await $.turn.start({ text: '해줘', turnId: 't1' })
  await $.turn.complete({ ...TURN, answer: '완료' })

  expect(sessionStates(written)).toEqual(['working', 'idle'])
  const file = written.find((w) => w.path.includes('sessions'))!
  expect(file.path.replaceAll('\\', '/')).toMatch(/\/\.claude\/claude-status\/sessions\/[^/]+\.json$/)
  const out = JSON.parse(file.text)
  expect(out.project).toBe('MyGame')
  expect(out.session).toBe(DESKTOP.CLAUDE_CODE_HOST_SESSION_ID)
})

test('a subagent turn leaves the session state alone', async ($, on) => {
  const written: Array<{ path: string; text: string }> = []
  engine(on, written)
  on('turn.start', (_, e) => ({ turnId: e.turnId }))
  on('turn.complete', (_, e) => ({ text: e.answer }))

  await $.turn.start({ text: '조사', turnId: 't2', agentId: 'a1' })
  await $.turn.complete({ ...TURN, answer: '결과', agentId: 'a1' })

  expect(sessionStates(written)).toEqual([])
})

test('waiting for the person marks the session waiting', async ($, on) => {
  const written: Array<{ path: string; text: string }> = []
  engine(on, written)
  on('classic.Notification', () => ({}))

  await $.classic.Notification({ message: 'Claude needs your permission to use Bash', notification_type: 'permission_prompt' })

  expect(sessionStates(written)).toEqual(['waiting'])
})

test('a turn that ends in an error tells the mascot it failed', async ($, on) => {
  const written: Array<{ path: string; text: string }> = []
  engine(on, written)
  on('turn.complete', (_, e) => ({ text: e.answer }))

  await $.turn.complete({ ...TURN, answer: 'API Error: overloaded', reason: 'error' } as any)

  const note = written.find((w) => w.path.endsWith('notify.json'))
  expect(note).toBeDefined()
  expect(JSON.parse(note!.text).kind).toBe('failed')
  expect(JSON.parse(note!.text).text).toBe('API Error: overloaded')
  expect(sessionStates(written)).toEqual(['idle'])
})

test('the end of a session marks it ended', async ($, on) => {
  const written: Array<{ path: string; text: string }> = []
  engine(on, written)
  on('session.end', (_, e) => ({ sessionId: e.sessionId }))

  await $.session.end({ reason: 'other', sessionId: 's1', resume: {} } as any)

  expect(sessionStates(written)).toEqual(['ended'])
})
