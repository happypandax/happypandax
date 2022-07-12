import { handler, RequestOptions } from '../../misc/requests';
import { ViewID } from '../../misc/types';
import { ServiceType } from '../../services/constants';

export default handler().post(async (req, res) => {
  const server = global.app.service.get(ServiceType.Server);

  const {
    path,
    patterns,
    options,
    view_id,
    limit,
    offset,
    __options,
  } = req.body;

  return server
    .scan_galleries(
      {
        path: path as string,
        patterns: patterns as string[],
        options: options as object,
        view_id: view_id as ViewID,
        limit: limit as number,
        offset: offset as number,
      },
      undefined,
      __options as RequestOptions
    )
    .then((r) => {
      res.status(200).json(r);
    });
});
