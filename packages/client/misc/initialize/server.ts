import setupServices from '../../services/index';
import setupLogger from '../logger';

export async function serverInitialize() {
  global.app = global?.app ?? ({} as any);
  global.app.IS_SERVER = true;
  global.app.title = 'HappyPanda X';

  global.app.log = setupLogger();
  global.log = global.app.log;

  global.app.service = await setupServices();

  global.app.log.i('initialized server');
  global.app.initialized = true;
}

export default serverInitialize;
