import { ServiceType } from '../../server/constants';
import { handler } from '../../server/requests';

export default handler().post(async (req, res) => {
  const server = await global.app.service
    .get(ServiceType.Server)
    .context({ req, res });

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
