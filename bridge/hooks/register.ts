// ClaudeStatus 브리지: 사용량이 움직일 때마다 5시간·주간 사용률과 현재 로그인 계정을
// ~/.claude/claude-status/usage-<계정>.json 에 쓴다. 데스크톱 마스코트(mascot/claude_mascot.pyw)가 이 파일들을 읽는다.
// 토큰은 다루지 않는다. 계정은 환경변수 CLAUDE_CODE_USER_EMAIL(Desktop 세션), 없으면 ~/.claude.json 의 oauthAccount.emailAddress 를 읽는다.
import type { Register, SessionRateLimit } from 'claude-code'

async function home($: any): Promise<string> {
  return (await $.env.get('USERPROFILE')) || (await $.env.get('HOME')) || ''
}

async function readAccount($: any, root: string): Promise<string | null> {
  // Desktop 앱이 띄운 세션은 앱의 로그인 계정으로 돈다: .claude.json(CLI 로그인)과 다를 수 있어 이 값을 먼저 본다
  const sessionEmail = await $.env.get('CLAUDE_CODE_USER_EMAIL')
  if (sessionEmail) return sessionEmail
  try {
    const config = JSON.parse(await $.fs.read(`${root}/.claude.json`))
    return config?.oauthAccount?.emailAddress ?? null
  } catch {
    return null
  }
}

async function writeUsage($: any, limits: SessionRateLimit[]): Promise<void> {
  const windows: Record<string, { percent: number; resetsAt: string | null }> = {}
  for (const w of limits ?? []) {
    windows[w.kind] = { percent: w.percentUsed, resetsAt: w.resetsAt ?? null }
  }
  // 첫 응답 전에는 값이 없다: 빈 값으로 이전 기록을 덮지 않는다
  if (Object.keys(windows).length === 0) return
  const root = await home($)
  const account = await readAccount($, root)
  const out = { updatedAt: new Date().toISOString(), account, windows }
  // 계정마다 파일을 따로 쓴다: 한 파일을 같이 쓰면 마지막에 응답한 계정 값이 다른 계정 값을 덮는다
  const name = (account ?? 'unknown').replace(/[^\w.@-]/g, '_')
  await $.fs.write(`${root}/.claude/claude-status/usage-${name}.json`, JSON.stringify(out, null, 1))
}

export const register: Register = (on) => {
  on('session.start', async ($, e, next) => {
    try {
      const usage = await $.session.usage()
      await writeUsage($, usage.rateLimits)
    } catch {
      // 파일을 못 써도 세션은 그대로 간다
    }
    return next(e)
  })
  on('session.measure', async ($, e, next) => {
    if (e.changed.includes('rateLimits')) {
      try {
        await writeUsage($, e.rateLimits)
      } catch {
        // 무시
      }
    }
    return next(e)
  })
}
