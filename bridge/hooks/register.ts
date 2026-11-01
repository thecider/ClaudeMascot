// ClaudeStatus 브리지: 사용량이 움직일 때마다 5시간·주간 사용률과 현재 로그인 계정을
// ~/.claude/claude-status/usage-<계정>.json 에 쓴다. 턴이 끝나거나 사람의 답을 기다리면 notify.json(종류·프로젝트·한 줄·세션)도 쓴다.
// 데스크톱 마스코트(mascot/claude_mascot.pyw)가 이 파일들을 읽는다.
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

// 말풍선에 넣을 한 줄: 답변 첫 줄에서 마크다운 기호를 빼고 NOTIFY_CHARS 자로 자른다
const NOTIFY_CHARS = 40

function firstLine(answer: string): string {
  const line = answer.split('\n').map((l) => l.trim()).find((l) => l) ?? ''
  const plain = line.replace(/^(#+|[-*>]|\d+\.)\s+/, '').replace(/\*\*|`/g, '')
  const chars = Array.from(plain)
  return chars.length > NOTIFY_CHARS ? chars.slice(0, NOTIFY_CHARS).join('') + '…' : plain
}

// 권한 확인 알림 문구(「Claude needs your permission to use <도구>」)에서 말풍선 한 줄을 만든다. 질문(AskUserQuestion)도 이 알림으로 온다
function waitingLine(message: string): string {
  const tool = /use (\S+)$/.exec(message.trim())?.[1]
  if (tool === 'AskUserQuestion') return '질문에 답해 주세요'
  return tool ? `${tool} 사용 허락이 필요해요` : message
}

// ~/.claude/claude-status/notify.json 에 쓴다. 마스코트가 보고 말풍선을 띄운다
// kind: done = 턴이 끝남(「작업 완료」), waiting = 사람의 답(권한 확인·질문)을 기다림(「확인이 필요해요」)
// session: Desktop 앱 세션 ID(local_…, 환경변수 CLAUDE_CODE_HOST_SESSION_ID). 말풍선을 누르면 마스코트가 이 세션을 연다. CLI 세션은 null
async function writeNotify($: any, kind: 'done' | 'waiting', text: string): Promise<void> {
  const root = await home($)
  const project = (await $.session.cwd()).split(/[\\/]/).filter(Boolean).pop() ?? ''
  const session = (await $.env.get('CLAUDE_CODE_HOST_SESSION_ID')) || null
  const out = { at: new Date().toISOString(), kind, project, text, session }
  await $.fs.write(`${root}/.claude/claude-status/notify.json`, JSON.stringify(out, null, 1))
}

export const register: Register = (on) => {
  on('turn.complete', async ($, e, next) => {
    const result = await next(e)
    // 메인 대화가 답하고 끝난 턴만: 서브에이전트·중단·오류·빈 답변은 알리지 않는다
    if (e.agentId === undefined && e.reason === 'answer' && e.answer.trim()) {
      try {
        await writeNotify($, 'done', firstLine(e.answer))
      } catch {
        // 무시
      }
    }
    return result
  })
  // 권한 확인·질문이 몇 초 넘게 답을 못 받으면 오는 알림. auto 모드가 스스로 허락한 도구에는 오지 않는다(2026-11-01 Desktop 세션 실측)
  on('classic.Notification', async ($, e, next) => {
    if (e.notification_type === 'permission_prompt') {
      try {
        await writeNotify($, 'waiting', waitingLine(e.message))
      } catch {
        // 무시
      }
    }
    return next(e)
  })
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
