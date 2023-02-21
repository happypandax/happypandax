const path = require('path');
const { merge } = require('webpack-merge');
const {
  PHASE_PRODUCTION_BUILD,
  PHASE_PRODUCTION_SERVER,
} = require('next/constants');

const nextConfig = (phase, { defaultConfig }) => {
  /** @type {import('next').NextConfig} */
  const config = {
    output: phase === PHASE_PRODUCTION_BUILD ? 'standalone' : undefined,
    poweredByHeader: false,
    swcMinify: true,
    experimental: {
      appDir: false,
      // this includes files from the monorepo base two directories up
      // outputFileTracingRoot: path.join(__dirname, '../../'),
      // outputFileTracingIncludes: {
      //   '*': ['../../node_modules/next/dist/server/**/*'],
      // },
    },
    transpilePackages: [
      PHASE_PRODUCTION_BUILD,
      PHASE_PRODUCTION_SERVER,
    ].includes(phase)
      ? [
          '@tanstack/query-core',
          '@tanstack/react-query',
          '@tanstack/react-query-devtools',
          'next-connect',
          'axios',
        ]
      : [],
    typescript: {
      ignoreBuildErrors: true,
    },
    images: {
      // domains: ['via.placeholder.com'],
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

  return config;
};

module.exports = nextConfig;
