import { ServiceType } from '../../server/constants';
import { handler } from '../../server/requests';

export default handler().post(async (req, res) => {
  const server = await global.app.service
    .get(ServiceType.Server)
    .context({ req, res });

  const { command_ids, __options } = req.body;

  let p: Promise<any>;

  const m = req.method.toUpperCase();

  return server
    .command_state(
      {
        command_ids: command_ids as string[],
      },
      undefined,
      __options
    )
    .then((r) => {
      res.status(200).json(r);
    });
});
