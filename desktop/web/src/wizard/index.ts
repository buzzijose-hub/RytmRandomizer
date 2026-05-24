/**
 * Public surface of the wizard module.
 *
 * Re-exports the top-level `<Wizard />` + every step component (used by tests and the
 * future Tauri shell) and the related types.
 */

export { Wizard } from './Wizard';
export type { WizardProps } from './Wizard';

export { WizardSteps } from './WizardSteps';
export type { WizardStepsProps } from './WizardSteps';

export { NameStep } from './NameStep';
export type { NameStepProps } from './NameStep';

export { AddStep } from './AddStep';
export type { AddStepProps } from './AddStep';

export { AnalyzeStep } from './AnalyzeStep';
export type { AnalyzeStepProps } from './AnalyzeStep';

export { ReviewStep } from './ReviewStep';
export type { ReviewStepProps } from './ReviewStep';
