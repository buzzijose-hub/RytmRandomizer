const assert = require('node:assert/strict');
const { test } = require('node:test');
const { assertExactPad2Plan, assertPlanDeadline, freshBootstrapReceived } = require('../e2e/fixtures/plan_inspection_package_journey.cjs');

const candidate = {
  candidate_id: 'candidate-fixture',
  pad_deltas: [{ pad_id: 2, changed_keys: ['flt', 'amp_decay'], proposed_params: { flt: 127, amp_decay: 0 } }],
};
const plan = {
  ready: true,
  candidate_id: candidate.candidate_id,
  blocked_reasons: [],
  packets: [
    { pad_id: 2, parameter: 'amp_decay', channel: 1, control: 80, value: 0 },
    { pad_id: 2, parameter: 'flt', channel: 1, control: 74, value: 127 },
  ],
};

test('actual packaged phase deadline refuses expired and invalid budgets before later work', () => {
  assertPlanDeadline(1000, 1, 1999);
  assert.throws(() => assertPlanDeadline(1000, 1, 2000), assert.AssertionError);
  for (const budget of [0, -1, 601, NaN]) {
    assert.throws(() => assertPlanDeadline(1000, budget, 1001), assert.AssertionError);
  }
});

test('replacement bootstrap requires fresh status and completion from the same new socket', () => {
  assert.equal(freshBootstrapReceived({}, 'old'), false);
  assert.equal(freshBootstrapReceived({ session_status_socket: 'old', bootstrap_socket: 'old' }, 'old'), false);
  assert.equal(freshBootstrapReceived({ session_status_socket: 'new' }, 'old'), false);
  assert.equal(freshBootstrapReceived({ session_status_socket: 'new', bootstrap_socket: 'old' }, 'old'), false);
  assert.equal(freshBootstrapReceived({ session_status_socket: 'new', bootstrap_socket: 'new' }, 'old'), true);
});

test('actual packaged plan verifier requires the complete ordered candidate packet list', () => {
  assert.deepEqual(assertExactPad2Plan(plan, candidate), plan.packets);
  for (const packets of [[], plan.packets.slice(0, 1), [plan.packets[0], plan.packets[0]], [...plan.packets].reverse()]) {
    assert.throws(() => assertExactPad2Plan({ ...plan, packets }, candidate), assert.AssertionError);
  }
});

test('actual packaged plan verifier rejects stale blocked and wrong destination plans', () => {
  for (const invalid of [
    { ...plan, ready: false },
    { ...plan, candidate_id: 'stale-candidate' },
    { ...plan, blocked_reasons: ['paired_control_precision_unverified'] },
    { ...plan, packets: plan.packets.map(packet => ({ ...packet, channel: 2 })) },
    { ...plan, packets: plan.packets.map(packet => ({ ...packet, value: 64 })) },
  ]) assert.throws(() => assertExactPad2Plan(invalid, candidate), assert.AssertionError);
});

test('actual packaged plan verifier rejects out-of-scope controls pads and fractional values', () => {
  for (const invalid of [
    { ...candidate, pad_deltas: [] },
    { ...candidate, pad_deltas: [{ ...candidate.pad_deltas[0], pad_id: 1 }] },
    { ...candidate, pad_deltas: [{ pad_id: 2, changed_keys: ['lfo_depth'], proposed_params: { lfo_depth: 64 } }] },
    { ...candidate, pad_deltas: [{ pad_id: 2, changed_keys: ['flt'], proposed_params: { flt: 0.5 } }] },
  ]) assert.throws(() => assertExactPad2Plan(plan, invalid), assert.AssertionError);
});
