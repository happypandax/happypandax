import '../semantic/dist/semantic.css';
import '../style/global.css';
import 'animate.css';
import 'react-virtualized/styles.css';

import { GetServerSidePropsResult, NextPageContext } from 'next';
import dynamic from 'next/dynamic';
import { RecoilRoot } from 'recoil';

import setupLogger from '../misc/logger';
import { ServiceType } from '../services/constants';
import setupServices from '../services/index';

import type { AppProps } from 'next/app';
const Theme = dynamic(() => import('../components/Theme'), { ssr: false });
interface PageProps {}

export async function getServerSideProps(
  context: NextPageContext
): Promise<GetServerSidePropsResult<PageProps>> {
  const server = global.app.service.get(ServiceType.Server);

  if (global.app.IS_SERVER && !global.app.service) {
    global.app.service = setupServices();
  }

  console.log(server.logged_in);

  return {
    props: {},
    redirect: server.logged_in
      ? undefined
      : { permanent: false, destination: '/login' },
  };
}

function MyApp({ Component, pageProps }: AppProps<PageProps>) {
  return (
    <RecoilRoot>
      <Theme>
        <Component {...pageProps} />
      </Theme>
    </RecoilRoot>
  );
}

global.app = {
  IS_SERVER: typeof window === 'undefined',
  title: 'HappyPanda X',
  log: setupLogger(),
} as any;

export default MyApp;
