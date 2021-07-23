import { handler } from '../../misc/requests';
import { urlparse } from '../../misc/utility';
import { ServiceType } from '../../services/constants';

export default handler().get(async (req, res) => {
  const server = global.app.service.get(ServiceType.Server);

  const {
    item_type,
    limit,
    page,
    metatags,
    fields,
    filter_id,
    sort_by,
    sort_desc,
    search_query,
    search_options,
  } = urlparse(req.url).query;

  return server
    .library({
      item_type: item_type as number,
      fields: fields as any,
      limit: limit as number,
      page: page as number,
      metatags: metatags as any,
      filter_id: filter_id as number,
      sort_by: sort_by as number,
      sort_desc: sort_desc as boolean,
      search_query: search_query as string,
      search_options: search_options as any,
    })
    .then((r) => {
      res.status(200).json(r);
    });
});
