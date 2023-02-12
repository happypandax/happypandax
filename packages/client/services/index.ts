import { ServiceLocator } from './base';
import FairyService from './fairy';
import PixieService from './pixie';
import ServerService from './server';

export default async function setupServices() {
  global.app.log('Setting up services...');
  const locator = new ServiceLocator();
  locator.set(new ServerService());
  locator.set(new PixieService());
  locator.set(new FairyService());

  await locator.init(locator);

  return locator;
}
