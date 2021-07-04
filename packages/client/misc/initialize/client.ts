import setupLogger from '../logger';

export async function clientInitialize() {
  global.app = global?.app ?? ({} as any);
  global.app.IS_SERVER = false;
  global.app.title = 'HappyPanda X';

  global.app.log = setupLogger();

  global.app.log.i('initialized client');
  global.app.initialized = true;
}

export default clientInitialize;
