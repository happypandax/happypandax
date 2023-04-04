import { ServiceType } from '../../server/constants';
import { handler } from '../../server/requests';
import { ActivityType } from '../../shared/enums';

export default handler().post(async (req, res) => {
  const server = await global.app.service
    .get(ServiceType.Server)
    .context({ req, res });

  const { items, activity_type, __options } = req.body;

  return server
    .activities(
      {
        items: items as Record<string, number[]>,
        activity_type: activity_type as ActivityType,
      },
      undefined,
      __options
    )
    .then((r) => {
      res.status(200).json(r);
    });
});
