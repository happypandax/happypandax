import 'server-only';
import '../public/semantic/semantic.css';
import '../style/global.css';
import 'animate.css';
import 'react-virtualized/styles.css';
import 'nprogress/css/nprogress.css';

import Theme from '../components/Theme';
import { ServiceType } from '../server/constants';
import { serverInitialize } from '../server/initialize';
import { fetchQuery } from '../server/requests';
import { MomoType } from '../shared/query';
import { NotificationData } from '../shared/types';
import { AppRoot } from './client';

async function getInitiallProps() {
  const server = global.APP.service.get(ServiceType.Server);
  const fairy = global.app.service.get(ServiceType.Fairy);

  const s = server.status();
  const connected = s.connected;
  const loggedIn = s.loggedIn;

  const sameMachine = await (await fetchQuery(MomoType.SAME_MACHINE)).data;

  const user = s.loggedIn
    ? await server.user({}, undefined, { cache: true })
    : null;

  // const  session = await getSession(context.ctx.req, context.ctx.res);
  let notifications: NotificationData[] = [];

  // notifications = fairy.get(session?.id);

  // if (!loggedIn) {
  //   // No way to get the current path in NextJS app 'directory' yet
  //   const n = ''; // encodeURIComponent(context.router.asPath)
  //   redirect(`/login?next=${n}`);
  // }

  return {
    connected,
    loggedIn,
    sameMachine,
    user,
    notifications,
  };
}

export default async function RootLayout({
  // Layouts must accept a children prop.
  // This will be populated with nested layouts or pages
  children,
}: {
  children: React.ReactNode;
}) {
  const pageProps = await getInitiallProps();

  return (
    <html lang="en">
      <body>
        {
          <AppRoot pageProps={pageProps}>
            <Theme>{children}</Theme>
          </AppRoot>
        }
      </body>
    </html>
  );
}

if (!global?.app?.initialized && process.env.NODE_ENV !== 'test') {
  await serverInitialize();
}
