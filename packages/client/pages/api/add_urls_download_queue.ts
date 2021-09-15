import { handler } from '../../misc/requests';
import { ServiceType } from '../../services/constants';

export default handler().post(async (req, res) => {
  const server = global.app.service.get(ServiceType.Server);

  const { urls, identifier, options, priority } = req.body;

  return server
    .add_urls_to_download_queue({
      urls,
      identifier,
      options,
      priority,
    })
    .then((r) => {
      res.status(200).json(r);
    });
});
