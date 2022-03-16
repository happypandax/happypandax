import { handler } from '../../misc/requests';
import { urlparse } from '../../misc/utility';
import { ServiceType } from '../../services/constants';

export default handler()
  .get(async (req, res) => {
    const server = global.app.service.get(ServiceType.Server);

    const { plugin_id } = urlparse(req.url).query;

    return server
      .plugin({
        plugin_id: plugin_id as string,
      })
      .then((r) => {
        res.status(200).json(r);
      });
  })
  .post(async (req, res) => {
    const server = global.app.service.get(ServiceType.Server);

    const { plugin_id } = req.body;

    return server
      .install_plugin({
        plugin_id: plugin_id as string,
      })
      .then((r) => {
        res.status(200).json(r);
      });
  })
  .put(async (req, res) => {
    const server = global.app.service.get(ServiceType.Server);

    const { plugin_id } = req.body;

    return server
      .disable_plugin({
        plugin_id: plugin_id as string,
      })
      .then((r) => {
        res.status(200).json(r);
      });
  })
  .delete(async (req, res) => {
    const server = global.app.service.get(ServiceType.Server);

    const { plugin_id } = req.body;

    return server
      .remove_plugin({
        plugin_id: plugin_id as string,
      })
      .then((r) => {
        res.status(200).json(r);
      });
  });
