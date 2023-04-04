import { ServiceType } from '../../server/constants';
import { handler, RequestOptions } from '../../server/requests';
import { ViewID } from '../../shared/types';
import { urlparse } from '../../shared/utility';

export default handler().get(async (req, res) => {
  const server = await global.app.service
    .get(ServiceType.Server)
    .context({ req, res });

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
