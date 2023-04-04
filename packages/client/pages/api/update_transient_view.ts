import { JsonMap } from 'happypandax-client';

import { ServiceType } from '../../server/constants';
import { handler, RequestOptions } from '../../server/requests';
import { ViewID } from '../../shared/types';

export default handler().post(async (req, res) => {
  const server = await global.app.service
    .get(ServiceType.Server)
    .context({ req, res });

  const { view_id, options, properties, __options } = req.body;

  return server
    .update_transient_view(
      {
        view_id: view_id as ViewID,
        options: options as JsonMap,
        properties: properties as JsonMap,
      },
      undefined,
      __options as RequestOptions
    )
    .then((r) => {
      res.status(200).json(r);
    });
});
