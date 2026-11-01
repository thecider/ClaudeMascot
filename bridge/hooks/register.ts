// ClaudeStatus 브리지: 사용량이 움직일 때마다 5시간·주간 사용률과 현재 로그인 계정을
// ~/.claude/claude-status/usage-<계정>.json 에 쓴다. 작업 알림(완료·대기·실패)은 notify.json, 세션마다 지금 상태(작업 중·대기·끝)는 sessions/<세션>.json 에 쓴다.
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

// 이 세션의 데이터 폴더·프로젝트 이름(작업 폴더 이름)·Desktop 앱 세션 ID(local_…, 환경변수 CLAUDE_CODE_HOST_SESSION_ID. CLI 세션은 null)
async function where($: any): Promise<{ dir: string; project: string; session: string | null }> {
  const dir = `${await home($)}/.claude/claude-status`
  const project = (await $.session.cwd()).split(/[\\/]/).filter(Boolean).pop() ?? ''
  const session = (await $.env.get('CLAUDE_CODE_HOST_SESSION_ID')) || null
  return { dir, project, session }
}

// ~/.claude/claude-status/notify.json 에 쓴다. 마스코트가 보고 말풍선을 띄운다
// kind: done = 턴이 끝남(「작업 완료」), waiting = 사람의 답(권한 확인·질문)을 기다림(「확인이 필요해요」), failed = 턴이 오류로 끝남(「작업이 실패했어요」)
// session 이 있으면 말풍선을 누를 때 마스코트가 그 세션을 연다
async function writeNotify($: any, kind: 'done' | 'waiting' | 'failed', text: string): Promise<void> {
  const { dir, project, session } = await where($)
  const out = { at: new Date().toISOString(), kind, project, text, session }
  await $.fs.write(`${dir}/notify.json`, JSON.stringify(out, null, 1))
}

// ~/.claude/claude-status/sessions/<세션>.json 에 이 세션의 지금 상태를 쓴다. 마스코트가 모아 작업 중 그림·세션 현황을 보여 준다
// state: working = 메인 대화 턴이 도는 중, waiting = 사람의 답을 기다림, idle = 턴이 끝남, ended = 세션이 끝남(마스코트가 파일을 지운다)
// 파일을 지우는 API 가 없어 끝난 세션도 ended 로 남긴다
async function writeSession($: any, state: 'working' | 'waiting' | 'idle' | 'ended', id?: string): Promise<void> {
  try {
    const { dir, project, session } = await where($)
    const out = { at: new Date().toISOString(), state, project, session }
    await $.fs.write(`${dir}/sessions/${(id ?? (await $.session.id())).replace(/[^\w.-]/g, '_')}.json`, JSON.stringify(out, null, 1))
  } catch {
    // 파일을 못 써도 세션은 그대로 간다
  }
}

export const register: Register = (on) => {
  // 세션 상태는 메인 대화 턴만 본다: 서브에이전트 턴은 메인 턴 안에서 돌아 그 시작·끝이 세션 상태를 바꾸지 않는다
  on('turn.start', async ($, e, next) => {
    if (e.agentId === undefined) await writeSession($, 'working')
    return next(e)
  })
  // 도구가 끝날 때마다 working 으로 되돌린다: 권한 확인·질문(waiting)에 답이 오면 도구가 돌고 끝난다. 긴 턴이 살아 있다는 표시도 된다
  on('tool.call', async ($, e, next) => {
    const result = await next(e)
    await writeSession($, 'working')
    return result
  })
  on('turn.complete', async ($, e, next) => {
    const result = await next(e)
    if (e.agentId !== undefined) return result
    await writeSession($, 'idle')
    // 답하고 끝난 턴은 「작업 완료」, 오류로 끝난 턴은 「실패」. 중단·빈 답변은 알리지 않는다
    try {
      if (e.reason === 'answer' && e.answer.trim()) await writeNotify($, 'done', firstLine(e.answer))
      else if (e.reason === 'error') await writeNotify($, 'failed', firstLine(e.answer))
    } catch {
      // 무시
    }
    return result
  })
  on('session.end', async ($, e, next) => {
    await writeSession($, 'ended', e.sessionId)
    return next(e)
  })
  // 권한 확인·질문이 몇 초 넘게 답을 못 받으면 오는 알림. auto 모드가 스스로 허락한 도구에는 오지 않는다(2026-11-01 Desktop 세션 실측)
  on('classic.Notification', async ($, e, next) => {
    if (e.notification_type === 'permission_prompt') {
      await writeSession($, 'waiting')
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
