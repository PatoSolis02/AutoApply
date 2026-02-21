import { describe, expect, it } from 'vitest';
import { errorMessageForStatus } from './api';

describe('api error message mapping', () => {
  it('maps 409 to transition conflict message', () => {
    expect(errorMessageForStatus(409)).toContain('allowed application lifecycle');
  });

  it('maps 422 to compliance block message', () => {
    expect(errorMessageForStatus(422)).toContain('blocked by compliance checks');
  });

  it('falls back for other statuses', () => {
    expect(errorMessageForStatus(500)).toContain('Something went wrong');
  });
});
