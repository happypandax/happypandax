import { ServiceType } from '../../server/constants';
import { handler, RequestOptions } from '../../server/requests';
import { urlparse } from '../../shared/utility';

export default handler()
  .get(async (req, res) => {
    const server = await global.app.service
      .get(ServiceType.Server)
      .context({ req, res });

    const { item_type, item_id, fields, __options } = urlparse(req.url).query;

    return server
      .item(
        {
          item_type: item_type as number,
          fields: fields as any,
          item_id: item_id as number,
        },
        undefined,
        __options as RequestOptions
      )
      .then((r) => {
        res.status(200).json(r);
      });
  })
  .patch(async (req, res) => {
    const server = await global.app.service
      .get(ServiceType.Server)
      .context({ req, res });

    const { item_type, item, options, __options } = req.body;

    return server
      .update_item(
        {
          item_type: item_type as number,
          item: item as any,
          options: options as any,
        },
        undefined,
        __options as RequestOptions
      )
      .then((r) => {
        res.status(200).json(r);
      });
  })
  .post(async (req, res) => {
    const server = await global.app.service
      .get(ServiceType.Server)
      .context({ req, res });

    const { item_type, item, options, __options } = req.body;

    return server
      .new_item(
        {
          item_type: item_type as number,
          item: item as any,
          options: options as any,
        },
        undefined,
        __options as RequestOptions
      )
      .then((r) => {
        res.status(200).json(r);
      });
  });
