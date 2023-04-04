import { ServiceType } from '../../server/constants';
import { handler, RequestOptions } from '../../server/requests';
import { urlparse } from '../../shared/utility';

export default handler().get(async (req, res) => {
  const server = await global.app.service
    .get(ServiceType.Server)
    .context({ req, res });

  const {
    item_id,
    item_type,
    metatags,
    related_type,
    limit,
    offset,
    fields,
    __options,
  } = urlparse(req.url).query;

  return server
    .related_items(
      {
        item_id: item_type as number,
        item_type: item_type as number,
        related_type: related_type as number,
        metatags: metatags as any,
        fields: fields as any,
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
