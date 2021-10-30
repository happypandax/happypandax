const { merge } = require('webpack-merge');
const withTM = require('next-transpile-modules')([]);
const { PHASE_DEVELOPMENT_SERVER } = require('next/constants');

module.exports = (phase, { defaultConfig }) => {
  const config = {
    ...defaultConfig,
    poweredByHeader: false,
    swcMinify: true,
    typescript: {
      ignoreBuildErrors: true,
    },
    webpack: (wconfig, options) => {
      let cfg = {
        experiments: {
          topLevelAwait: true, // not supported by jest yet
        },
      };

      if (options.isServer) {
        cfg = {
          ...cfg,
        };
      } else {
        cfg = {
          ...cfg,
          resolve: {
            fallback: {
              // os: false,
              // net: false,
              // fs: false,
              // http: false,
            },
          },
        };
      }

      return merge(wconfig, cfg);
    },
  };

  function plugins(cfg) {
    return withTM(cfg);
  }

  if (phase === PHASE_DEVELOPMENT_SERVER) {
    return plugins({
      ...config,
      /* development only config options here */
    });
  }

  return plugins({
    ...config,
    /* config options for all phases except development here */
  });
};
