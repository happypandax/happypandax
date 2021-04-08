import type { AppProps } from 'next/app';
import setupLogger from '../misc/logger';

import '../semantic/dist/semantic.css';
import 'animate.css';

function MyApp({ Component, pageProps }: AppProps) {
  return <Component {...pageProps} />;
}

global.app = {
  IS_SERVER: typeof window === 'undefined',
  title: 'HappyPanda X',
  log: setupLogger(),
} as any;

export default MyApp;
