// CDP 检查：导航后等待 N 毫秒，输出页面内脉冲/SMIL/模拟状态
const port = 9224
const waitMs = Number(process.argv[2] || 6000)
const url = process.argv[3] || 'http://localhost:7100/'

const { spawn } = require('child_process')
const edge = 'C:\\Program Files (x86)\\Microsoft\\Edge\\Application\\msedge.exe'
const proc = spawn(edge, [
  '--headless', '--disable-gpu', '--use-angle=swiftshader', '--enable-unsafe-swiftshader',
  `--remote-debugging-port=${port}`, `--user-data-dir=${require('os').tmpdir()}\\cdp-${Date.now()}`,
  '--window-size=1440,900', 'about:blank',
], { stdio: 'ignore' })
const sleep = (ms) => new Promise((r) => setTimeout(r, ms))

async function getWsUrl() {
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
  const ws = new WebSocket(await getWsUrl())
  let id = 0
  const pending = new Map()
  const send = (method, params = {}) =>
    new Promise((resolve) => {
      const mid = ++id
      pending.set(mid, resolve)
      ws.send(JSON.stringify({ id: mid, method, params }))
    })
  ws.onmessage = (e) => {
    const msg = JSON.parse(e.data)
    if (msg.id && pending.has(msg.id)) { pending.get(msg.id)(msg.result); pending.delete(msg.id) }
  }
  await new Promise((r) => (ws.onopen = r))
  await send('Page.enable')
  await send('Runtime.enable')
  await send('Page.navigate', { url })
  await sleep(waitMs)
  const expr = `JSON.stringify({
    animates: document.querySelectorAll('animate').length,
    circles: [...document.querySelectorAll('circle')].map(c => ({r: c.getAttribute('r'), op: c.style.opacity, cx: c.getAttribute('cx')})).slice(0,5),
    pulseTexts: [...document.querySelectorAll('text')].filter(t => t.textContent.startsWith('+')).map(t => ({txt: t.textContent, op: t.getAttribute('opacity') || t.style.opacity})),
  })`
  const res = await send('Runtime.evaluate', { expression: expr, returnByValue: true })
  console.log(res.result.value)
  ws.close(); proc.kill(); process.exit(0)
})().catch((e) => { console.error(e); proc.kill(); process.exit(1) })
