import { handler } from '../../misc/requests';
import { urlparse } from '../../misc/utility';
import { ServiceType } from '../../services/constants';

export default handler().all(async (req, res) => {
  const server = global.app.service.get(ServiceType.Server);

  const { command_ids } = urlparse(req.url).query;

  let p: Promise<any>;

  const m = req.method.toUpperCase();

  switch (m) {
    case 'GET':
      p = server.command_value({
        command_ids: command_ids as number[],
      });
      break;
    case 'POST':
      p = server.start_command({
        command_ids: command_ids as number[],
      });
      break;
    case 'DELETE':
      p = server.stop_command({
        command_ids: command_ids as number[],
      });
      break;
    default:
      p = server.command_state({
        command_ids: command_ids as number[],
      });
      break;
  }

  return p.then((r) => {
    res.status(200).json(r);
  });
});
