import { handler } from '../../../../misc/requests';

export default handler().all(async (req, res) => {
  return res.status(200).end('test');
});
