module.exports = {
  stories: [
    '../(pages|components)/**/*.stories.mdx',
    '../(pages|components)/**/*.stories.@(js|jsx|ts|tsx)',
  ],
  addons: [
    '@storybook/addon-links',
    '@storybook/addon-essentials',
    'storybook-css-modules-preset',
  ],
};
