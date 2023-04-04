import { ServiceType } from '../../server/constants';
import { handler, RequestOptions } from '../../server/requests';

export default handler().post(async (req, res) => {
  const server = await global.app.service
    .get(ServiceType.Server)
    .context({ req, res });

  const { pattern, __options } = req.body;

  return server
    .resolve_path_pattern(
      {
        pattern: pattern as string,
      },
      undefined,
      __options as RequestOptions
    )
    .then((r) => {
      res.status(200).json(r);
    });
});
