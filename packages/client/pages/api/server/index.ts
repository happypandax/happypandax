import axios from 'axios';
import { fileTypeFromBuffer, fileTypeFromFile } from 'file-type';
import { createReadStream, existsSync } from 'fs';
import path from 'path';
import sanitize from 'sanitize-filename';
import { Readable } from 'stream';

import {
  ITEM_THUMB_STATIC_FOLDER,
  PAGE_STATIC_FOLDER,
  THUMB_STATIC_FOLDER,
} from '../../../server/constants';
import { handler } from '../../../server/requests';
import { getPixie } from '../../../services/pixie';

const errTxt = "Momo didn't find anything!";

async function imageFromPath(path_type, req, res) {
  const { t, p1, p2, p3, it } = req.query;

  if (t && p1 && p2 && p3) {
    let p: string;

    if (path_type === 'page') {
      p = PAGE_STATIC_FOLDER;
    } else if (t === 'ti' && it) {
      p = path.join(ITEM_THUMB_STATIC_FOLDER, sanitize(it as string));
    } else {
      p = THUMB_STATIC_FOLDER;
    }

    p = path.join(
      p,
      sanitize(p1 as string),
      sanitize(p2 as string),
      sanitize(p3 as string)
    );

    if (!existsSync(p)) {
      return res.status(404).end(errTxt);
    }
    const type = await fileTypeFromFile(p);
    const s = createReadStream(p);
    s.on('open', function () {
      res.setHeader('Content-Type', type?.mime ? type?.mime : '');
      s.pipe(res);
    });
    s.on('error', function (e) {
      if (process.env.NODE_ENV === 'development') {
        throw e;
      }
      return res.status(404).end(errTxt);
    });
  } else {
    return res.status(404).end(errTxt);
  }
}

export function createImageHandler(path_type: string) {
  return handler({ auth: false }).get(async (req, res) => {
    const { t, ...rest } = req.query;
    const pixie = await getPixie(false);

    if (pixie.isHPXInstanced) {
      const token = req.headers?.['x-hpx-token'];
      if (token != pixie.HPXToken) {
        return res.status(404).end("Momo: invalid token!");
      }
    }

    const hostPaths = THUMB_STATIC_FOLDER && ITEM_THUMB_STATIC_FOLDER && PAGE_STATIC_FOLDER;

    if (hostPaths && pixie.isLocal && pixie.connected && t && Object.keys(rest ?? {}).length) {
      if (t === 'g' || (rest?.l1 && rest?.l2 && rest?.l3)) {
        try {
          const b = await pixie.image({ t, ...(rest as any) });
          if (b.data && Buffer.isBuffer(b.data)) {
            const type = await fileTypeFromBuffer(b.data);
            const s = new Readable();
            s.push(b.data);
            s.push(null);
            s.on('error', function (e) {
              if (process.env.NODE_ENV === 'development') {
                throw e;
              }

              return res.status(404).end(errTxt);
            });
            res.setHeader('Content-Type', type?.mime ? type?.mime : '');
            s.pipe(res);

            return;

          } else {
            global.app.log.w(b?.data);
            return res.status(404).end(errTxt);
          }
        } catch (err) {
          global.app.log.w('Error on', req.url, err);
          if (process.env.NODE_ENV === 'development') {
            throw err;
          }
          return res.status(404).end(errTxt);
        }
      } else {
        return await imageFromPath(path_type, req, res);
      }

    } else if (!pixie.isHPXInstanced && pixie.webserver_endpoint) {

      // forward
      const url = pixie.webserver_endpoint + req.url

      try {
        const r = await axios(url, {
          responseType: "stream",
          method: req.method ?? 'GET',
          headers: {
            'x-hpx-token': pixie.HPXToken,
          }
        });


        const type = r.headers['content-type'];
        if (type) {
          res.setHeader('Content-Type', type);
        }

        r.data.on('error', function (e) {
          if (process.env.NODE_ENV === 'development') {
            throw e;
          }
          return res.status(404).end(errTxt);
        });

        r.data.pipe(res)

        return;
      } catch (err) {
        if (process.env.NODE_ENV === 'development') {
          throw err;
        }
        return res.status(404).end(errTxt);
      }
    }

    return res.status(404).end(errTxt);
  });
}

export default handler();
