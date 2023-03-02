const path = require('path');
const glob = require('glob');
const fs = require('fs');
const { compile } = require('nexe');
// const { version } = require('./package.json');

const name = 'happypandax_client';
const outputDir = 'dist';
const nodeVersion = '18.14.0';

compile({
  input: './main.js',
  output: path.join(outputDir, name),
  build: false, //required to be true to use patches
  remote: 'https://github.com/urbdyn/nexe_builds/releases/download/0.3.0/',
  targets: [
    {
      version: nodeVersion,
    },
  ],
  //   patches: [
  //     async (compiler, next) => {
  //       await compiler.setFileContentsAsync(
  //         'lib/new-native-module.js',
  //         'module.exports = 42'
  //       )
  //       return next()
  //     }
  //   ]
  resources: [
    'public/**/*',
    'next.config.js',
    './.next/**/*',
    'node_modules/**/*',
  ],
  temp: 'build/.nexe',
}).then(() => {
  const cwd = __dirname;

  const nativeModules = glob.sync('node_modules/**/*.node', {
    cwd,
    absolute: false,
  });

  if (nativeModules.length > 0) {
    console.log(
      `Copying ${nativeModules.length} native modules to ${outputDir}...`
    );

    nativeModules.forEach((module) => {
      console.log(`Copying native module: ${module}`);
      const modulePath = path.join(cwd, module);

      const moduleDir = path.join(outputDir, path.dirname(module));
      // create module dir in output dir if it doesn't exist
      if (!fs.existsSync(moduleDir)) {
        fs.mkdirSync(moduleDir, {
          recursive: true,
        });
      }

      const moduleOutputPath = path.join(outputDir, module);
      fs.copyFileSync(modulePath, moduleOutputPath);
    });
  }

  console.log('Success!');
});
