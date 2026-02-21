import { describe, expect, it } from 'vitest';
import { getAllowedTargets, toStatusLabel } from './status';

describe('status utilities', () => {
  it('returns expected contract transitions', () => {
    expect(getAllowedTargets('captured')).toEqual(['drafting', 'rejected']);
    expect(getAllowedTargets('offer')).toEqual([]);
  });

  it('renders a human-friendly label', () => {
    expect(toStatusLabel('ready_to_apply')).toBe('Ready To Apply');
  });
});
