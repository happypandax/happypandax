import { handler } from '../../server/requests';
import { ServiceType } from '../../services/constants';

export default handler().post(async (req, res) => {
  const server = global.app.service.get(ServiceType.Server);

  const { command_ids, __options } = req.body;

  let p: Promise<any>;

  const m = req.method.toUpperCase();

  return server
    .command_value(
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
