import { handler } from '../../misc/requests';
import { ServiceType } from '../../services/constants';

export default handler().get(async (req, res) => {
  const server = global.app.service.get(ServiceType.Server);

  const s = server.status();
  res.status(200).json(s);
});
