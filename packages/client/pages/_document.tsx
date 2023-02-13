import Document, { Head, Html, Main, NextScript } from 'next/document';

import { IS_SERVER } from '../server/constants';
import setupServices from '../services';

class MyDocument extends Document {
  static async getInitialProps(ctx) {
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



if (!global?.app?.initialized && process.env.NODE_ENV !== 'test') {
  if (IS_SERVER) {
    const { serverInitialize } = await import('../server/initialize');
    await serverInitialize();
  }
}

if (IS_SERVER && !global?.app?.initialized) {
  if (process.env.NODE_ENV === 'development') {
    global.app.service = await setupServices();
  }
}

export default MyDocument;
