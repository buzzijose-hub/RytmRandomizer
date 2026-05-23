/**
 * Public surface of the cockpit module.
 *
 * Re-exports the top-level `<Cockpit />` and every child component used by tests and the
 * future Tauri shell. Consumers should import from here rather than reaching into
 * individual files.
 */

export { Cockpit } from './Cockpit';
export type { CockpitProps } from './Cockpit';

export { HeaderBar } from './HeaderBar';
export { SnapshotPanel } from './SnapshotPanel';
export type { SnapshotPanelProps } from './SnapshotPanel';
export { PadCard } from './PadCard';
export type { PadCardProps } from './PadCard';
export { HistoryStrip } from './HistoryStrip';
export { MutationPanel } from './MutationPanel';
export type { MutationPanelProps } from './MutationPanel';
export { ProfileToggle } from './ProfileToggle';
export type { ProfileToggleProps } from './ProfileToggle';
export { ProfileChips } from './ProfileChips';
export type { ProfileChipsProps } from './ProfileChips';
export { DepthSlider } from './DepthSlider';
export type { DepthSliderProps } from './DepthSlider';
export { ActionBar } from './ActionBar';
export type { ActionBarProps } from './ActionBar';
export { Knob, valueToAngle } from './Knob';
export type { KnobProps } from './Knob';
export { LockButton } from './LockButton';
export type { LockButtonProps } from './LockButton';

export { CockpitClientProvider, useCockpitClient } from './context';
export type { CockpitClientProviderProps } from './context';
export { usePadLocks } from './usePadLocks';
export type { PadLocksApi } from './usePadLocks';
