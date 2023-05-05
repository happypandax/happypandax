import { createSession } from 'better-sse';

import { ServiceType } from '../../../server/constants';
import { getServerSession, handler } from '../../../server/requests';

export default handler({ auth: false }).all(async (req, res) => {
  const session = await createSession(req, res, {
    headers: {
      'Cache-Control': 'no-cache, no-transform',
    },
  });
  const fairy = global.app.service.get(ServiceType.Fairy);
  const sess = await getServerSession({ req, res });

  fairy.register(req, session, sess.id);
});
