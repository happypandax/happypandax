

import { MomoAction } from '../../../misc/enums';
import { handler } from '../../../misc/requests';

export default handler().post(async (req, res) => {
    const { action } = req.body

    switch (action as MomoAction) {
        case MomoAction.SAME_MACHINE:
            res.status(200).json({ data: true })
            break
        default:
            res.status(404).end("no.");
    }

});
