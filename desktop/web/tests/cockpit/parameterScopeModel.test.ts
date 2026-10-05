import { describe, expect, it } from 'vitest';

import { explicitParameterSelection, parameterBlockers, parameterCellKey, parameterSelected, replaceParameterCells, selectableParameter } from '../../src/cockpit/parameterScopeModel';
import { parameterControls, scopeControl } from './parameterScopeFixture';

describe('canonical parameter scope presentation', () => {
  it('preserves exact machine-specific identities without translating their values', () => {
    expect(parameterCellKey(parameterControls[8]!)).toBe('1:src_bd_hard_decay');
    expect(parameterCellKey(parameterControls[9]!)).toBe('11:src_cy_ride_tail');
    expect(explicitParameterSelection(null, [parameterControls[10]!])).toEqual([{ item_id: 1, parameter_key: 'filter1_frequency' }]);
    expect(parameterControls[10]!.value).toBe(16256);
  });
  it('distinguishes legacy all, explicit none and an exact cell selection', () => {
    const control = scopeControl();
    expect(parameterSelected(null, control)).toBe(true);
    expect(parameterSelected([], control)).toBe(false);
    expect(parameterSelected([{ item_id: 1, parameter_key: 'flt' }, { item_id: 2, parameter_key: 'amp_decay' }], control)).toBe(false);
    expect(parameterSelected([{ item_id: 2, parameter_key: 'flt' }], control)).toBe(true);
    expect(explicitParameterSelection([], [control])).toEqual([]);
  });
  it('excludes unsupported, protected and missing values from explicit all', () => {
    const eligible = parameterControls.filter(selectableParameter);
    expect(eligible).toHaveLength(7);
    expect(explicitParameterSelection(null, parameterControls)).toHaveLength(7);
  });
  it('adds/removes only requested eligible cells while retaining other pads and pages', () => {
    const controls = [scopeControl(), scopeControl({ item_id: 1, parameter_key: 'amp_decay' }), scopeControl({ parameter_key: 'pitch', protected: true })];
    expect(replaceParameterCells(null, controls, [controls[0]!], false)).toEqual([{ item_id: 1, parameter_key: 'amp_decay' }]);
    expect(replaceParameterCells([], controls, controls, true)).toEqual([{ item_id: 1, parameter_key: 'amp_decay' }, { item_id: 2, parameter_key: 'flt' }]);
    expect(replaceParameterCells([{ item_id: 2, parameter_key: 'flt' }], controls, [controls[0]!], true)).toEqual([{ item_id: 2, parameter_key: 'flt' }]);
  });
  it('names policy and source blockers without treating live blocking as offline protection', () => {
    expect(parameterBlockers(scopeControl({ protected: true, mutation_supported: false, value: null, reasons: ['saved_offset_unverified', 'saved_offset_unverified'] }), true, false)).toEqual([
      'Pad or track not targeted', 'Pad or track locked', 'Offline mutation unsupported', 'Source value unavailable', 'Mandatory protection', 'saved offset unverified',
    ]);
    expect(parameterBlockers(scopeControl(), false, true)).toEqual([]);
    expect(selectableParameter(parameterControls[7]!)).toBe(true);
  });
});
