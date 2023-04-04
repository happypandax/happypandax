import { ServiceType } from '../../server/constants';
import { handler, RequestOptions } from '../../server/requests';
import { urlparse } from '../../shared/utility';

export default handler().get(async (req, res) => {
  const server = await global.app.service
    .get(ServiceType.Server)
    .context({ req, res });

  const { item_types, search_query, limit, __options } = urlparse(
    req.url
  ).query;

  return server
    .search_labels(
      {
        item_types: item_types as number[],
        search_query: search_query?.toString?.() as string,
        limit: limit as number,
      },
      undefined,
      __options as RequestOptions
    )
    .then((r) => {
      res.status(200).json(r);
    });
});
