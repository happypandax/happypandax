import { handler } from '../../misc/requests';
import { urlparse } from '../../misc/utility';
import { ServiceType } from '../../services/constants';

export default handler().get(async (req, res) => {
  const server = global.app.service.get(ServiceType.Server);

  const { item_types, search_query, limit } = urlparse(req.url).query;

  return server
    .search_items({
      item_types: item_types as number[],
      search_query: search_query as string,
      limit: limit as number,
    })
    .then((r) => {
      res.status(200).json(r);
    });
});
