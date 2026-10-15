import type { ParameterCell, PerformanceParameterControl } from '../ws/protocol';

export function parameterCellKey(cell: ParameterCell): string {
  return `${cell.item_id}:${cell.parameter_key}`;
}

export function selectableParameter(control: PerformanceParameterControl): boolean {
  return control.mutation_supported && !control.protected && control.value !== null;
}

export function parameterSelected(
  selection: readonly ParameterCell[] | null,
  control: PerformanceParameterControl,
): boolean {
  return selection === null || selection.some((cell) => parameterCellKey(cell) === parameterCellKey(control));
}

/** Materialize legacy-all from canonical supported source cells, never guessed rows. */
export function explicitParameterSelection(
  selection: readonly ParameterCell[] | null,
  controls: readonly PerformanceParameterControl[],
): ParameterCell[] {
  return selection === null
    ? controls.filter(selectableParameter).map(({ item_id, parameter_key }) => ({ item_id, parameter_key }))
    : [...selection];
}

export function replaceParameterCells(
  selection: readonly ParameterCell[] | null,
  controls: readonly PerformanceParameterControl[],
  changed: readonly PerformanceParameterControl[],
  selected: boolean,
): ParameterCell[] {
  const next = new Map(explicitParameterSelection(selection, controls).map((cell) => [parameterCellKey(cell), cell]));
  for (const control of changed.filter(selectableParameter)) {
    const cell = { item_id: control.item_id, parameter_key: control.parameter_key };
    if (selected) next.set(parameterCellKey(cell), cell);
    else next.delete(parameterCellKey(cell));
  }
  return [...next.values()].sort((a, b) => a.item_id - b.item_id || a.parameter_key.localeCompare(b.parameter_key));
}

export function parameterBlockers(control: PerformanceParameterControl, locked: boolean, targeted: boolean): string[] {
  const reasons = control.reasons.map((reason) => reason.replaceAll('_', ' '));
  if (control.protected) reasons.unshift('Mandatory protection');
  if (control.value === null) reasons.unshift('Source value unavailable');
  if (!control.mutation_supported) reasons.unshift('Offline mutation unsupported');
  if (locked) reasons.unshift('Pad or track locked');
  if (!targeted) reasons.unshift('Pad or track not targeted');
  return [...new Set(reasons)];
}
