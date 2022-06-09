import { handler } from '../../misc/requests';
import { ServiceType } from '../../services/constants';

export default handler().post(async (req, res) => {
  const server = global.app.service.get(ServiceType.Server);

  const { command_ids } = req.body;

  let p: Promise<any>;

  const m = req.method.toUpperCase();

  return server
    .command_state({
      command_ids: command_ids as string[],
    })
    .then((r) => {
      res.status(200).json(r);
    });
});
