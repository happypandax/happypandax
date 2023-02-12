import { ServiceType } from '../../server/constants';
import { handler, RequestOptions } from '../../server/requests';
import { TransientViewAction } from '../../shared/enums';
import { ViewID } from '../../shared/types';

export default handler().post(async (req, res) => {
  const server = await global.app.service.get(ServiceType.Server).context({ req, res });

  const { view_id, action, __options } = req.body;

  return server
    .transient_view_action(
      {
        view_id: view_id as ViewID,
        action: action as TransientViewAction,
      },
      undefined,
      __options as RequestOptions
    )
    .then((r) => {
      res.status(200).json(r);
    });
});
