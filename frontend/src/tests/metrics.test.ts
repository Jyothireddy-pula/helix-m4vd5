/**
 * Unit tests for frontend metric formatting and utility logic.
 */
import { describe, it, expect } from 'vitest'

// ---------------------------------------------------------------------------
// Helpers duplicated from component logic (tested in isolation)
// ---------------------------------------------------------------------------

function fmtMW(v: number | null | undefined): string {
  if (v === null || v === undefined) return '—'
  return v.toLocaleString('en-GB', { maximumFractionDigits: 0 }) + ' MW'
}

function fmtPct(v: number | null | undefined): string {
  if (v === null || v === undefined) return '—'
  return v.toFixed(1) + '%'
}

function signedLabel(v: number | null | undefined): string {
  if (v === null || v === undefined) return '—'
  return (v > 0 ? '+' : '') + v.toFixed(0) + ' MW'
}

function leadTimeLabel(hours: number | null | undefined): string {
  if (hours === null || hours === undefined) return '—'
  return `${hours.toFixed(1)}h`
}

function isoToDisplay(iso: string): string {
  // Converts "2026-01-15T12:00:00+00:00" → "15 Jan 2026 12:00 UTC"
  const d = new Date(iso)
  return d.toUTCString().replace(':00 GMT', ' UTC').replace(/ \d\d:\d\d/, m => m)
}

// ---------------------------------------------------------------------------
// Tests
// ---------------------------------------------------------------------------

describe('fmtMW', () => {
  it('formats a positive number', () => {
    expect(fmtMW(1984)).toContain('MW')
    expect(fmtMW(1984)).toContain('1')
  })
  it('returns em-dash for null', () => {
    expect(fmtMW(null)).toBe('—')
  })
  it('returns em-dash for undefined', () => {
    expect(fmtMW(undefined)).toBe('—')
  })
  it('formats zero', () => {
    expect(fmtMW(0)).toBe('0 MW')
  })
})

describe('fmtPct', () => {
  it('formats a percentage to one decimal', () => {
    expect(fmtPct(100)).toBe('100.0%')
    expect(fmtPct(16.7)).toBe('16.7%')
  })
  it('returns em-dash for null', () => {
    expect(fmtPct(null)).toBe('—')
  })
})

describe('signedLabel', () => {
  it('prefixes positive values with +', () => {
    expect(signedLabel(1817)).toBe('+1817 MW')
  })
  it('does not prefix negative values', () => {
    expect(signedLabel(-500)).toBe('-500 MW')
  })
  it('returns em-dash for null', () => {
    expect(signedLabel(null)).toBe('—')
  })
  it('handles zero', () => {
    expect(signedLabel(0)).toBe('0 MW')
  })
})

describe('leadTimeLabel', () => {
  it('formats lead time with one decimal', () => {
    expect(leadTimeLabel(20.5)).toBe('20.5h')
    expect(leadTimeLabel(0)).toBe('0.0h')
  })
  it('returns em-dash for null', () => {
    expect(leadTimeLabel(null)).toBe('—')
  })
})

describe('forecast eligibility rule', () => {
  // Mirrors the backend rule: eligible if publishTime <= cutoff
  function isEligible(publishIso: string, cutoffIso: string): boolean {
    return new Date(publishIso) <= new Date(cutoffIso)
  }

  it('marks forecast published before cutoff as eligible', () => {
    expect(isEligible('2026-01-14T15:30:00Z', '2026-01-14T16:00:00Z')).toBe(true)
  })
  it('marks forecast published exactly at cutoff as eligible', () => {
    expect(isEligible('2026-01-14T16:00:00Z', '2026-01-14T16:00:00Z')).toBe(true)
  })
  it('marks forecast published after cutoff as ineligible', () => {
    expect(isEligible('2026-01-14T18:30:00Z', '2026-01-14T16:00:00Z')).toBe(false)
  })
  it('handles same-day delivery: cutoff is day-1 16:00', () => {
    // Delivery Jan 15, cutoff Jan 14 16:00
    const cutoff = '2026-01-14T16:00:00Z'
    expect(isEligible('2026-01-13T22:30:00Z', cutoff)).toBe(true)
    expect(isEligible('2026-01-14T22:30:00Z', cutoff)).toBe(false)
  })
})

describe('decision cutoff computation', () => {
  // Mirrors backend compute_decision_cutoff logic
  function computeCutoff(deliveryIso: string, cutoffHour = 16): Date {
    const delivery = new Date(deliveryIso)
    const deliveryDate = new Date(Date.UTC(
      delivery.getUTCFullYear(),
      delivery.getUTCMonth(),
      delivery.getUTCDate(),
    ))
    const dayBefore = new Date(deliveryDate)
    dayBefore.setUTCDate(dayBefore.getUTCDate() - 1)
    dayBefore.setUTCHours(cutoffHour, 0, 0, 0)
    return dayBefore
  }

  it('cutoff for Jan 15 delivery is Jan 14 16:00', () => {
    const c = computeCutoff('2026-01-15T12:00:00Z')
    expect(c.toISOString()).toBe('2026-01-14T16:00:00.000Z')
  })
  it('cutoff for Jan 1 delivery is Dec 31 16:00', () => {
    const c = computeCutoff('2026-01-01T00:30:00Z')
    expect(c.toISOString()).toBe('2025-12-31T16:00:00.000Z')
  })
  it('cutoff for Jan 31 delivery is Jan 30 16:00', () => {
    const c = computeCutoff('2026-01-31T23:30:00Z')
    expect(c.toISOString()).toBe('2026-01-30T16:00:00.000Z')
  })
  it('respects a non-default cutoff hour', () => {
    const c = computeCutoff('2026-01-15T00:00:00Z', 12)
    expect(c.toISOString()).toBe('2026-01-14T12:00:00.000Z')
  })
})
