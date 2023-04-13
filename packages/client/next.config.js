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
      'strtok3',
      'peek-readable',
      'token-types',
      '@tiptap/core',
      '@tiptap/extension-blockquote',
      '@tiptap/extension-bold',
      '@tiptap/extension-bubble-menu',
      '@tiptap/extension-bullet-list',
      '@tiptap/extension-code',
      '@tiptap/extension-code-block',
      '@tiptap/extension-document',
      '@tiptap/extension-dropcursor',
      '@tiptap/extension-floating-menu',
      '@tiptap/extension-gapcursor',
      '@tiptap/extension-hard-break',
      '@tiptap/extension-heading',
      '@tiptap/extension-highlight',
      '@tiptap/extension-history',
      '@tiptap/extension-horizontal-rule',
      '@tiptap/extension-italic',
      '@tiptap/extension-list-item',
      '@tiptap/extension-ordered-list',
      '@tiptap/extension-paragraph',
      '@tiptap/extension-placeholder',
      '@tiptap/extension-strike',
      '@tiptap/extension-text',
      '@tiptap/extension-typography',
      '@tiptap/pm',
      '@tiptap/react',
      '@tiptap/starter-kit',
      'prosemirror-changeset',
      'prosemirror-collab',
      'prosemirror-commands',
      'prosemirror-dropcursor',
      'prosemirror-gapcursor',
      'prosemirror-history',
      'prosemirror-inputrules',
      'prosemirror-keymap',
      'prosemirror-markdown',
      'prosemirror-menu',
      'prosemirror-model',
      'prosemirror-schema-basic',
      'prosemirror-schema-list',
      'prosemirror-state',
      'prosemirror-tables',
      'prosemirror-trailing-node',
      'prosemirror-transform',
      'prosemirror-view',
      'orderedmap',
      'w3c-keyname',
      'rope-sequence',
      'markdown-it',
      'crelt',
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
