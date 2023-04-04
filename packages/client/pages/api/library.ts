import { ServiceType } from '../../server/constants';
import { handler, RequestOptions } from '../../server/requests';
import { urlparse } from '../../shared/utility';

export default handler().get(async (req, res) => {
  const server = await global.app.service
    .get(ServiceType.Server)
    .context({ req, res });

  const {
    item_type,
    related_type,
    item_id,
    limit,
    page,
    metatags,
    fields,
    filter_id,
    search_query,
    sort_options,
    search_options,
    __options,
  } = urlparse(req.url).query;

  return server
    .library(
      {
        item_id: item_id as number,
        related_type: related_type as number,
        item_type: item_type as number,
        fields: fields as any,
        limit: limit as number,
        page: page as number,
        metatags: metatags as any,
        filter_id: filter_id as number,
        sort_options: sort_options as any,
        search_query: search_query as string,
        search_options: search_options as any,
      },
      undefined,
      __options as RequestOptions
    )
    .then((r) => {
      res.status(200).json(r);
    });
});
