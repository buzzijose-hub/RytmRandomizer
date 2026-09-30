import { cleanup, fireEvent, render, screen, within } from '@testing-library/react';

import { TouchDialog } from '../../src/appliance/TouchDialog';
import { TouchNumber } from '../../src/appliance/TouchNumber';

afterEach(cleanup);

describe('touch numeric controls', () => {
  it('clamps both endpoints and stages a value without a hardware keyboard', () => {
    const changed = vi.fn(); render(<TouchNumber label="TEST" value={99} onChange={changed} />);
    fireEvent.click(screen.getByRole('button', { name: 'TEST 99 percent. Adjust' }));
    fireEvent.click(screen.getByRole('button', { name: '+10' })); expect(screen.getByText('100%', { selector: 'output' })).toBeInTheDocument();
    fireEvent.click(screen.getByRole('button', { name: '0%' })); fireEvent.click(screen.getByRole('button', { name: '-10' }));
    expect(screen.getByText('0%', { selector: 'output' })).toBeInTheDocument(); fireEvent.click(screen.getByRole('button', { name: 'SET 0%' })); expect(changed).toHaveBeenCalledWith(0);
  });
  it('cancels through the visible close button and honors disabled input', () => {
    const changed = vi.fn(); const { rerender } = render(<TouchNumber label="TEST" value={25} onChange={changed} />);
    fireEvent.click(screen.getByRole('button', { name: 'TEST 25 percent. Adjust' })); fireEvent.click(screen.getByRole('button', { name: 'Close dialog' })); expect(changed).not.toHaveBeenCalled();
    rerender(<TouchNumber label="TEST" value={25} disabled onChange={changed} />); expect(screen.getByRole('button', { name: 'TEST 25 percent. Adjust' })).toBeDisabled();
  });
  it('traps boundaries while allowing normal tab navigation inside a modal', () => {
    const close = vi.fn(); render(<TouchDialog title="Focus" onClose={close} actions={<button type="button">FOOTER ACTION</button>}><button type="button">FIRST CONTENT</button><button type="button">LAST CONTENT</button></TouchDialog>);
    const dialog = screen.getByRole('dialog'); const first = within(dialog).getByRole('button', { name: 'Close dialog' }); const middle = within(dialog).getByRole('button', { name: 'FIRST CONTENT' });
    middle.focus(); fireEvent.keyDown(dialog, { key: 'Tab', shiftKey: true }); expect(middle).toHaveFocus();
    fireEvent.keyDown(dialog, { key: 'ArrowDown' }); expect(close).not.toHaveBeenCalled();
    first.focus(); fireEvent.keyDown(dialog, { key: 'Tab' }); expect(first).toHaveFocus();
    fireEvent.keyDown(dialog, { key: 'Tab', shiftKey: true }); expect(screen.getByRole('button', { name: 'FOOTER ACTION' })).toHaveFocus();
    fireEvent.keyDown(dialog, { key: 'Tab' }); expect(first).toHaveFocus();
    fireEvent.keyDown(dialog, { key: 'Escape' }); expect(close).toHaveBeenCalledOnce();
  });
  it('supports a content-only dialog without an empty action region', () => {
    render(<TouchDialog title="Information" onClose={vi.fn()}><p>Read-only details</p></TouchDialog>);
    expect(screen.getByRole('dialog')).toHaveTextContent('Read-only details');
    expect(screen.getAllByRole('button')).toHaveLength(1);
  });
});
