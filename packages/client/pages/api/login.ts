import { handler } from '../../server/requests';
import { ServiceType } from '../../services/constants';

export default handler().post(async (req, res) => {
  const server = global.app.service.get(ServiceType.Server);

  const { username, password, endpoint } = req.body;

  return server.login(username, password, endpoint).then(() => {
    return res.status(200).json({ status: server.logged_in });
  });
});
