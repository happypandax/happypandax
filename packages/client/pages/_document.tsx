import Document, { Head, Html, Main, NextScript } from 'next/document';

import setupServices from '../services';

class MyDocument extends Document {
  static async getInitialProps(ctx) {
    // TODO: put server initialization here, then it works well
    if (global.app.IS_SERVER && !global.app.service) {
      global.app.service = setupServices();
    }
    const initialProps = await Document.getInitialProps(ctx);
    return { ...initialProps };
  }

  render() {
    return (
      <Html>
        <Head />
        <body>
          <Main />
          <NextScript />
        </body>
      </Html>
    );
  }
}

export default MyDocument;
