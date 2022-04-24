import { handler } from '../../../../misc/requests';
import { ServiceType } from '../../../../services/constants';

export default handler().post(async (req, res) => {
  const server = global.app.service.get(ServiceType.Server);

  const { identifier, credentials, options } = req.body;

  return server
    .submit_login({
      identifier: identifier as string,
      credentials: credentials as any,
      options: options as any,
    })
    .then((r) => {
      res.status(200).json(r);
    })
    .catch((e) => {
      res.status(500).json({ error: e.message });
    });
});
