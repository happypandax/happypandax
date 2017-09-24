const webpack = require('webpack');

const config = {
    entry:  __dirname + '/static/__javascript__/main.js',
    output: {
        path: __dirname + '/static/lib',
        filename: 'bundle.js',
    },
    resolve: {
        extensions: ['.js', '.jsx', '.css']
    },
};

module: {
  rules: [
    {
      test: /\.jsx?/,
      exclude: /node_modules/,
      use: 'babel-loader'
    }
  ]
}

module.exports = config;