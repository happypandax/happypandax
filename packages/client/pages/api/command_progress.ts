import { handler, RequestOptions } from '../../server/requests';
import { ServiceType } from '../../services/constants';
import { CommandIDKey } from '../../shared/types';
import { urlparse } from '../../shared/utility';

export default handler().get(async (req, res) => {
  const server = global.app.service.get(ServiceType.Server);

  const { command_ids, __options } = urlparse(req.url).query;

  return server
    .command_progress(
      {
        command_ids: command_ids as CommandIDKey[],
      },
      undefined,
      __options as RequestOptions
    )
    .then((r) => {
      res.status(200).json(r);
    });
});
