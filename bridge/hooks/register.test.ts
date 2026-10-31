import { expect, test } from 'claude-code/testing'

const LIMITS = [
  { kind: 'five_hour', percentUsed: 42.5, resetsAt: '2026-10-26T15:00:00Z' },
  { kind: 'seven_day', percentUsed: 12, resetsAt: '2026-10-30T00:00:00Z' },
]

function engine(on: any, written: Array<{ path: string; text: string }>, env: Record<string, string> = {}) {
  const vars: Record<string, string> = { USERPROFILE: 'C:\\Users\\Tester', ...env }
  on('env.get', (_: any, e: any) => ({ value: vars[e.name] }))
  on('session.cwd', () => ({ value: 'F:\\Work\\MyGame' }))
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

const TURN = { answer: '', durationMs: 5000, isAborted: false, turnId: 't1', reason: 'answer' as const }

test('a finished turn tells the mascot the project and the first line of the answer', async ($, on) => {
  const written: Array<{ path: string; text: string }> = []
  engine(on, written)
  on('turn.complete', (_, e) => ({ text: e.answer }))

  await $.turn.complete({ ...TURN, answer: '\n**끌기 기능을 `main`에 커밋했습니다**(1f0bdb6).\n\n세부 내용' })

  expect(written.length).toBe(1)
  expect(written[0].path.replaceAll('\\', '/')).toBe('C:/Users/Tester/.claude/claude-status/notify.json')
  const out = JSON.parse(written[0].text)
  expect(out.project).toBe('MyGame')
  expect(out.text).toBe('끌기 기능을 main에 커밋했습니다(1f0bdb6).')
  expect(typeof out.at).toBe('string')
})

test('a long first line is cut short for the speech bubble', async ($, on) => {
  const written: Array<{ path: string; text: string }> = []
  engine(on, written)
  on('turn.complete', (_, e) => ({ text: e.answer }))

  await $.turn.complete({ ...TURN, answer: '가'.repeat(100) })

  expect(written.length).toBe(1)
  expect(JSON.parse(written[0].text).text).toBe('가'.repeat(40) + '…')
})

test('a subagent, an interrupted or an empty turn tells the mascot nothing', async ($, on) => {
  const written: Array<{ path: string; text: string }> = []
  engine(on, written)
  on('turn.complete', (_, e) => ({ text: e.answer }))

  await $.turn.complete({ ...TURN, answer: '조사 결과', agentId: 'a1' })
  await $.turn.complete({ ...TURN, answer: '중단됨', reason: 'aborted', isAborted: true })
  await $.turn.complete({ ...TURN, answer: '' })

  expect(written.length).toBe(0)
})
