import { handler, RequestOptions } from '../../server/requests';
import { ServiceType } from '../../services/constants';

export default handler().post(async (req, res) => {
  const server = global.app.service.get(ServiceType.Server);

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
