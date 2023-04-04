import { ServiceType } from '../../server/constants';
import { handler, RequestOptions } from '../../server/requests';
import { urlparse } from '../../shared/utility';

export default handler().get(async (req, res) => {
  const server = await global.app.service
    .get(ServiceType.Server)
    .context({ req, res });

  const { item_type, translate, locale, children, __options } = urlparse(
    req.url
  ).query;

  return server
    .sort_indexes(
      {
        item_type: item_type as number,
        translate: translate as boolean,
        children: children as boolean,
        locale: locale as string,
      },
      undefined,
      __options as RequestOptions
    )
    .then((r) => {
      res.status(200).json(r);
    });
});
