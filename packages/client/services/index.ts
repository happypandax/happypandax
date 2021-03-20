import { ServiceLocator } from './base';
import ServerService from './server';

export default async function setupServices() {
  global.app.log('Setting up services...');
  const locator = new ServiceLocator();
  locator.set(new ServerService());

  return locator;
}
