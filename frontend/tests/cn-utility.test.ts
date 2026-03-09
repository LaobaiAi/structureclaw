import { describe, it, expect } from 'vitest'
import { cn } from '@/lib/utils'

describe('cn() Utility (DSGN-04)', () => {
  it('should merge simple class names', () => {
    expect(cn('foo', 'bar')).toBe('foo bar')
  })

  it('should handle conditional classes with falsy values', () => {
    expect(cn('foo', false && 'bar', 'baz')).toBe('foo baz')
    expect(cn('foo', null, 'bar', undefined)).toBe('foo bar')
    expect(cn('foo', '', 'bar')).toBe('foo bar')
  })

  it('should merge conflicting Tailwind classes (last wins)', () => {
    // tailwind-merge resolves conflicts
    expect(cn('p-4', 'p-2')).toBe('p-2')
    expect(cn('text-red-500', 'text-blue-500')).toBe('text-blue-500')
    expect(cn('bg-white', 'bg-black')).toBe('bg-black')
  })

  it('should handle arrays of class names', () => {
    expect(cn(['foo', 'bar'], 'baz')).toBe('foo bar baz')
  })

  it('should handle objects with boolean values', () => {
    expect(cn({ foo: true, bar: false, baz: true })).toBe('foo baz')
  })

  it('should handle mixed input types', () => {
    expect(cn('foo', ['bar', 'baz'], { qux: true })).toBe('foo bar baz qux')
  })

  it('should return empty string for no inputs', () => {
    expect(cn()).toBe('')
  })

  it('should handle complex Tailwind class merging', () => {
    // Test real-world scenario: variant classes
    const result = cn(
      'inline-flex items-center justify-center rounded-md',
      'bg-primary text-primary-foreground',
      'hover:bg-primary/90',
      false && 'disabled-classes',
      'h-10 px-4'
    )
    expect(result).toContain('bg-primary')
    expect(result).toContain('hover:bg-primary/90')
    expect(result).not.toContain('disabled-classes')
  })
})
