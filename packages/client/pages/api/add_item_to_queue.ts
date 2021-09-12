import { handler } from '../../misc/requests';
import { ServiceType } from '../../services/constants';

export default handler().post(async (req, res) => {
  const server = global.app.service.get(ServiceType.Server);

  const { queue_type, item_id, item_type, options, priority } = req.body;

  return server
    .add_item_to_queue({
      queue_type,
      item_id,
      options,
      priority,
      item_type,
    })
    .then((r) => {
      res.status(200).json(r);
    });
});
