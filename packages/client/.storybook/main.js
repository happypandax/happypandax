const { merge } = require('webpack-merge');

module.exports = {
  core: {
    builder: 'webpack5',
  },
  stories: [
    '../(pages|components)/**/*.stories.mdx',
    '../(pages|components)/**/*.stories.@(js|jsx|ts|tsx)',
  ],
  addons: [
    '@storybook/addon-links',
    '@storybook/addon-essentials',
    'storybook-addon-themes',
    'storybook-css-modules-preset',
  ],
  webpackFinal: async (config, { configType }) => {
    // `configType` has a value of 'DEVELOPMENT' or 'PRODUCTION'
    // You can change the configuration based on that.
    // 'PRODUCTION' is used when building the static version of storybook.

    config = merge(config, {
      experiments: {
        topLevelAwait: true,
      },
    });
    // Return the altered config
    return config;
  },
};
