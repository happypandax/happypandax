import '../semantic/dist/semantic.css';
import '../style/global.css';
import 'animate.css';
import 'react-virtualized/styles.css';

import App, { AppContext, AppInitialProps, AppProps } from 'next/app';
import dynamic from 'next/dynamic';
import { useMemo } from 'react';
import { DndProvider } from 'react-dnd';
import { HTML5Backend } from 'react-dnd-html5-backend';
import { QueryClient, QueryClientProvider } from 'react-query';
import { ReactQueryDevtools } from 'react-query/devtools';
import { RecoilRoot } from 'recoil';

import { ServiceType } from '../services/constants';

const Theme = dynamic(() => import('../components/Theme'), { ssr: false });
interface AppPageProps extends AppInitialProps {
  pageProps: {};
}

export function AppRoot({ children }: { children: React.ReactNode }) {
  console.log('yes');
  const queryClient = useMemo(() => {
    return new QueryClient({
      defaultOptions: {
        queries: {
          staleTime:
            process.env.NODE_ENV === 'development'
              ? Infinity
              : 1000 * 60 * 60 * 6,
        },
      },
    });
  }, []);

  return (
    <QueryClientProvider client={queryClient}>
      <RecoilRoot>
        <DndProvider backend={HTML5Backend}>
          <Theme>{children}</Theme>
        </DndProvider>
      </RecoilRoot>
      <ReactQueryDevtools initialIsOpen={false} />
    </QueryClientProvider>
  );
}

function MyApp({ Component, pageProps }: AppProps<AppPageProps['pageProps']>) {
  return (
    <AppRoot>
      <Component {...pageProps} />
    </AppRoot>
  );
}

MyApp.getInitialProps = async function (
  context: AppContext
): Promise<AppPageProps> {
  const props = await App.getInitialProps(context);

  if (global.app.IS_SERVER) {
    const server = global.app.service.get(ServiceType.Server);

    if (
      !server.logged_in &&
      !['/login', '/_error'].includes(context.router.pathname)
    ) {
      context.ctx.res.writeHead(307, {
        Location: `/login?next=${encodeURI(context.router.asPath)}`,
      });
      context.ctx.res.end();

      return props;
    }
  }

  return props;
};

export default MyApp;

const IS_SERVER = typeof window === 'undefined';

if (!global?.app?.initialized && process.env.NODE_ENV !== 'test') {
  if (!IS_SERVER) {
    const { clientInitialize } = await import('../misc/initialize/client');
    await clientInitialize();
  }
}
