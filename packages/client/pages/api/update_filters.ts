import { handler, RequestOptions } from '../../misc/requests';
import { ServiceType } from '../../services/constants';

export default handler().post(async (req, res) => {
  const server = global.app.service.get(ServiceType.Server);

  const { item_ids, __options } = req.body;

  return server
    .update_filters(
      {
        item_ids: item_ids as number[],
      },
      undefined,
      __options as RequestOptions
    )
    .then((r) => {
      res.status(200).json(r);
    });
});
