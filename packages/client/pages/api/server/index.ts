import FileType from 'file-type';
import { createReadStream, existsSync } from 'fs';
import path from 'path';
import sanitize from 'sanitize-filename';
import { Readable } from 'stream';

import { handler } from '../../../misc/requests';
import {
  PAGE_STATIC_FOLDER,
  PIXIE_ENDPOINT,
  ServiceType,
  THUMB_STATIC_FOLDER,
} from '../../../services/constants';

// THIS IS SPECIFIC TO WHEN THE WEBSERVER IS STARTED BY HPX SERVER

const errTxt = "Momo didn't find anything!";

async function getPixie() {
  const pixie = global.app.service.get(ServiceType.Pixie);
  if (!pixie.connected) {
    let addr = PIXIE_ENDPOINT;
    if (!addr) {
      const server = global.app.service.get(ServiceType.Server);
      const s = server.status();
      if (s.connected && s.loggedIn) {
        const props = await server.properties({ keys: ['pixie.connect'] });
        addr = props.pixie.connect;
      } else {
        throw Error('server not connected');
      }
    }

    await pixie.connect(addr);
  }
  return pixie;
}

export function createImageHandler(path_type: string) {
  return handler().get(async (req, res) => {
    const { p1, p2, p3, ...rest } = req.query;

    if (p1 && p2 && p3) {
      const p = path.join(
        path_type === 'page' ? PAGE_STATIC_FOLDER : THUMB_STATIC_FOLDER,
        sanitize(p1 as string),
        sanitize(p2 as string),
        sanitize(p3 as string)
      );

      if (!existsSync(p)) {
        return res.status(404).end(errTxt);
      }
      const type = await FileType.fromFile(p);
      const s = createReadStream(p);
      s.on('open', function () {
        res.setHeader('Content-Type', type?.mime ? type?.mime : '');
        s.pipe(res);
      });
      s.on('error', function () {
        return res.status(404).end(errTxt);
      });
    } else if (Object.keys(rest ?? {}).length) {
      const pixie = await getPixie();
      try {
        const b = await pixie.image({ ...(rest as any) });
        if (b.data && Buffer.isBuffer(b.data)) {
          const type = await FileType.fromBuffer(b.data);
          const s = new Readable();
          s.push(b.data);
          s.push(null);
          s.on('error', function () {
            return res.status(404).end(errTxt);
          });
          res.setHeader('Content-Type', type?.mime ? type?.mime : '');
          s.pipe(res);
        } else {
          global.app.log.w(b?.data);
          return res.status(404).end(errTxt);
        }
      } catch (err) {
        global.app.log.w('Error on', req.url, err);
        return res.status(404).end(errTxt);
      }
    } else {
      return res.status(404).end(errTxt);
    }
  });
}

export default handler();
