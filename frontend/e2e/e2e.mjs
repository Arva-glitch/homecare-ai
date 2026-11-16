// End-to-end UI test: drives the real frontend (Vite) + backend (FastAPI + MySQL) in headless Chrome.
import { chromium } from 'playwright-core'

const BASE = process.env.BASE || 'http://127.0.0.1:5173'
const OUT = process.env.OUT || '/home/claude/e2e/shots'
const browser = await chromium.launch({ executablePath: '/usr/bin/google-chrome', args: ['--no-sandbox'] })
const ctx = await browser.newContext({ viewport: { width: 1440, height: 900 } })
const page = await ctx.newPage()
const errors = []
page.on('console', (m) => { if (m.type() === 'error') errors.push(m.text()) })
page.on('pageerror', (e) => errors.push(String(e)))
page.on('response', (r) => { if (r.url().includes('/api/') && r.status() >= 500) errors.push(`${r.status()} ${r.url()}`) })

const step = async (name, fn) => {
  try { await fn(); console.log('PASS', name) } catch (e) { console.log('FAIL', name, e.message.split('\n')[0]); errors.push(`${name}: ${e.message.split('\n')[0]}`) }
}
const shot = (n) => page.screenshot({ path: `${OUT}/${n}.png`, fullPage: true })

await step('login page + demo login', async () => {
  await page.goto(BASE + '/login')
  await shot('01-login')
  await page.getByText('Fill demo login').click()
  await page.getByRole('button', { name: 'Sign in' }).click()
  await page.waitForSelector('text=Registered appliances', { timeout: 15000 })
  await page.waitForTimeout(1200)
  await shot('02-dashboard')
})

await step('appliances list, search, add with validation', async () => {
  await page.getByRole('link', { name: 'My Appliances' }).click()
  await page.waitForSelector('text=Kitchen Refrigerator')
  await page.getByLabel('Search appliances').fill('samsung')
  await page.waitForTimeout(800)
  const cards = await page.locator('text=Front-Load Washing Machine').count()
  if (!cards) throw new Error('search did not find washing machine')
  await page.getByLabel('Search appliances').fill('')
  await page.waitForTimeout(600)
  await shot('03-appliances')
  await page.getByRole('button', { name: 'Add appliance' }).first().click()
  const dlg = page.getByRole('dialog')
  await dlg.locator('input').first().fill('Study Room AC')
  await dlg.locator('select').first().selectOption('Air Conditioner')
  await dlg.locator('input[type=date]').first().fill('2019-03-01')
  await shot('04-add-appliance')
  await dlg.getByRole('button', { name: 'Add appliance' }).click()
  await page.waitForSelector('text=Study Room AC', { timeout: 10000 })
})

await step('appliance detail + log maintenance', async () => {
  await page.getByText('Kitchen Refrigerator').first().click()
  await page.waitForSelector('text=Maintenance history')
  await page.waitForTimeout(800)
  await shot('05-appliance-detail')
  await page.getByRole('button', { name: 'Log maintenance' }).click()
  const dlg = page.getByRole('dialog')
  await dlg.locator('input[type=number]').fill('500')
  await dlg.getByRole('button', { name: 'Save' }).click()
  await page.waitForSelector('text=Maintenance recorded', { timeout: 10000 })
})

await step('predictions: run all + expand', async () => {
  await page.getByRole('link', { name: 'Predictive Maintenance' }).click()
  await page.waitForSelector('text=How to read these scores')
  await page.getByRole('button', { name: 'Run prediction for all' }).click()
  await page.waitForSelector('text=Re-assessed', { timeout: 15000 })
  await page.locator('button[aria-expanded]').first().click()
  await page.waitForSelector('text=Why this recommendation')
  await page.waitForTimeout(800)
  await shot('06-predictions')
})

await step('scheduler: accept suggestion, create, start, complete', async () => {
  await page.getByRole('link', { name: 'Maintenance Scheduler' }).click()
  await page.waitForSelector('text=Calendar')
  const accept = page.getByRole('button', { name: 'Accept suggestion' })
  if (await accept.count()) { await accept.first().click(); await page.waitForSelector('text=Added for', { timeout: 10000 }) }
  await page.getByRole('button', { name: 'Schedule maintenance' }).click()
  const dlg = page.getByRole('dialog')
  await page.waitForTimeout(500)
  await dlg.locator('select').first().selectOption({ index: 1 })
  await dlg.locator('input[type="datetime-local"]').fill('2030-01-15T11:00')
  await dlg.getByRole('button', { name: 'Schedule', exact: true }).click()
  await page.waitForSelector('text=Maintenance scheduled', { timeout: 10000 })
  await page.getByRole('button', { name: 'Start' }).first().click()
  await page.waitForSelector('text=Marked in progress', { timeout: 10000 })
  await page.getByRole('button', { name: 'Complete' }).first().click()
  await page.getByRole('dialog').getByRole('button', { name: 'Mark completed' }).click()
  await page.waitForSelector('text=Task completed', { timeout: 10000 })
  await page.waitForTimeout(500)
  await shot('07-scheduler')
})

