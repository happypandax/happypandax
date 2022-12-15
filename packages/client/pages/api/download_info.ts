import { handler, RequestOptions } from '../../server/requests';
import { ServiceType } from '../../services/constants';
import { urlparse } from '../../shared/utility';

export default handler().get(async (req, res) => {
  const server = global.app.service.get(ServiceType.Server);

  const { __options } = urlparse(req.url).query;

  return server
    .download_info({}, undefined, __options as RequestOptions)
    .then((r) => {
      res.status(200).json(r);
    });
});
