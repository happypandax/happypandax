import { TransientViewAction } from '../../misc/enums';
import { handler, RequestOptions } from '../../misc/requests';
import { ViewID } from '../../misc/types';
import { ServiceType } from '../../services/constants';

export default handler().post(async (req, res) => {
  const server = global.app.service.get(ServiceType.Server);

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
