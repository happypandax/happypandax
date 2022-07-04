import { handler, RequestOptions } from '../../misc/requests';
import { urlparse } from '../../misc/utility';
import { ServiceType } from '../../services/constants';

export default handler().get(async (req, res) => {
  const server = global.app.service.get(ServiceType.Server);

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
