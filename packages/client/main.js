const { defaultConfig } = require('next/dist/server/config-shared');
const NextServer = require('next/dist/server/next-server').default;
const http = require('http');
const dotenv = require('dotenv');
const { parseArgs } = require('util');
const nextConfigs = require('./next.config');
const _ = require('lodash');

const dir = __dirname;

process.env.NODE_ENV = 'production';
process.chdir(dir);

dotenv.config();

let hostname = 'localhost';
let port = 7008;

const {
  values: { host: cliHost, port: cliPort, env, help, cwd },
} = parseArgs({
  options: {
    host: {
      type: 'string',
      short: 'h',
      default: '',
    },
    port: {
      type: 'string',
      short: 'p',
      default: '',
    },
    env: {
      type: 'string',
      default: '',
    },
    cwd: {
      type: 'string',
      default: '',
    },
    help: {
      type: 'boolean',
      default: false,
    },
  },
});

if (help) {
  console.log(`Usage: happypandax_client [options]

Options:
  -h, --host      Hostname to listen on
  -p, --port      Port to listen on
  --cwd           Working directory (defaults to where the executable is)
  --env           Environment variables to load
  --help          Displays this message
`);
  process.exit(0);
}

if (env) {
  console.log(`> Loading environment variables from given env`);
  const envConfig = dotenv.parse(Buffer.from(env, 'utf8'));
  if (envConfig) {
    Object.entries(envConfig).forEach(([key, value]) => {
      process.env[key] = value;
    });
  }
}

Object.entries(process.env).forEach(([key, value]) => {
  if (key === 'HPX_HOST') {
    hostname = value;
  }

  if (key === 'HPX_PORT') {
    port = parseInt(value, 10);
  }
});

if (cwd) {
  console.log(`> Changing working directory to ${cwd}`);
  process.chdir(cwd);
}

if (cliHost) {
  hostname = cliHost;
}

if (cliPort) {
  port = parseInt(cliPort, 10);
}

// Make sure commands gracefully respect termination signals (e.g. from Docker)
// Allow the graceful termination to be manually configurable
if (!process.env.NEXT_MANUAL_SIG_HANDLE) {
  process.on('SIGTERM', () => process.exit(0));
  process.on('SIGINT', () => process.exit(0));
}

let handler;

const server = http.createServer(async (req, res) => {
  try {
    await handler(req, res);
  } catch (err) {
    console.error(err);
    res.statusCode = 500;
    res.end('Internal Momo Error (×﹏×)');
  }
});

const config = _.mergeWith(
  {},
  defaultConfig,
  nextConfigs(undefined, { defaultConfig: {} }),
  (objValue, srcValue) => {
    if (_.isArray(objValue)) {
      return srcValue;
    }
  }
);

server.listen(port, (err) => {
  if (err) {
    console.error('Failed to start server (×_×)', err);
    process.exit(1);
  }
  const nextServer = new NextServer({
    hostname,
    port,
    dir,
    dev: false,
    customServer: false,
    conf: {
      configFileName: 'next.config.js',
      ...config,
    },
  });
  handler = nextServer.getRequestHandler();

  console.log(
    '> Listening on port',
    port,
    '\n> url: http://' + hostname + ':' + port,
    '\n Ready! („• ᴗ •„)'
  );
});
