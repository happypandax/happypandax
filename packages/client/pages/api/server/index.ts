import FileType from 'file-type';
import fs from 'fs';
import path from 'path';
import sanitize from 'sanitize-filename';

import { handler } from '../../../misc/requests';
import { STATIC_FOLDER } from '../../../services/constants';

// THIS IS SPECIFIC TO WHEN THE WEBSERVER IS STARTED BY HPX SERVER

const errTxt = "Momo didn't find anything!";

export function createImageHandler(path_type: string) {
  return handler().get(async (req, res) => {
    const { p1, p2, p3 } = req.query;

    if (!(p1 && p2 && p3)) {
      return res.status(404).end(errTxt);
    } else {
      const p = path.join(
        STATIC_FOLDER,
        path_type,
        sanitize(p1 as string),
        sanitize(p2 as string),
        sanitize(p3 as string)
      );

      if (!fs.existsSync(p)) {
        return res.status(404).end(errTxt);
      }
      const type = await FileType.fromFile(p);
      const s = fs.createReadStream(p);
      s.on('open', function () {
        res.setHeader('Content-Type', type?.mime ? type?.mime : '');
        s.pipe(res);
      });
      s.on('error', function () {
        return res.status(404).end(errTxt);
      });
    }
  });
}

export default handler();
