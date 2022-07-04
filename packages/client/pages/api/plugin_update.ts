import { handler, RequestOptions } from '../../misc/requests';
import { urlparse } from '../../misc/utility';
import { ServiceType } from '../../services/constants';

export default handler()
  .get(async (req, res) => {
    const server = global.app.service.get(ServiceType.Server);

    const { plugin_ids, force, push, __options } = urlparse(req.url).query;

    return server
      .check_plugin_update(
        {
          plugin_ids: plugin_ids as string[],
          force: force as boolean,
          push: push as boolean,
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

    const { plugin_ids, force, push, __options } = urlparse(req.url).query;

    return server
      .update_plugin(
        {
          plugin_ids: plugin_ids as string[],
          force: force as boolean,
          push: push as boolean,
        },
        undefined,
        __options as RequestOptions
      )
      .then((r) => {
        res.status(200).json(r);
      });
  });
