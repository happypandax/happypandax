import { ServiceType } from '../../server/constants';
import { handler, RequestOptions } from '../../server/requests';
import { urlparse } from '../../shared/utility';

export default handler()
  .get(async (req, res) => {
    const server = await global.app.service
      .get(ServiceType.Server)
      .context({ req, res });

    const { plugin_id, __options } = urlparse(req.url).query;

    return server
      .plugin(
        {
          plugin_id: plugin_id as string,
        },
        undefined,
        __options as RequestOptions
      )
      .then((r) => {
        res.status(200).json(r);
      });
  })
  .post(async (req, res) => {
    const server = await global.app.service
      .get(ServiceType.Server)
      .context({ req, res });

    const { plugin_id, __options } = req.body;

    return server
      .install_plugin(
        {
          plugin_id: plugin_id as string,
        },
        undefined,
        __options as RequestOptions
      )
      .then((r) => {
        res.status(200).json(r);
      });
  })
  .put(async (req, res) => {
    const server = await global.app.service
      .get(ServiceType.Server)
      .context({ req, res });

    const { plugin_id, __options } = req.body;

    return server
      .disable_plugin(
        {
          plugin_id: plugin_id as string,
        },
        undefined,
        __options as RequestOptions
      )
      .then((r) => {
        res.status(200).json(r);
      });
  })
  .delete(async (req, res) => {
    const server = await global.app.service
      .get(ServiceType.Server)
      .context({ req, res });

    const { plugin_id, __options } = req.body;

    return server
      .remove_plugin(
        {
          plugin_id: plugin_id as string,
        },
        undefined,
        __options as RequestOptions
      )
      .then((r) => {
        res.status(200).json(r);
      });
  });
