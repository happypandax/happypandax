import { ServiceType } from '../../server/constants';
import { handler } from '../../server/requests';

export default handler({ auth: false }).post(async (req, res) => {
  const server = await global.app.service.get(ServiceType.Server);

  const { username, password } = req.body;

  return server.login(username, password).then((session) => {
    return res.status(200).json({ session });
  });
});
