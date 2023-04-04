import { ServiceType } from '../../server/constants';
import { handler, RequestOptions } from '../../server/requests';

export default handler().post(async (req, res) => {
  const server = await global.app.service
    .get(ServiceType.Server)
    .context({ req, res });

  const { item_id, __options } = req.body;

  return server
    .page_read_event(
      {
        item_id: item_id as number,
      },
      undefined,
      __options as RequestOptions
    )
    .then((r) => {
      res.status(200).json(r);
    });
});