await step('report issue -> AI suggestions -> schedule', async () => {
  await page.getByRole('link', { name: 'Report an Issue' }).click()
  await page.waitForSelector('text=New issue')
  await page.waitForTimeout(600)
  const form = page.locator('form').first()
  await form.locator('select').nth(0).selectOption({ label: 'Bathroom Geyser (Geyser)' })
  await form.locator('select').nth(1).selectOption('Not Heating')
  await form.locator('textarea').fill('Water stays lukewarm even after 40 minutes of heating.')
  await form.locator('select').nth(2).selectOption('High')
  await form.getByRole('button', { name: 'Submit issue' }).click()
  await page.waitForSelector('text=Analysis for Bathroom Geyser', { timeout: 15000 })
  const sch = page.getByRole('button', { name: 'Schedule it' })
  if (await sch.count()) { await sch.click(); await page.waitForSelector('text=Maintenance scheduled (Pending)', { timeout: 10000 }) }
  await shot('08-issues')
})

await step('expenses: add + report', async () => {
  await page.getByRole('link', { name: 'Expenses' }).click()
  await page.waitForSelector('text=Monthly expenditure')
  await page.getByRole('button', { name: 'Add expense' }).click()
  const dlg = page.getByRole('dialog')
  await dlg.locator('input[type=number]').fill('1234')
  await dlg.locator('textarea').fill('E2E test expense')
  await dlg.getByRole('button', { name: 'Save' }).click()
  await page.waitForSelector('text=Expense added', { timeout: 10000 })
  await page.waitForTimeout(800)
  await shot('09-expenses')
})

await step('assistant chat', async () => {
  await page.getByRole('link', { name: 'AI HomeCare Assistant' }).click()
  await page.getByText('Which appliance requires immediate maintenance?').click()
  await page.waitForSelector('text=Rule-based response', { timeout: 15000 })
  await page.getByLabel('Message').fill('Why is my washing machine leaking?')
  await page.getByRole('button', { name: 'Send' }).click()
  await page.waitForFunction(() => document.querySelectorAll('.md').length >= 2, null, { timeout: 15000 })
  await page.waitForTimeout(500)
  await shot('10-assistant')
})

await step('notifications', async () => {
  await page.getByRole('link', { name: /Notifications/ }).click()
  await page.waitForSelector('text=Check for alerts')
  await page.waitForTimeout(600)
  await shot('11-notifications')
  await page.getByRole('button', { name: 'Mark all read' }).click()
  await page.waitForSelector('text=All marked as read', { timeout: 10000 })
})

await step('profile update', async () => {
  await page.getByRole('link', { name: 'Profile' }).click()
  await page.locator('textarea').fill('Indore, MP')
  await page.getByRole('button', { name: 'Save profile' }).click()
  await page.waitForSelector('text=Profile updated', { timeout: 10000 })
  await shot('12-profile')
})

await step('mobile layout', async () => {
  await page.setViewportSize({ width: 390, height: 844 })
  await page.getByRole('button', { name: 'Open menu' }).click()
  await page.waitForTimeout(300)
  await shot('13-mobile-menu')
  await page.getByRole('link', { name: 'Dashboard' }).last().click()
  await page.waitForTimeout(1200)
  await shot('14-mobile-dashboard')
  await page.setViewportSize({ width: 1440, height: 900 })
})

await step('logout with confirmation', async () => {
  await page.getByRole('button', { name: 'Logout' }).click()
  await page.getByRole('dialog').getByRole('button', { name: 'Log out' }).click()
  await page.waitForSelector('text=Sign in', { timeout: 10000 })
})

await step('forgot password flow', async () => {
  await page.goto(BASE + '/forgot-password')
  await page.locator('input[type=email]').fill('priya@homecare.ai')
  await page.getByRole('button', { name: 'Send reset link' }).click()
  await page.getByRole('link', { name: 'Open reset link' }).click()
  const pw = page.locator('input[type=password]')
  await pw.nth(0).fill('Demo@1234')
  await pw.nth(1).fill('Demo@1234')
  await page.getByRole('button', { name: 'Reset password' }).click()
  await page.waitForSelector('text=Password reset', { timeout: 10000 })
})

await browser.close()
const relevant = errors.filter((e) => !e.includes('favicon'))
console.log(`\nErrors: ${relevant.length}`)
relevant.forEach((e) => console.log(' -', e))
process.exit(relevant.length ? 1 : 0)
