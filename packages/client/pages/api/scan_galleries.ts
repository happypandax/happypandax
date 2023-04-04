import { ServiceType } from '../../server/constants';
import { handler, RequestOptions } from '../../server/requests';
import { ViewID } from '../../shared/types';

export default handler().post(async (req, res) => {
  const server = await global.app.service
    .get(ServiceType.Server)
    .context({ req, res });

  const { path, patterns, options, view_id, limit, offset, __options } =
    req.body;

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
