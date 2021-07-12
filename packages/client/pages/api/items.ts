import { handler } from '../../misc/requests';
import { urlparse } from '../../misc/utility';
import { ServiceType } from '../../services/constants';

export default handler().get(async (req, res) => {
  const server = global.app.service.get(ServiceType.Server);

  const { item_type, limit, offset } = urlparse(req.url).query;

  return server
    .items({
      item_type: item_type as number,
      limit: limit as number,
      offset: offset as number,
    })
    .then((r) => {
      res.status(200).json(r);
    });
});
