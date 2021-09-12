import { handler } from '../../misc/requests';
import { urlparse } from '../../misc/utility';
import { ServiceType } from '../../services/constants';

export default handler().get(async (req, res) => {
  const server = global.app.service.get(ServiceType.Server);

  const { log_type } = urlparse(req.url).query;

  return server
    .log({
      log_type: log_type as number,
    })
    .then((r) => {
      res.status(200).json(r);
    });
});
