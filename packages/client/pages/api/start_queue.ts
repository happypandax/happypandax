import { ServiceType } from '../../server/constants';
import { handler, RequestOptions } from '../../server/requests';

export default handler().post(async (req, res) => {
  const server = await global.app.service
    .get(ServiceType.Server)
    .context({ req, res });

  const { queue_type, __options } = req.body;

  return server
    .start_queue(
      {
        queue_type: queue_type as number,
      },
      undefined,
      __options as RequestOptions
    )
    .then((r) => {
      res.status(200).json(r);
    });
});
