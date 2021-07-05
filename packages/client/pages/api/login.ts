

import { handler } from '../../misc/requests';
import { ServiceType } from '../../services/constants';

export default handler().post(async (req, res) => {
  const server = global.app.service.get(ServiceType.Server);

  const { username, password } = req.body;

  return server
    .login(username, password)
    .then(() => {
      res.status(200).json({ status: server.logged_in });
    })
    .catch((e) => {
      res.status(500).json({ status: server.logged_in, error: e.message });
    });
});
