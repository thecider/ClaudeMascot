import { expect, test } from 'claude-code/testing'

const LIMITS = [
  { kind: 'five_hour', percentUsed: 42.5, resetsAt: '2026-10-26T15:00:00Z' },
  { kind: 'seven_day', percentUsed: 12, resetsAt: '2026-10-30T00:00:00Z' },
]

function engine(on: any, written: Array<{ path: string; text: string }>, env: Record<string, string> = {}) {
  const vars: Record<string, string> = { USERPROFILE: 'C:\\Users\\Tester', ...env }
  on('env.get', (_: any, e: any) => ({ value: vars[e.name] }))
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
