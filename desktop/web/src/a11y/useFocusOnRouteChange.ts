/**
 * useFocusOnRouteChange — moves focus to a ref'd element each time the
 * dependency (typically the hash route) changes.
 *
 * SR users get the route's heading announced automatically; sighted
 * keyboard users see a visible focus indicator on the new heading.
 *
 * Usage:
 *   const headingRef = useRef<HTMLHeadingElement>(null);
 *   useFocusOnRouteChange(headingRef, [route]);
 *   return <h1 ref={headingRef} tabIndex={-1}>...</h1>;
 *
 * The tabIndex={-1} on the heading is required so it can receive
 * programmatic focus without entering the tab order.
 */
import { useEffect, type RefObject } from 'react';

export function useFocusOnRouteChange(
  ref: RefObject<HTMLElement>,
  deps: ReadonlyArray<unknown>,
): void {
  useEffect(() => {
    if (ref.current === null) return;
    ref.current.focus();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, deps);
}
