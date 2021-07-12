import { handler } from '../../misc/requests';
import { urlparse } from '../../misc/utility';
import { ServiceType } from '../../services/constants';

export default handler().get(async (req, res) => {
  const server = global.app.service.get(ServiceType.Server);

  const { item_type, translate, locale } = urlparse(req.url).query;

  return server
    .sort_indexes({
      item_type: item_type as number,
      translate: translate as boolean,
      locale: locale as string,
    })
    .then((r) => {
      res.status(200).json(r);
    });
});
