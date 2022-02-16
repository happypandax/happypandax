import { handler } from '../../misc/requests';
import { urlparse } from '../../misc/utility';
import { ServiceType } from '../../services/constants';

export default handler()
  .get(async (req, res) => {
    const server = global.app.service.get(ServiceType.Server);

    const { cfg, flatten } = urlparse(req.url).query;

    return server
      .config({
        cfg: cfg as any,
        flatten: flatten as boolean,
      })
      .then((r) => {
        res.status(200).json(r);
      });
  })
  .post(async (req, res) => {
    const server = global.app.service.get(ServiceType.Server);

    const { cfg } = req.body;

    return server.set_config({ cfg }).then((r) => {
      return res.status(200).json(r);
    });
  });
