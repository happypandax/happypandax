import { handler, RequestOptions } from '../../server/requests';
import { ServiceType } from '../../services/constants';

export default handler().post(async (req, res) => {
  const server = global.app.service.get(ServiceType.Server);

  const { queue_type, item_id, item_type, __options } = req.body;

  return server
    .remove_item_from_queue(
      {
        queue_type,
        item_id,
        item_type,
      },
      undefined,
      __options as RequestOptions
    )
    .then((r) => {
      res.status(200).json(r);
    });
});
