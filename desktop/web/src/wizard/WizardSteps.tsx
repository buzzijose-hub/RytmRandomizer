/**
 * WizardSteps — top step indicator: Name · Add · Analyze · Review.
 *
 * Pure presentational. Highlights the active step and dims previous/upcoming steps.
 * The container drives the active step; this component does not navigate on click.
 */

import type { WizardStep } from '../types/wizard_protocol';

export interface WizardStepsProps {
  active: WizardStep;
}

interface StepDescriptor {
  id: WizardStep;
  label: string;
  index: number;
}

const STEP_ORDER: ReadonlyArray<StepDescriptor> = [
  { id: 'name', label: 'Name', index: 1 },
  { id: 'add', label: 'Add', index: 2 },
  { id: 'analyze', label: 'Analyze', index: 3 },
  { id: 'review', label: 'Review', index: 4 },
];

export function WizardSteps({ active }: WizardStepsProps): JSX.Element {
  const activeIndex = STEP_ORDER.find((s) => s.id === active)?.index ?? 1;
  return (
    <nav className="wizard-steps" data-testid="wizard-steps" aria-label="Wizard steps">
      {STEP_ORDER.map((step) => {
        const stateClass =
          step.index < activeIndex
            ? 'wizard-step done'
            : step.index === activeIndex
              ? 'wizard-step active'
              : 'wizard-step';
        return (
          <div
            key={step.id}
            className={stateClass}
            data-testid={`wizard-step-${step.id}`}
            data-step-state={
              step.index < activeIndex ? 'done' : step.index === activeIndex ? 'active' : 'upcoming'
            }
            aria-current={step.id === active ? 'step' : undefined}
          >
            <span className="wizard-step-index">{step.index}</span>
            <span className="wizard-step-label">{step.label}</span>
          </div>
        );
      })}
    </nav>
  );
}
