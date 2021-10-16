import { createSession } from 'better-sse';
import superjson from 'superjson';

import { getSession, handler } from '../../../misc/requests';
import { ServiceType } from '../../../services/constants';

export default handler().all(async (req, res) => {
  const session = await createSession(req, res, {
    serializer: superjson.stringify,
    headers: {
      'Cache-Control': 'no-cache, no-transform',
    },
  });
  const fairy = global.app.service.get(ServiceType.Fairy);

  const s = await getSession(req, res);

  fairy.register(req, session, s.id);
});
