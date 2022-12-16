'use client';
import dynamic from 'next/dynamic';
import { usePathname, useRouter, useSearchParams } from 'next/navigation';
import NProgress from 'nprogress';
import { useEffect, useMemo, useRef, useState } from 'react';
import { DndProvider } from 'react-dnd';
import { HTML5Backend } from 'react-dnd-html5-backend';
import { RecoilRoot, useRecoilState, useSetRecoilState } from 'recoil';

import { QueryClientProvider, useIsFetching } from '@tanstack/react-query';
import { ReactQueryDevtools } from '@tanstack/react-query-devtools';

import { clientInitialize } from '../client/initialize';
import { queryClient } from '../client/queries';
import { LoginModal } from '../components/Login';
import { NotificationData, ServerUser } from '../shared/types';
import { AppState } from '../state';
import { useGlobalValue, useSetGlobalState } from '../state/global';

const Theme = dynamic(() => import('../components/Theme'), { ssr: false });
interface PageProps {
  notifications: NotificationData[];
  user: ServerUser | null;
  loggedIn: boolean;
  connected: boolean;
  sameMachine: boolean;
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
  const pathname = usePathname();
  const searchParams = useSearchParams();

  useMemo(() => {
    NProgress.configure({ showSpinner: false });
    window.addEventListener('DOMContentLoaded', (event) => {
      NProgress.done();
    });
  }, []);

  useEffect(() => {
    NProgress.start();
  }, [pathname, searchParams]);

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
  pageProps?: PageProps;
}) {
  const pathname = usePathname();

  const setConnected = useSetGlobalState('connected');
  const setLoggedIn = useSetGlobalState('loggedIn');
  const setSameMachine = useSetGlobalState('sameMachine');
  const setUser = useSetGlobalState('user');

  useEffect(() => {
    setConnected(pageProps.connected);
    setLoggedIn(pageProps.loggedIn);
    setSameMachine(pageProps.sameMachine);
    setUser(pageProps.user);
  }, [pageProps]);

  return (
    <QueryClientProvider client={queryClient}>
      <RecoilRoot initializeState={(snapshot) => {}}>
        <DndProvider backend={HTML5Backend}>
          <AppInit />
          {!pageProps.loggedIn && pathname !== '/login' && <LoginModal />}
          {children}
        </DndProvider>
      </RecoilRoot>
      <ReactQueryDevtools initialIsOpen={false} />
    </QueryClientProvider>
  );
}

if (!global?.app?.initialized && process.env.NODE_ENV !== 'test') {
  await clientInitialize();
}
