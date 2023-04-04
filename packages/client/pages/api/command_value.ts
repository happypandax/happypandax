import { ServiceType } from '../../server/constants';
import { handler } from '../../server/requests';

export default handler().post(async (req, res) => {
  const server = await global.app.service
    .get(ServiceType.Server)
    .context({ req, res });

  const { command_ids, raise_error, __options } = req.body;

  let p: Promise<any>;

  const m = req.method.toUpperCase();

  return server
    .command_value(
      {
        command_ids: command_ids as string[],
        raise_error: raise_error as boolean,
      },
      undefined,
      __options
    )
    .then((r) => {
      res.status(200).json(r);
    });
});
