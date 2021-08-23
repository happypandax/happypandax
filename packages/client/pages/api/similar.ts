import { handler } from '../../misc/requests';
import { urlparse } from '../../misc/utility';
import { ServiceType } from '../../services/constants';

export default handler().get(async (req, res) => {
  const server = global.app.service.get(ServiceType.Server);

  const { item_type, item_id, limit, fields, profile_options } = urlparse(
    req.url
  ).query;

  return server
    .similar({
      item_type: item_type as number,
      item_id: item_id as number,
      fields: fields as any,
      limit: limit as number,
      profile_options: profile_options as any,
    })
    .then((r) => {
      res.status(200).json(r);
    });
});
