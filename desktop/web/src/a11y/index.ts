/**
 * Public surface of the a11y module. Other Phase B clusters append
 * to this file as they ship.
 */
export { nextIndex, isRovingKey, type RovingKey } from './rovingTabindex';
export { useFocusOnRouteChange } from './useFocusOnRouteChange';
export { announce, _registerWriter, _reset } from './announcer';
export { LiveRegion } from './LiveRegion';
export { useDocumentTitle } from './useDocumentTitle';
