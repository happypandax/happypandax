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
        <Head>
          <meta charSet="utf-8" />
          <meta
            name="viewport"
            content="width=device-width, initial-scale=1.0"
          />
          <link
            rel="apple-touch-icon"
            sizes="180x180"
            href="/favicon/apple-touch-icon.png?v=kPxXam0OO4"
          />
          <link
            rel="icon"
            type="image/png"
            sizes="32x32"
            href="/favicon/favicon-32x32.png?v=kPxXam0OO4"
          />
          <link
            rel="icon"
            type="image/png"
            sizes="16x16"
            href="/favicon/favicon-16x16.png?v=kPxXam0OO4"
          />
          <link rel="manifest" href="/favicon/site.webmanifest?v=kPxXam0OO4" />
          <link
            rel="mask-icon"
            href="/favicon/safari-pinned-tab.svg?v=kPxXam0OO4"
            color="#363636"
          />
          <link rel="shortcut icon" href="/favicon/favicon.ico?v=kPxXam0OO4" />
          <meta name="apple-mobile-web-app-title" content="HappyPanda X" />
          <meta name="application-name" content="HappyPanda X" />
          <meta name="msapplication-TileColor" content="#ffffff" />
          <meta
            name="msapplication-TileImage"
            content="/favicon/mstile-144x144.png?v=kPxXam0OO4"
          />
          <meta
            name="msapplication-config"
            content="/favicon/browserconfig.xml?v=kPxXam0OO4"
          />
          <meta name="theme-color" content="#ffffff" />
        </Head>
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
