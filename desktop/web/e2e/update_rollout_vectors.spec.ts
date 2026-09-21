import { createHash } from 'node:crypto';
import { expect, test } from '@playwright/test';

test('native rollout vectors straddle the strict ten percent boundary', () => {
  const bucket = (id: string): number => createHash('sha256').update(id).digest().readUInt32BE(0) % 100;
  expect(bucket('00000000-0000-4000-8000-000000000015')).toBe(9);
  expect(bucket('00000000-0000-4000-8000-000000000119')).toBe(10);
  expect(bucket('00000000-0000-4000-8000-000000000016')).toBe(11);
});
