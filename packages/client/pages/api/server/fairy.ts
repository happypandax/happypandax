import { createSession } from 'better-sse';

import { getSession, handler } from '../../../server/requests';
import { ServiceType } from '../../../services/constants';

export default handler().all(async (req, res) => {
  const session = await createSession(req, res, {
    headers: {
      'Cache-Control': 'no-cache, no-transform',
    },
  });
  const fairy = global.app.service.get(ServiceType.Fairy);

  const s = await getSession(req, res);

  fairy.register(req, session, s.id);
});
