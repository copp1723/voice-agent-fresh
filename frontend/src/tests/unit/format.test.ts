import { describe, it, expect } from 'vitest'
import {
  formatDuration,
  formatPhoneNumber,
  formatPercent,
  formatNumber,
  truncateText,
} from '@utils/format'

describe('Format Utilities', () => {
  describe('formatDuration', () => {
    it('formats seconds correctly', () => {
      expect(formatDuration(45)).toBe('45s')
      expect(formatDuration(59)).toBe('59s')
    })

    it('formats minutes correctly', () => {
      expect(formatDuration(60)).toBe('1m')
      expect(formatDuration(90)).toBe('1m 30s')
      expect(formatDuration(120)).toBe('2m')
    })

    it('formats hours correctly', () => {
      expect(formatDuration(3600)).toBe('1h')
      expect(formatDuration(3660)).toBe('1h 1m')
      expect(formatDuration(7200)).toBe('2h')
    })
  })

  describe('formatPhoneNumber', () => {
    it('formats 10-digit US numbers', () => {
      expect(formatPhoneNumber('1234567890')).toBe('(123) 456-7890')
      expect(formatPhoneNumber('9876543210')).toBe('(987) 654-3210')
    })

    it('formats 11-digit US numbers with country code', () => {
      expect(formatPhoneNumber('11234567890')).toBe('+1 (123) 456-7890')
    })

    it('returns original for non-standard formats', () => {
      expect(formatPhoneNumber('123')).toBe('123')
      expect(formatPhoneNumber('+44123456789')).toBe('+44123456789')
    })
  })

  describe('formatPercent', () => {
    it('formats percentages correctly', () => {
      expect(formatPercent(50)).toBe('50.0%')
      expect(formatPercent(99.9)).toBe('99.9%')
      expect(formatPercent(100, 0)).toBe('100%')
    })
  })

  describe('formatNumber', () => {
    it('formats numbers with correct decimals', () => {
      expect(formatNumber(1000)).toBe('1,000')
      expect(formatNumber(1234.567, 2)).toBe('1,234.57')
      expect(formatNumber(1000000)).toBe('1,000,000')
    })
  })

  describe('truncateText', () => {
    it('truncates long text', () => {
      const longText = 'This is a very long text that needs to be truncated'
      expect(truncateText(longText, 20)).toBe('This is a very lo...')
    })

    it('does not truncate short text', () => {
      const shortText = 'Short text'
      expect(truncateText(shortText, 20)).toBe('Short text')
    })

    it('uses custom suffix', () => {
      const text = 'Custom suffix test'
      expect(truncateText(text, 10, '…')).toBe('Custom su…')
    })
  })
})