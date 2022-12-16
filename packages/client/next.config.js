const { merge } = require('webpack-merge');

/** @type {import('next').NextConfig} */
const config = {
  poweredByHeader: false,
  swcMinify: true,
  experimental: {
    appDir: true,
  },
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

module.exports = config;
