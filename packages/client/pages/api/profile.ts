import { handler, RequestOptions } from '../../misc/requests';
import { urlparse } from '../../misc/utility';
import { ServiceType } from '../../services/constants';

export default handler().get(async (req, res) => {
  const server = global.app.service.get(ServiceType.Server);

  const { item_type, item_ids, profile_options, __options } = urlparse(
    req.url
  ).query;

  return server
    .profile(
      {
        item_type: item_type as number,
        item_ids: item_ids as number[],
        profile_options: profile_options as any,
      },
      undefined,
      __options as RequestOptions
    )
    .then((r) => {
      res.status(200).json(r);
    });
});
