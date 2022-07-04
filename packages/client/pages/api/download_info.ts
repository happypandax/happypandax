import { handler, RequestOptions } from '../../misc/requests';
import { urlparse } from '../../misc/utility';
import { ServiceType } from '../../services/constants';

export default handler().get(async (req, res) => {
  const server = global.app.service.get(ServiceType.Server);

  const { __options } = urlparse(req.url).query;

  return server
    .download_info({}, undefined, __options as RequestOptions)
    .then((r) => {
      res.status(200).json(r);
    });
});
