import { clean, daysUntil, healthColor, inr, RISK_COLORS } from '../utils/format'

describe('format utils', () => {
  it('formats rupees', () => { expect(inr(1234)).toContain('1,234') })
  it('maps health score to risk colour', () => {
    expect(healthColor(90)).toBe(RISK_COLORS.Low)
    expect(healthColor(60)).toBe(RISK_COLORS.Medium)
    expect(healthColor(40)).toBe(RISK_COLORS.High)
    expect(healthColor(10)).toBe(RISK_COLORS.Critical)
  })
  it('converts empty strings to null', () => { expect(clean({ a: '', b: 'x' })).toEqual({ a: null, b: 'x' }) })
  it('computes days until a date', () => {
    const d = new Date(); d.setDate(d.getDate() + 5)
    const iso = new Date(d.getTime() - d.getTimezoneOffset() * 60000).toISOString().slice(0, 10)
    expect(daysUntil(iso)).toBe(5)
  })
})
