import { ServiceType } from '../../server/constants';
import { handler, RequestOptions } from '../../server/requests';
import { urlparse } from '../../shared/utility';

export default handler().get(async (req, res) => {
  const server = await global.app.service
    .get(ServiceType.Server)
    .context({ req, res });

  const { item_type, search_query, limit, offset, fields, __options } =
    urlparse(req.url).query;

  return server
    .search_items(
      {
        item_type: item_type as number,
        fields: fields as any,
        search_query: search_query?.toString?.() as string,
        limit: limit as number,
        offset: offset as number,
      },
      undefined,
      __options as RequestOptions
    )
    .then((r) => {
      res.status(200).json(r);
    });
});
