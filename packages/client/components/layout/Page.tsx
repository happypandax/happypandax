import { Dimmer, Segment, Sidebar } from 'semantic-ui-react';
import { DndProvider } from 'react-dnd';
import { HTML5Backend } from 'react-dnd-html5-backend';
import MainSidebar from '../Sidebar';

export default function PageLayout({
  dimmed,
  menu,
  children,
}: {
  dimmed?: boolean;
  menu?: React.ReactNode;
  children?: React.ReactNode;
}) {
  return (
    <>
      <MainSidebar />
      {menu}
      <Sidebar.Pusher
        as={Dimmer.Dimmable}
        dimmed={dimmed}
        className="force-viewport-size">
        <Dimmer simple active={dimmed} />
        <DndProvider backend={HTML5Backend}>{children}</DndProvider>
      </Sidebar.Pusher>
    </>
  );
}
