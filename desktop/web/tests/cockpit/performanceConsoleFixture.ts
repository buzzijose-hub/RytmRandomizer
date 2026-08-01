import { performanceConsoleDemoModel } from '../../src/cockpit';
import type { LiveGuiPerformanceConsoleModelDict } from '../../src/types/live_gui_protocol';
import performanceConsolePayloadJson from './fixtures/performance_console.json';

/**
 * `fixtures/performance_console.json` is GENERATED from the passive Python
 * payload — regenerate with
 * `python scripts/generate_live_gui_protocol_ts.py --fixture`.
 * `tests/architecture/test_live_gui_protocol_is_generated.py` keeps it fresh.
 */
export interface PerformanceConsolePayloadFixture {
  readonly live_gui_performance_console: LiveGuiPerformanceConsoleModelDict;
  readonly safety: ReadonlyArray<string>;
}

export const performanceConsolePayloadFixture: PerformanceConsolePayloadFixture =
  performanceConsolePayloadJson as unknown as PerformanceConsolePayloadFixture;

export const performanceConsoleModel = performanceConsoleDemoModel;
