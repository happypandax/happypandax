import fs from 'fs';
import { readFile } from 'fs/promises';
import { Liquid } from 'liquidjs';
import onFinished from 'on-finished';
import path from 'path';
import send from 'send';

import { handler } from '../../../../../server/requests';
import { getPixie } from '../../../../../services/pixie';

let engine: Liquid;

/** pipe the send file stream from https://github.com/expressjs/express/blob/d0e166c3c6eaf80871b7f38839ea90e048452844/lib/response.js#L1021 */
function sendfile(res, file, options, callback) {
  let done = false;
  let streaming;

  // request aborted
  function onaborted() {
    if (done) return;
    done = true;

    var err = new Error('Request aborted');
    err.code = 'ECONNABORTED';
    callback(err);
  }

  // directory
  function ondirectory() {
    if (done) return;
    done = true;

    var err = new Error('EISDIR, read');
    err.code = 'EISDIR';
    callback(err);
  }

  // errors
  function onerror(err) {
    if (done) return;
    done = true;
    callback(err);
  }

  // ended
  function onend() {
    if (done) return;
    done = true;
    callback();
  }

  // file
  function onfile() {
    streaming = false;
  }

  // finished
  function onfinish(err) {
    if (err && err.code === 'ECONNRESET') return onaborted();
    if (err) return onerror(err);
    if (done) return;

    setImmediate(function () {
      if (streaming !== false && !done) {
        onaborted();
        return;
      }

      if (done) return;
      done = true;
      callback();
    });
  }

  // streaming
  function onstream() {
    streaming = true;
  }

  file.on('directory', ondirectory);
  file.on('end', onend);
  file.on('error', onerror);
  file.on('file', onfile);
  file.on('stream', onstream);
  onFinished(res, onfinish);

  if (options.headers) {
    // set headers on successful transfer
    file.on('headers', function headers(res) {
      let obj = options.headers;
      let keys = Object.keys(obj);

      for (let i = 0; i < keys.length; i++) {
        let k = keys[i];
        res.setHeader(k, obj[k]);
      }
    });
  }

  // pipe
  file.pipe(res);
}

const errTxt = "Momo didn't find anything!";

export default handler().all((req, res, next) => {
  getPixie()
    .then(async (pixie) => {
      console.debug({ req: req.url });
      const plugin = await pixie.plugin({ plugin_id: req.query.id as string });

      if (!plugin?.info?.site) {
        return res.status(404).end(errTxt);
      }

      let filePath = '/' + (req.query.path ?? '');

      if (filePath.endsWith('/')) {
        for (const f of ['index.html', 'index.htm']) {
          if (fs.existsSync(path.join(plugin.info.site, filePath + f))) {
            filePath += f;
            break;
          }
        }
      }

      if (!engine) {
        engine = new Liquid({
          cache: process.env.NODE_ENV === 'production',
          dynamicPartials: true,
          jekyllInclude: true,
          trimTagLeft: true,
          trimTagRight: true,
          trimOutputLeft: true,
          trimOutputRight: true,
          root: [plugin.default_site],
          globals: {
            __default__: 'base.html',
            dev: process.env.NODE_ENV !== 'production',
            version: plugin.version,
            version_web: plugin.version_web,
            version_db: plugin.version_db,
          },
          extname: '.html',
        });
      }

      let fpath = path.join(plugin.info.site, filePath);

      if (filePath.startsWith('/api')) {
        const defaultPath = path.join(plugin.default_site, filePath);
        if (fs.existsSync(defaultPath)) {
          fpath = defaultPath;
        }
      }

      const pathname = encodeURIComponent(fpath);

      if (fs.existsSync(fpath)) {
        if (fpath.endsWith('.html') || fpath.endsWith('.htm')) {
          readFile(fpath, { encoding: 'utf-8' })
            .then((data) => {
              return engine
                .parseAndRender(
                  data,
                  {
                    plugin_id: plugin.info.id,
                    plugin: {
                      id: plugin.info.id,
                      name: plugin.info.name,
                      version: plugin.info.version,
                      shortname: plugin.info.shortname,
                      author: plugin.info.author,
                      website: plugin.info.website,
                      description: plugin.info.description,
                    },
                  },
                  {}
                )
                .then((html) => {
                  res.writeHead(200, { 'Content-Type': 'text/html' }).end(html);
                });
            })
            .catch((err) => {
              let txt = errTxt;
              if (process.env.NODE_ENV !== 'production') {
                txt = JSON.stringify(err, null, 2);
              } else {
                console.error(err);
              }
              res.status(404).end(txt);
            });
          return;
        }

        const file = send(req, pathname, {});
        sendfile(res, file, {}, () => { });
      } else {
        res.status(404).end(errTxt);
      }
    })
    .catch((err) => {
      res.status(500).end(err.message);
    });
});
