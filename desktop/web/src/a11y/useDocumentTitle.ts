/**
 * useDocumentTitle — sets document.title for the lifetime of the
 * mounted component; restores the previous title on unmount.
 *
 * Setting title from React (rather than from a server-rendered <title>)
 * is required for SPA route changes — WCAG 2.4.2 ("Page Titled") fails
 * if every route shares the same static title.
 */
import { useEffect } from 'react';

export function useDocumentTitle(title: string): void {
  useEffect(() => {
    const previous = document.title;
    document.title = title;
    return () => {
      document.title = previous;
    };
  }, [title]);
}
