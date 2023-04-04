import { ServiceType } from '../../../../server/constants';
import { handler } from '../../../../server/requests';

export default handler().post(async (req, res) => {
  const server = await global.app.service
    .get(ServiceType.Server)
    .context({ req, res });

  const msg = req.body ? JSON.parse(req.body) : {};
  let plugin_id = '';
  req?.headers?.referer?.split('/')?.forEach((p) => {
    if (p.split('-').length - 1 == 4) {
      plugin_id = p;
    }
  });

  return server
    .send_plugin_message({
      plugin_id: plugin_id as string,
      msg: msg as any,
    })
    .then((r) => {
      res.status(200).json(r);
    })
    .catch((err) => {
      res.status(500).json({ error: err.message, code: err?.code });
    });
});
