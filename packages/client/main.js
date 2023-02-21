// const { createServer } = require('http');
// const { parse } = require('url');
// const next = require('next');

// const dev = false;
// const hostname = 'localhost';
// const port = 7088;
// // when using middleware `hostname` and `port` must be provided below
// const app = next({
//   dev,
//   hostname,
//   port,
//   queit: false,
//   dir: '.',
//   conf: {
//     poweredByHeader: false,
//     experimental: {
//       appDir: false,
//     },
//   },
// });
// const handle = app.getRequestHandler();

// app
//   .prepare()
//   .then(() => {
//     createServer(async (req, res) => {
//       try {
//         // Be sure to pass `true` as the second argument to `url.parse`.
//         // This tells it to parse the query portion of the URL.
//         const parsedUrl = parse(req.url, true);
//         await handle(req, res, parsedUrl);
//       } catch (err) {
//         console.error('Error occurred handling', req.url, err);
//         res.statusCode = 500;
//         res.end('internal server error');
//       }
//     }).listen(port, (err) => {
//       if (err) throw err;
//       console.log(`> Ready on http://${hostname}:${port}`);
//     });
//   })
//   .catch((ex) => {
//     console.error('Failed to start');
//     console.error(ex.stack);
//     process.exit(1);
//   });

const { startServer } = require('next/dist/server/lib/start-server');
const path = require('path');

const dir = __dirname;

const hostname = 'localhost';
const port = 7088;

// log current working directory

startServer({
  dir,
  hostname,
  port,
})
  .then(() => {
    console.log(`> Ready on http://${hostname}:${port}`);
  })
  .catch((ex) => {
    console.error('Failed to start');
    console.error(ex.stack);
    process.exit(1);
  });
