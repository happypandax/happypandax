import { handler } from '../../misc/requests';
import { urlparse } from '../../misc/utility';
import { ServiceType } from '../../services/constants';

export default handler().get(async (req, res) => {
  const server = global.app.service.get(ServiceType.Server);

  const { state } = urlparse(req.url).query;

  return server
    .list_plugins({
      state: state as number,
    })
    .then((r) => {
      res.status(200).json(r);
    });
});
