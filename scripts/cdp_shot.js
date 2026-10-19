// CDP 真时截图：导航后真实等待 N 秒再截图（验证实时动画）
const port = 9223
const waitMs = Number(process.argv[2] || 8000)
const url = process.argv[3] || 'http://localhost:7100/'
const out = process.argv[4] || 'cdp_shot.png'

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
  throw new Error('no debug target')
}

;(async () => {
  const ws = new WebSocket(await getWsUrl())
  let id = 0
  const pending = new Map()
  const send = (method, params = {}) =>
    new Promise((resolve, reject) => {
      const mid = ++id
      pending.set(mid, { resolve, reject })
      ws.send(JSON.stringify({ id: mid, method, params }))
    })
  ws.onmessage = (e) => {
    const msg = JSON.parse(e.data)
    if (msg.id && pending.has(msg.id)) {
      pending.get(msg.id).resolve(msg.result)
      pending.delete(msg.id)
    }
  }
  await new Promise((r) => (ws.onopen = r))
  await send('Page.enable')
  await send('Page.navigate', { url })
  await sleep(waitMs)
  const shot = await send('Page.captureScreenshot', { format: 'png' })
  require('fs').writeFileSync(out, Buffer.from(shot.data, 'base64'))
  console.log('saved', out)
  ws.close()
  proc.kill()
  process.exit(0)
})().catch((e) => { console.error(e); proc.kill(); process.exit(1) })
