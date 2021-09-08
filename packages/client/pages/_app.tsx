import '../semantic/dist/semantic.css';
import '../style/global.css';
import 'animate.css';
import 'react-virtualized/styles.css';
import 'nprogress/css/nprogress.css';

import App, { AppContext, AppInitialProps, AppProps } from 'next/app';
import dynamic from 'next/dynamic';
import Router, { useRouter } from 'next/router';
import NProgress from 'nprogress';
import { useEffect, useState } from 'react';
import { DndProvider } from 'react-dnd';
import { HTML5Backend } from 'react-dnd-html5-backend';
import { QueryClientProvider, useIsFetching } from 'react-query';
import { ReactQueryDevtools } from 'react-query/devtools';
import { RecoilRoot } from 'recoil';

import { queryClient } from '../client/queries';
import { LoginModal } from '../components/Login';
import { ServiceType } from '../services/constants';
import { AppState } from '../state';

const Theme = dynamic(() => import('../components/Theme'), { ssr: false });
interface AppPageProps extends AppInitialProps {
  pageProps: {
    loggedIn: boolean;
    sameMachine: boolean;
  };
}

function Progress() {
  const router = useRouter();
  const isFetching = useIsFetching({
    predicate: (q) => {
      // TODO: filter out status ping query
      return true;
    },
  });
  const [started, setStarted] = useState(false);

  useEffect(() => {
    NProgress.configure({ showSpinner: false });

    router.events.on('routeChangeStart', () => {
      NProgress.start();
    });

    router.events.on('routeChangeComplete', () => {
      NProgress.done();
    });
  }, []);

  useEffect(() => {
    if (isFetching) {
      if (!started) {
        NProgress.start();
        setStarted(true);
      }
    } else {
      NProgress.done();
      setStarted(false);
    }
  }),
    [isFetching];

  return null;
}

export function AppRoot({
  children,
  pageProps,
}: {
  children: React.ReactNode;
  pageProps?: AppPageProps['pageProps'];
}) {
  return (
    <QueryClientProvider client={queryClient}>
      <RecoilRoot
        initializeState={(snapshot) => {
          if (pageProps.loggedIn) {
            snapshot.set(AppState.loggedIn, pageProps.loggedIn);
            snapshot.set(AppState.sameMachine, pageProps.sameMachine);
          }
        }}>
        <DndProvider backend={HTML5Backend}>
          <Progress />
          {children}
        </DndProvider>
      </RecoilRoot>
      <ReactQueryDevtools initialIsOpen={false} />
    </QueryClientProvider>
  );
}

function MyApp({ Component, pageProps }: AppProps<AppPageProps['pageProps']>) {
  const router = useRouter();

  return (
    <AppRoot pageProps={pageProps}>
      {!['/login', '/_error'].includes(router.pathname) && <LoginModal />}
      <Theme>
        <Component {...pageProps} />
      </Theme>
    </AppRoot>
  );
}

function redirect(params: {
  ctx: AppContext['ctx'];
  location: string;
  status?: number;
}) {
  const { ctx, location, status = 307 } = params;

  if (ctx.res) {
    ctx.res.writeHead(status, {
      Location: location,
      // Add the content-type for SEO considerations
      'Content-Type': 'text/html; charset=utf-8',
    });
    ctx.res.end();
    return;
  }

  Router.replace(location, undefined);
}

MyApp.getInitialProps = async function (
  context: AppContext
): Promise<AppPageProps> {
  let loggedIn = false;
  let sameMachine = false;
  if (global.app.IS_SERVER) {
    sameMachine =
      context.ctx.req.socket.localAddress ===
      context.ctx.req.socket.remoteAddress;
    const server = global.app.service.get(ServiceType.Server);
    loggedIn = server.logged_in;

    if (!loggedIn && !['/login', '/_error'].includes(context.router.pathname)) {
      return redirect({
        location: `/login?next=${encodeURI(context.router.asPath)}`,
        ctx: context.ctx,
      }) as any;
    }
  }

  const props = await App.getInitialProps(context);

  return { ...props, pageProps: { ...props.pageProps, loggedIn, sameMachine } };
};

export default MyApp;

const IS_SERVER = typeof window === 'undefined';

if (!global?.app?.initialized && process.env.NODE_ENV !== 'test') {
  if (!IS_SERVER) {
    const { clientInitialize } = await import('../misc/initialize/client');
    await clientInitialize();
  }
}
