import { handler } from '../../misc/requests';
import { ServiceType } from '../../services/constants';

export default handler().post(async (req, res) => {
  const server = global.app.service.get(ServiceType.Server);

  const { item_ids } = req.body;

  return server
    .update_filters({
      item_ids: item_ids as number[],
    })
    .then((r) => {
      res.status(200).json(r);
    });
});
