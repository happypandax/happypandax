import { ServiceType } from '../../server/constants';
import { handler, RequestOptions } from '../../server/requests';

export default handler().post(async (req, res) => {
  const server = await global.app.service
    .get(ServiceType.Server)
    .context({ req, res });

  const { item_type, item_id, viewer_args, __options } = req.body;

  return server
    .open_gallery(
      {
        item_id: item_id as number,
        item_type: item_type as number,
        viewer_args: viewer_args as string,
      },
      undefined,
      __options as RequestOptions
    )
    .then((r) => {
      res.status(200).json(r);
    });
});
