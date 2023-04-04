import { ServiceType } from '../../server/constants';
import { handler } from '../../server/requests';

export default handler().get(async (req, res) => {
  const server = await global.app.service
    .get(ServiceType.Server)
    .context({ req, res });

  const s = server.status();
  res.status(200).json(s);
});
