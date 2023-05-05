import setupServices from '../services/index';
import setupLogger from '../shared/logger';
import { getServerSession } from './requests';

export async function serverInitialize() {
  global.app = global?.app ?? ({} as any);
  global.app.log = setupLogger({});
  try {
    global.app.getServerSession = getServerSession;
    global.app.IS_SERVER = true;
    global.app.title = 'HappyPanda X';

    global.log = global.app.log;

    global.app.service = await setupServices();

    global.app.log.i('initialized server');
    global.app.initialized = true;
  } catch (e) {
    global.app.log.c(e);
    throw e;
  }
}

export default serverInitialize;
