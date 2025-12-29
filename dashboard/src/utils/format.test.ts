/**
 * Tests for format utilities
 */

import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import {
  formatBytes,
  formatTimeAgo,
  formatDate,
  formatDuration,
  formatNumber,
  formatPercent,
  formatSize,
  formatFileSize,
} from './format';

describe('formatBytes', () => {
  it('handles zero bytes', () => {
    expect(formatBytes(0)).toBe('0 B');
  });

  it('formats bytes', () => {
    expect(formatBytes(500)).toBe('500 B');
    expect(formatBytes(1023)).toBe('1023 B');
  });

  it('formats kilobytes', () => {
    expect(formatBytes(1024)).toBe('1.0 KB');
    expect(formatBytes(1536)).toBe('1.5 KB');
    expect(formatBytes(10240)).toBe('10.0 KB');
  });

  it('formats megabytes', () => {
    expect(formatBytes(1048576)).toBe('1.0 MB');
    expect(formatBytes(5242880)).toBe('5.0 MB');
  });

  it('formats gigabytes', () => {
    expect(formatBytes(1073741824)).toBe('1.0 GB');
    expect(formatBytes(2147483648)).toBe('2.0 GB');
  });

  // formatSize and formatFileSize are aliases
  it('has working aliases', () => {
    expect(formatSize(1024)).toBe(formatBytes(1024));
    expect(formatFileSize(1048576)).toBe(formatBytes(1048576));
  });
});

describe('formatTimeAgo', () => {
  beforeEach(() => {
    vi.useFakeTimers();
    vi.setSystemTime(new Date('2025-01-15T12:00:00Z'));
  });

  afterEach(() => {
    vi.useRealTimers();
  });

  it('handles just now', () => {
    const now = new Date().toISOString();
    expect(formatTimeAgo(now)).toBe('just now');
  });

  it('handles seconds ago', () => {
    const thirtySecsAgo = new Date(Date.now() - 30 * 1000).toISOString();
    expect(formatTimeAgo(thirtySecsAgo)).toBe('just now');
  });

  it('handles minutes ago', () => {
    const fiveMinsAgo = new Date(Date.now() - 5 * 60 * 1000).toISOString();
    expect(formatTimeAgo(fiveMinsAgo)).toBe('5m ago');

    const oneMinAgo = new Date(Date.now() - 60 * 1000).toISOString();
    expect(formatTimeAgo(oneMinAgo)).toBe('1m ago');
  });

  it('handles hours ago', () => {
    const twoHoursAgo = new Date(Date.now() - 2 * 60 * 60 * 1000).toISOString();
    expect(formatTimeAgo(twoHoursAgo)).toBe('2h ago');

    const oneHourAgo = new Date(Date.now() - 60 * 60 * 1000).toISOString();
    expect(formatTimeAgo(oneHourAgo)).toBe('1h ago');
  });

  it('handles days ago', () => {
    const threeDaysAgo = new Date(Date.now() - 3 * 24 * 60 * 60 * 1000).toISOString();
    expect(formatTimeAgo(threeDaysAgo)).toBe('3d ago');

    const oneDayAgo = new Date(Date.now() - 24 * 60 * 60 * 1000).toISOString();
    expect(formatTimeAgo(oneDayAgo)).toBe('1d ago');
  });

  it('returns date string for old dates (>7 days)', () => {
    // For dates older than 7 days, returns localized date string
    const twoWeeksAgo = new Date(Date.now() - 14 * 24 * 60 * 60 * 1000).toISOString();
    const result = formatTimeAgo(twoWeeksAgo);
    // Should be a date string, not a relative time
    expect(result).not.toContain('ago');
  });
});

describe('formatDate', () => {
  it('formats date with default options', () => {
    const result = formatDate('2025-01-15T12:30:00Z');
    // Default format includes month and day (and time)
    expect(result).toContain('Jan');
    expect(result).toContain('15');
  });

  it('formats date with custom options', () => {
    const result = formatDate('2025-01-15T12:30:00Z', {
      year: 'numeric',
      month: 'long',
      day: 'numeric',
    });
    expect(result).toContain('January');
    expect(result).toContain('2025');
  });
});

describe('formatDuration', () => {
  it('formats seconds only', () => {
    expect(formatDuration(45)).toBe('0:45');
    expect(formatDuration(5)).toBe('0:05');
  });

  it('formats minutes and seconds', () => {
    expect(formatDuration(125)).toBe('2:05');
    expect(formatDuration(600)).toBe('10:00');
  });

  it('formats hours, minutes and seconds', () => {
    expect(formatDuration(3661)).toBe('1:01:01');
    expect(formatDuration(7200)).toBe('2:00:00');
  });

  it('handles zero', () => {
    expect(formatDuration(0)).toBe('0:00');
  });
});

describe('formatNumber', () => {
  it('formats integers', () => {
    expect(formatNumber(1000)).toBe('1,000');
    expect(formatNumber(1000000)).toBe('1,000,000');
  });

  it('handles small numbers', () => {
    expect(formatNumber(5)).toBe('5');
    expect(formatNumber(42)).toBe('42');
  });

  it('handles zero', () => {
    expect(formatNumber(0)).toBe('0');
  });
});

describe('formatPercent', () => {
  it('formats raw percentages (0-100 range)', () => {
    // When isDecimal=false (default), value is already a percentage
    expect(formatPercent(75)).toBe('75.0%');
    expect(formatPercent(50)).toBe('50.0%');
  });

  it('formats decimal values as percentages', () => {
    // When isDecimal=true, multiply by 100
    expect(formatPercent(0.75, true)).toBe('75.0%');
    expect(formatPercent(0.5, true)).toBe('50.0%');
  });

  it('handles edge cases', () => {
    expect(formatPercent(0)).toBe('0.0%');
    expect(formatPercent(100)).toBe('100.0%');
    expect(formatPercent(0, true)).toBe('0.0%');
    expect(formatPercent(1, true)).toBe('100.0%');
  });
});
