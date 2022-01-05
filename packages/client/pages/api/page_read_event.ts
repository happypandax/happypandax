import { handler } from '../../misc/requests';
import { ServiceType } from '../../services/constants';

export default handler().post(async (req, res) => {
  const server = global.app.service.get(ServiceType.Server);

  const { item_id } = req.body;

  return server
    .page_read_event({
      item_id: item_id as number,
    })
    .then((r) => {
      res.status(200).json(r);
    });
});
