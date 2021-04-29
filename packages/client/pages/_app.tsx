import type { AppProps } from 'next/app';
import setupLogger from '../misc/logger';

import '../semantic/dist/semantic.css';
import 'animate.css';
import 'react-virtualized/styles.css';
import { Theme } from '../components/Misc';

function MyApp({ Component, pageProps }: AppProps) {
  return (
    <Theme>
      <Component {...pageProps} />
    </Theme>
  );
}

global.app = {
  IS_SERVER: typeof window === 'undefined',
  title: 'HappyPanda X',
  log: setupLogger(),
} as any;

export default MyApp;
