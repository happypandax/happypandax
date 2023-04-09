const { merge } = require('webpack-merge');
const pkg = require('./package.json');

const nextConfig = (phase, { defaultConfig }) => {
  /** @type {import('next').NextConfig} */
  const config = {
    // output: phase === PHASE_PRODUCTION_BUILD ? 'standalone' : undefined,
    poweredByHeader: false,
    env: {
      PACKAGE_JSON: JSON.stringify(pkg),
    },
    swcMinify: true,
    experimental: {
      appDir: false,
    },
    transpilePackages: [
      '@tanstack/query-core',
      '@tanstack/react-query',
      '@tanstack/react-query-devtools',
      'next-connect',
      'axios',
      'swiper',
      'ssr-window',
      'file-type',
    ],
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
