import { handler, RequestOptions } from '../../misc/requests';
import { ViewID } from '../../misc/types';
import { urlparse } from '../../misc/utility';
import { ServiceType } from '../../services/constants';

export default handler().get(async (req, res) => {
  const server = global.app.service.get(ServiceType.Server);

  const { view_id, limit, offset, desc, __options } = urlparse(req.url).query;

  return server
    .transient_view(
      {
        view_id: view_id as ViewID,
        limit: limit as number,
        desc: desc as boolean,
        offset: offset as number,
      },
      undefined,
      __options as RequestOptions
    )
    .then((r) => {
      res.status(200).json(r);
    });
});
