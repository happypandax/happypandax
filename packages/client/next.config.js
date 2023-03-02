const { merge } = require('webpack-merge');

const nextConfig = (phase, { defaultConfig }) => {
  /** @type {import('next').NextConfig} */
  const config = {
    // output: phase === PHASE_PRODUCTION_BUILD ? 'standalone' : undefined,
    poweredByHeader: false,
    swcMinify: true,
    experimental: {
      appDir: false,
    },
    transpilePackages: [],
    typescript: {
      ignoreBuildErrors: true,
    },
    images: {},
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

  return config;
};

module.exports = nextConfig;
