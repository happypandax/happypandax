import { ServiceType } from '../../server/constants';
import { handler } from '../../server/requests';

export default handler().post(async (req, res) => {
  const server = await global.app.service
    .get(ServiceType.Server)
    .context({ req, res });

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
