import { handler, RequestOptions } from '../../server/requests';
import { ServiceType } from '../../services/constants';
import { urlparse } from '../../shared/utility';

export default handler().get(async (req, res) => {
  const server = global.app.service.get(ServiceType.Server);

  const { item_type, metatags, limit, offset, fields, __options } = urlparse(
    req.url
  ).query;

  return server
    .items(
      {
        item_type: item_type as number,
        fields: fields as any,
        metatags: metatags as any,
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
