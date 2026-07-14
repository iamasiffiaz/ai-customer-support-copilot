import { chromium } from 'playwright'
import { mkdir } from 'node:fs/promises'
import path from 'node:path'
import { fileURLToPath } from 'node:url'

const __dirname = path.dirname(fileURLToPath(import.meta.url))
const outDir = path.resolve(__dirname, '../docs/screenshots')
const base = process.env.APP_URL || 'http://127.0.0.1:5180'

const shots = [
  { file: '01-landing.png', url: '/', fullPage: true },
  { file: '02-dashboard.png', url: '/dashboard', fullPage: true },
  { file: '03-tickets.png', url: '/tickets', fullPage: true },
  { file: '04-ticket-detail.png', url: null, fullPage: true },
  { file: '05-knowledge-base.png', url: '/knowledge-base', fullPage: true },
  { file: '06-copilot.png', url: '/copilot', fullPage: true },
]

await mkdir(outDir, { recursive: true })

const browser = await chromium.launch({ headless: true })
const page = await browser.newPage({
  viewport: { width: 1440, height: 900 },
  deviceScaleFactor: 1,
})

async function settle() {
  await page.waitForLoadState('networkidle').catch(() => {})
  await page.waitForTimeout(1200)
}

await page.goto(`${base}/`, { waitUntil: 'domcontentloaded', timeout: 60000 })
await settle()
await page.screenshot({ path: path.join(outDir, shots[0].file), fullPage: shots[0].fullPage })

for (const shot of shots.slice(1)) {
  if (shot.file === '04-ticket-detail.png') {
    await page.goto(`${base}/tickets`, { waitUntil: 'domcontentloaded', timeout: 60000 })
    await settle()
    const link = page.locator('a[href^="/tickets/"]').first()
    if (await link.count()) {
      await link.click()
      await settle()
    } else {
      await page.goto(`${base}/tickets/1`, { waitUntil: 'domcontentloaded', timeout: 60000 })
      await settle()
    }
  } else {
    await page.goto(`${base}${shot.url}`, { waitUntil: 'domcontentloaded', timeout: 60000 })
    await settle()
  }
  await page.screenshot({ path: path.join(outDir, shot.file), fullPage: shot.fullPage })
  console.log('saved', shot.file)
}

await browser.close()
console.log('done', outDir)
