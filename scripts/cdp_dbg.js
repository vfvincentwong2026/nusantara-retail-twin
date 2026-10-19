// CDP 探针：检查演示台自动优化状态
const port = 9226
const { spawn } = require('child_process')
const edge = 'C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe'
const proc = spawn(edge, ['--headless','--disable-gpu','--use-angle=swiftshader','--enable-unsafe-swiftshader',`--remote-debugging-port=${port}`,`--user-data-dir=${require('os').tmpdir()}/cdp-${Date.now()}`,'--window-size=1440,900','about:blank'], { stdio: 'ignore' })
const sleep = (ms) => new Promise((r) => setTimeout(r, ms))
;(async () => {
  let wsUrl
  for (let i = 0; i < 30 && !wsUrl; i++) {
    try { const l = await (await fetch(`http://127.0.0.1:${port}/json/list`)).json(); wsUrl = l.find(t => t.type === 'page')?.webSocketDebuggerUrl } catch {}
    if (!wsUrl) await sleep(300)
  }
  const ws = new WebSocket(wsUrl)
  let id = 0; const pending = new Map()
  const send = (m, p = {}) => new Promise((res) => { const i = ++id; pending.set(i, res); ws.send(JSON.stringify({ id: i, method: m, params: p })) })
  ws.onmessage = (e) => { const m = JSON.parse(e.data); if (m.id && pending.has(m.id)) { pending.get(m.id)(m.result); pending.delete(m.id) } }
  await new Promise((r) => (ws.onopen = r))
  await send('Page.enable'); await send('Runtime.enable')
  await send('Page.navigate', { url: process.argv[2] || 'http://localhost:7100/?demo=1&auto=1' })
  await sleep(Number(process.argv[3] || 20000))
  const r = await send('Runtime.evaluate', { expression: `JSON.stringify({
    dashActive: [...document.querySelectorAll('button')].find(b=>b.textContent.includes('经营大屏'))?.className.includes('bg-foreground'),
    undoVisible: [...document.querySelectorAll('button')].some(b=>b.textContent.includes('撤销优化')),
    deltaBar: document.body.innerText.includes('本次调整对全店日毛利影响'),
    autoParam: new URLSearchParams(location.search).get('auto'),
    demoOpt: window.__demoOpt || 'none',
  })`, returnByValue: true })
  console.log(r.result.value)
  ws.close(); proc.kill(); process.exit(0)
})().catch((e) => { console.error(e); proc.kill(); process.exit(1) })
