import { handler } from '../../../server/requests';
import { MomoType } from '../../../shared/query';

export default handler().post(async (req, res) => {
  const { action } = req.body;

  switch (action as MomoType) {
    case MomoType.SAME_MACHINE: {
      const data = req.socket.localAddress === req.socket.remoteAddress;
      res.status(200).json({ data });
      break;
    }
    default:
      res.status(404).json({ error: 'no.', code: 0 });
  }
});
