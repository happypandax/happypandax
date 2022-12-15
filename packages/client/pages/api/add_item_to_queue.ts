import { handler } from '../../server/requests';
import { ServiceType } from '../../services/constants';

export default handler().post(async (req, res) => {
  const server = global.app.service.get(ServiceType.Server);

  const {
    queue_type,
    item_id,
    item_type,
    options,
    priority,
    __options,
  } = req.body;

  return server
    .add_item_to_queue(
      {
        queue_type,
        item_id,
        options,
        priority,
        item_type,
      },
      undefined,
      __options
    )
    .then((r) => {
      res.status(200).json(r);
    });
});
