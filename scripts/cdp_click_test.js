// CDP 交互测试：点击大屏优化按钮 → 验证撤销按钮出现 → 再点撤销 → 验证还原
const port = 9225
const { spawn } = require('child_process')
const edge = 'C:\\Program Files (x86)\\Microsoft\\Edge\\Application\\msedge.exe'
const proc = spawn(edge, [
  '--headless', '--disable-gpu', '--use-angle=swiftshader', '--enable-unsafe-swiftshader',
  `--remote-debugging-port=${port}`, `--user-data-dir=${require('os').tmpdir()}\\cdp-${Date.now()}`,
  '--window-size=1440,900', 'about:blank',
], { stdio: 'ignore' })
const sleep = (ms) => new Promise((r) => setTimeout(r, ms))

async function getWs() {
  for (let i = 0; i < 30; i++) {
    try {
      const list = await (await fetch(`http://127.0.0.1:${port}/json/list`)).json()
      const page = list.find((t) => t.type === 'page')
      if (page) return page.webSocketDebuggerUrl
    } catch {}
    await sleep(300)
  }
  throw new Error('no target')
}

;(async () => {
  const ws = new WebSocket(await getWs())
  let id = 0
  const pending = new Map()
  const send = (m, p = {}) => new Promise((res) => { const i = ++id; pending.set(i, res); ws.send(JSON.stringify({ id: i, method: m, params: p })) })
  ws.onmessage = (e) => { const m = JSON.parse(e.data); if (m.id && pending.has(m.id)) { pending.get(m.id)(m.result); pending.delete(m.id) } }
  await new Promise((r) => (ws.onopen = r))
  await send('Page.enable'); await send('Runtime.enable')
  await send('Page.navigate', { url: 'http://localhost:7100/?view=dash' })
  await sleep(3500)
  const click = (label) => send('Runtime.evaluate', { expression:
    `[...document.querySelectorAll('button')].find(b => b.textContent.includes('${label}'))?.click() ?? 'NOT_FOUND'`, returnByValue: true })
  const r1 = await click('一键智能优化')
  await sleep(700)
  const state1 = await send('Runtime.evaluate', { expression:
    `JSON.stringify({ undoBtn: [...document.querySelectorAll('button')].some(b => b.textContent.includes('撤销优化')), deltaBar: document.body.innerText.includes('本次调整对全店日毛利影响') })`, returnByValue: true })
  const r2 = await click('撤销优化')
  await sleep(700)
  const state2 = await send('Runtime.evaluate', { expression:
    `JSON.stringify({ optBtn: [...document.querySelectorAll('button')].some(b => b.textContent.includes('一键智能优化')), deltaBar: document.body.innerText.includes('本次调整对全店日毛利影响') })`, returnByValue: true })
  console.log('click1:', r1.result.value, '| after apply:', state1.result.value)
  console.log('click2:', r2.result.value, '| after undo:', state2.result.value)
  ws.close(); proc.kill(); process.exit(0)
})().catch((e) => { console.error(e); proc.kill(); process.exit(1) })
