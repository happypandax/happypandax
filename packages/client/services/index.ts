import { ServiceLocator } from './base';
import FairyService from './fairy';
import PixieService from './pixie';
import ServerService from './server';

export default function setupServices() {
  global.app.log('Setting up services...');
  const locator = new ServiceLocator();
  locator.set(new ServerService());
  locator.set(new PixieService());
  locator.set(new FairyService());

  return locator;
}
