import '../public/semantic/semantic.css';
import '../style/global.css';
import 'animate.css';
import 'react-virtualized/styles.css';
import 'nprogress/css/nprogress.css';

import App, { AppContext, AppInitialProps, AppProps } from 'next/app';
import dynamic from 'next/dynamic';
import Router, { useRouter } from 'next/router';
import NProgress from 'nprogress';
import { useEffect, useRef, useState } from 'react';
import { DndProvider } from 'react-dnd';
import { HTML5Backend } from 'react-dnd-html5-backend';
import { QueryClientProvider, useIsFetching } from 'react-query';
import { ReactQueryDevtools } from 'react-query/devtools';
import { RecoilRoot, useRecoilState, useSetRecoilState } from 'recoil';

import { queryClient } from '../client/queries';
import { LoginModal } from '../components/Login';
import { getSession } from '../misc/requests';
import { NotificationData } from '../misc/types';
import { ServiceType } from '../services/constants';
import { AppState } from '../state';
import { useGlobalValue, useSetGlobalState } from '../state/global';

const Theme = dynamic(() => import('../components/Theme'), { ssr: false });
interface AppPageProps extends AppInitialProps {
  pageProps: {
    notifications: NotificationData[];
    loggedIn: boolean;
    connected: boolean;
    sameMachine: boolean;
  };
}

function Fairy() {
  const [notificationAlert, setNotificatioAlert] = useRecoilState(
    AppState.notificationAlert
  );
  const [notifications, setNotifications] = useRecoilState(
    AppState.notifications
  );
  const setLoggedIn = useSetGlobalState('loggedIn');
  const setConnected = useSetGlobalState('connected');

  const [fairy, setFairy] = useState<EventSource>();

  const notificationAlertRef = useRef(notificationAlert);
  const notificationsRef = useRef(notifications);

  useEffect(() => {
    if (!fairy) return;

    const onStatus = ({ data }: any) => {
      const d: any = JSON.parse(data);
      setLoggedIn(d.loggedIn);
      setConnected(d.connected);
    };
    fairy.addEventListener('status', onStatus);

    return () => {
      fairy.removeEventListener('status', onStatus);
    };
  }, [fairy]);

  useEffect(() => {
    if (!fairy) return;
    const onNotif = ({ data }: any) => {
      const d: NotificationData = JSON.parse(data);
      if (d.date) {
        d.date = new Date(d.date);
      }
      setNotificatioAlert([d, ...notificationAlertRef.current]);
      setNotifications([d, ...notificationsRef.current]);
    };

    fairy.addEventListener('notification', onNotif);

    return () => {
      fairy.removeEventListener('notification', onNotif);
    };
  }, [fairy]);

  useEffect(() => {
    setFairy(new EventSource('/api/server/fairy'));
  }, []);

  useEffect(() => {
    notificationAlertRef.current = notificationAlert;
  }, [notificationAlert]);

  useEffect(() => {
    notificationsRef.current = notifications;
  }, [notifications]);

  return null;
}

function AppProgress() {
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

/**
 * Since we make use of recoil selectors, we need to have both recoil and global states, synced
 */
function ItemActivity() {
  const setItemActivityMap = useSetRecoilState(AppState.itemActivityState);
  const activity = useGlobalValue('activity');

  useEffect(() => {
    setItemActivityMap({ ...activity });
  }, [activity]);

  return null;
}

function AppInit() {
  return (
    <>
      <AppProgress />
      <Fairy />
      <ItemActivity />
    </>
  );
}

export function AppRoot({
  children,
  pageProps,
}: {
  children: React.ReactNode;
  pageProps?: AppPageProps['pageProps'];
}) {
  const setConnected = useSetGlobalState('connected');
  const setLoggedIn = useSetGlobalState('loggedIn');
  const setSameMachine = useSetGlobalState('sameMachine');

  useEffect(() => {
    setConnected(pageProps.connected);
    setLoggedIn(pageProps.loggedIn);
    setSameMachine(pageProps.sameMachine);
  }, [pageProps]);

  return (
    <QueryClientProvider client={queryClient}>
      <RecoilRoot initializeState={(snapshot) => {}}>
        <DndProvider backend={HTML5Backend}>
          <AppInit />
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
  let connected = false;
  if (global.app.IS_SERVER) {
    sameMachine =
      context.ctx.req.socket.localAddress ===
      context.ctx.req.socket.remoteAddress;
    const server = global.app.service.get(ServiceType.Server);

    const s = server.status();
    connected = s.connected;
    loggedIn = s.loggedIn;

    if (!loggedIn && !['/login', '/_error'].includes(context.router.pathname)) {
      return redirect({
        location: `/login?next=${encodeURIComponent(context.router.asPath)}`,
        ctx: context.ctx,
      }) as any;
    }
  }

  const props = await App.getInitialProps(context);

  const session = await getSession(context.ctx.req, context.ctx.res);
  const fairy = global.app.service.get(ServiceType.Fairy);

  return {
    ...props,
    pageProps: {
      ...props.pageProps,
      loggedIn,
      sameMachine,
      connected,
      notifications: fairy.get(session.id),
    },
  };
};

export default MyApp;

const IS_SERVER = typeof window === 'undefined';

if (!global?.app?.initialized && process.env.NODE_ENV !== 'test') {
  if (!IS_SERVER) {
    const { clientInitialize } = await import('../misc/initialize/client');
    await clientInitialize();
  }
}
