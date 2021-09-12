import { handler } from '../../misc/requests';
import { urlparse } from '../../misc/utility';
import { ServiceType } from '../../services/constants';

export default handler().get(async (req, res) => {
  const server = global.app.service.get(ServiceType.Server);

  const { queue_type, include_finished } = urlparse(req.url).query;

  return server
    .queue_state({
      queue_type: queue_type as number,
      include_finished: include_finished as boolean,
    })
    .then((r) => {
      res.status(200).json(r);
    });
});
