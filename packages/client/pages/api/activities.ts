import { ActivityType } from '../../misc/enums';
import { handler } from '../../misc/requests';
import { ServiceType } from '../../services/constants';

export default handler().post(async (req, res) => {
  const server = global.app.service.get(ServiceType.Server);


  const { items, activity_type } = req.body;

  return server
    .activities({
      items: items as Record<string, number[]>,
      activity_type: activity_type as ActivityType
    })
    .then((r) => {
      res.status(200).json(r);
    });
});
