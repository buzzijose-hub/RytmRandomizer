/**
 * LiveRegion — the single global aria-live container. Mount once at
 * App.tsx root; the announcer module writes into it via the registered
 * callback.
 *
 * `aria-live="polite"` queues announcements rather than interrupting
 * the user mid-action. `aria-atomic="true"` ensures the WHOLE region
 * content is read on every change (vs. just the diff), which avoids
 * stuttering announcements when the message changes rapidly.
 */

import { useEffect, useState } from 'react';

import { _registerWriter } from './announcer';

import './srOnly.css';

export function LiveRegion(): JSX.Element {
  const [text, setText] = useState<string>('');

  useEffect(() => {
    _registerWriter(setText);
    return () => _registerWriter(null);
  }, []);

  return (
    <div
      role="status"
      aria-live="polite"
      aria-atomic="true"
      className="sr-only"
      data-testid="a11y-live-region"
    >
      {text}
    </div>
  );
}
