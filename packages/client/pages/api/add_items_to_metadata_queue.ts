import { handler } from '../../misc/requests';
import { ServiceType } from '../../services/constants';

export default handler().post(async (req, res) => {
  const server = global.app.service.get(ServiceType.Server);

  const { items_kind, item_type, options, priority, __options } = req.body;

  return server
    .add_items_to_metadata_queue(
      {
        items_kind,
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
