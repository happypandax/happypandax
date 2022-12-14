import 'server-only';
import '../public/semantic/semantic.css';
import '../style/global.css';
import 'animate.css';
import 'react-virtualized/styles.css';
import 'nprogress/css/nprogress.css';

import { Session } from 'better-sse';

import { MomoAction } from '../misc/enums';
import { serverInitialize } from '../misc/initialize/server';
import { NotificationData, ServerUser } from '../misc/types';

async function getInitiallProps() {
    let loggedIn = false;
    let sameMachine =  await fetch("/api/server/momo", {
        body: {
            action: MomoAction.SAME_MACHINE
        }
    });

    let connected = false;
    let user: ServerUser | null = null;
    let session: Session;
    let notifications: NotificationData[] = [];

    sameMachine =
      context.ctx.req.socket.localAddress ===
      context.ctx.req.socket.remoteAddress;
    const server = global.app.service.get(ServiceType.Server);

    const s = server.status();
    connected = s.connected;
    loggedIn = s.loggedIn;

    user = s.loggedIn
      ? await server.user({}, undefined, { cache: true })
      : null;

    if (!loggedIn && !['/login', '/_error'].includes(context.router.pathname)) {
      return redirect({
        location: `/login?next=${encodeURIComponent(context.router.asPath)}`,
        ctx: context.ctx,
      }) as any;
    }

    session = await getSession(context.ctx.req, context.ctx.res);
    const fairy = global.app.service.get(ServiceType.Fairy);
    notifications = fairy.get(session?.id);

}

export default function RootLayout({
    // Layouts must accept a children prop.
    // This will be populated with nested layouts or pages
    children,
  }: {
    children: React.ReactNode;
  }) {
    return (
      <html lang="en">
        <body>{children}</body>
      </html>
    );
  }
  
if (!global?.app?.initialized && process.env.NODE_ENV !== 'test') {
    await serverInitialize();
}
