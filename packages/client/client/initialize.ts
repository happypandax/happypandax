import setupLogger from '../shared/logger';
import { GlobalState } from '../state/global';

export async function clientInitialize() {
  global.app = global?.app ?? ({} as any);
  global.app.IS_SERVER = false;
  global.app.title = 'HappyPanda X';

  global.app.log = setupLogger();
  global.log = global.app.log;

  global.app.log.i('initialized client');
  global.app.initialized = true;
  GlobalState.initialized = true;
}

export default clientInitialize;
