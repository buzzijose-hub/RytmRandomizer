/**
 * Tests for the WizardSteps indicator.
 */

import { describe, expect, it } from 'vitest';
import { render, screen } from '@testing-library/react';

import { WizardSteps } from '../../src/wizard/WizardSteps';
import type { WizardStep } from '../../src/types/wizard_protocol';

describe('WizardSteps', () => {
  it('renders all four steps with the active step highlighted', () => {
    render(<WizardSteps active="add" />);
    expect(screen.getByTestId('wizard-steps')).toBeInTheDocument();
    expect(screen.getByTestId('wizard-step-name')).toHaveAttribute('data-step-state', 'done');
    expect(screen.getByTestId('wizard-step-add')).toHaveAttribute('data-step-state', 'active');
    expect(screen.getByTestId('wizard-step-analyze')).toHaveAttribute('data-step-state', 'upcoming');
    expect(screen.getByTestId('wizard-step-review')).toHaveAttribute('data-step-state', 'upcoming');
  });

  it('marks "name" active when the first step is active (no done steps)', () => {
    render(<WizardSteps active="name" />);
    expect(screen.getByTestId('wizard-step-name')).toHaveAttribute('data-step-state', 'active');
    expect(screen.getByTestId('wizard-step-add')).toHaveAttribute('data-step-state', 'upcoming');
  });

  it('marks every earlier step as done when on the last step', () => {
    render(<WizardSteps active="review" />);
    expect(screen.getByTestId('wizard-step-name')).toHaveAttribute('data-step-state', 'done');
    expect(screen.getByTestId('wizard-step-add')).toHaveAttribute('data-step-state', 'done');
    expect(screen.getByTestId('wizard-step-analyze')).toHaveAttribute('data-step-state', 'done');
    expect(screen.getByTestId('wizard-step-review')).toHaveAttribute('data-step-state', 'active');
  });

  it('exposes aria-current="step" on the active step', () => {
    render(<WizardSteps active="analyze" />);
    expect(screen.getByTestId('wizard-step-analyze')).toHaveAttribute('aria-current', 'step');
    expect(screen.getByTestId('wizard-step-name')).not.toHaveAttribute('aria-current');
  });

  it('falls back to step index 1 when an unknown step is passed (defensive)', () => {
    // This exercises the `?? 1` branch in the active-index lookup. Cast through unknown
    // because TS would otherwise reject the bogus value.
    render(<WizardSteps active={'mystery' as unknown as WizardStep} />);
    // With activeIndex=1, name is active and all others upcoming.
    expect(screen.getByTestId('wizard-step-name')).toHaveAttribute('data-step-state', 'active');
    expect(screen.getByTestId('wizard-step-add')).toHaveAttribute('data-step-state', 'upcoming');
  });
});
