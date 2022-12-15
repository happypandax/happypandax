import { handler } from '../../server/requests';
import { ServiceType } from '../../services/constants';

export default handler().post(async (req, res) => {
  const server = global.app.service.get(ServiceType.Server);

  const { urls, identifier, options, priority, __options } = req.body;

  return server
    .add_urls_to_download_queue(
      {
        urls,
        identifier,
        options,
        priority,
      },
      undefined,
      __options
    )
    .then((r) => {
      res.status(200).json(r);
    });
});
