import { ServiceType } from '../../server/constants';
import { handler } from '../../server/requests';

export default handler().post(async (req, res) => {
  const server = await global.app.service.get(ServiceType.Server);

  const { session } = req.body;

  return server.logout(session).then((status) => {
    return res.status(200).json({ status });
  });
});
