import { handler, RequestOptions } from '../../server/requests';
import { ServiceType } from '../../services/constants';
import { urlparse } from '../../shared/utility';

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
