import { handler, RequestOptions } from '../../server/requests';
import { ServiceType } from '../../services/constants';
import { urlparse } from '../../shared/utility';

export default handler().get(async (req, res) => {
  const server = global.app.service.get(ServiceType.Server);

  const {
    queue_type,
    limit,
    include_finished,
    include_queued,
    include_active,
    __options,
  } = urlparse(req.url).query;

  return server
    .queue_items(
      {
        queue_type: queue_type as number,
        limit: limit as number,
        include_finished: include_finished as boolean,
        include_queued: include_queued as boolean,
        include_active: include_active as boolean,
      },
      undefined,
      __options as RequestOptions
    )
    .then((r) => {
      res.status(200).json(r);
    });
});
