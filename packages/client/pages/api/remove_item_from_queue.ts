import { ServiceType } from '../../server/constants';
import { handler, RequestOptions } from '../../server/requests';

export default handler().post(async (req, res) => {
  const server = await global.app.service
    .get(ServiceType.Server)
    .context({ req, res });

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
