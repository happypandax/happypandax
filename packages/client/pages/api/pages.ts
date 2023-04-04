import { ServiceType } from '../../server/constants';
import { handler, RequestOptions } from '../../server/requests';
import { urlparse } from '../../shared/utility';

export default handler().get(async (req, res) => {
  const server = await global.app.service
    .get(ServiceType.Server)
    .context({ req, res });

  const {
    gallery_id,
    window_size,
    number,
    fields,
    profile_options,
    __options,
  } = urlparse(req.url).query;

  return server
    .pages(
      {
        number: number as number,
        gallery_id: gallery_id as number,
        fields: fields as any,
        window_size: window_size as number,
        profile_options: profile_options as any,
      },
      undefined,
      __options as RequestOptions
    )
    .then((r) => {
      res.status(200).json(r);
    });
});
