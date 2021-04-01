import { Dimmer, Segment, Sidebar } from 'semantic-ui-react';
import MainSidebar from '../Sidebar';
import MainMenu from '../Menu';

export default function PageLayout({
  dimmed,
  children,
}: {
  dimmed?: boolean;
  children?: React.ReactNode;
}) {
  return (
    <>
      <MainSidebar />
      <Sidebar.Pusher
        as={Dimmer.Dimmable}
        dimmed={dimmed}
        className="force-viewport-size">
        <Dimmer simple active={dimmed} />
        {children}
      </Sidebar.Pusher>
    </>
  );
}
