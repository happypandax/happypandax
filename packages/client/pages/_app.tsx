import type { AppProps } from 'next/app';
import dynamic from 'next/dynamic';
import setupLogger from '../misc/logger';

import '../semantic/dist/semantic.css';
import '../style/global.css';
import 'animate.css';
import 'react-virtualized/styles.css';

const Theme = dynamic(() => import('../components/Theme'), { ssr: false });

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
