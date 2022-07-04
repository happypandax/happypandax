import { handler, RequestOptions } from '../../misc/requests';
import { urlparse } from '../../misc/utility';
import { ServiceType } from '../../services/constants';

export default handler()
  .get(async (req, res) => {
    const server = global.app.service.get(ServiceType.Server);

    const { cfg, flatten, __options } = urlparse(req.url).query;

    return server
      .config(
        {
          cfg: cfg as any,
          flatten: flatten as boolean,
        },
        undefined,
        __options as RequestOptions
      )
      .then((r) => {
        res.status(200).json(r);
      });
  })
  .post(async (req, res) => {
    const server = global.app.service.get(ServiceType.Server);

    const { cfg, __options } = req.body;

    return server.set_config({ cfg }, undefined, __options).then((r) => {
      return res.status(200).json(r);
    });
  });
