import { handler, RequestOptions } from '../../misc/requests';
import { ServiceType } from '../../services/constants';

export default handler().post(async (req, res) => {
  const server = global.app.service.get(ServiceType.Server);

  const { item_type, item_id, metatags, __options } = req.body;

  return server
    .update_metatags(
      {
        item_type: item_type as number,
        item_id: item_id as number,
        metatags: metatags as any,
      },
      undefined,
      __options as RequestOptions
    )
    .then((r) => {
      res.status(200).json(r);
    });
});
