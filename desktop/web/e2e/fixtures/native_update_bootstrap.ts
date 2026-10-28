/** Establish the actual App graph before starting native acceptance assertions. */
interface NativeDriver {
  run(scenario: string, origin: string): Promise<void>;
}

export async function bootstrap(
  scenario: string,
  origin: string,
  loadApp: () => Promise<unknown> = () => import('../../src/main'),
  loadDriver: () => Promise<NativeDriver> = () => import('./native_update_driver'),
): Promise<void> {
  await loadApp();
  const driver = await loadDriver();
  await driver.run(scenario, origin);
}
