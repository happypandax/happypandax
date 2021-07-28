import classNames from 'classnames';
import { useCallback } from 'react';
import { DndProvider } from 'react-dnd';
import { HTML5Backend } from 'react-dnd-html5-backend';
import { useRecoilState } from 'recoil';
import { Dimmer, Portal, Sidebar } from 'semantic-ui-react';

import { AppState } from '../../state';
import DrawerPortal from '../Drawer';
import { DrawerButton, ScrollUpButton } from '../Misc';
import MainSidebar from '../Sidebar';

export function BottomZoneItem({
  children,
  x,
  y,
  className,
}: {
  className?: string;
  children?: React.ReactNode;
  x: 'left' | 'right';
  y: 'top' | 'bottom';
}) {
  return <div className={classNames('item', x, y, className)}>{children}</div>;
}

export function BottomZone({ children }: { children?: React.ReactNode }) {
  return (
    <Portal open>
      <div id="bottom_zone">
        <div>{children}</div>
      </div>
    </Portal>
  );
}

export default function PageLayout({
  dimmed,
  menu,
  bottomZone,
  children,
}: {
  dimmed?: boolean;
  menu?: React.ReactNode;
  bottomZone?: React.ReactNode;
  children?: React.ReactNode;
}) {
  const [drawerOpen, setDrawerOpen] = useRecoilState(AppState.drawerOpen);

  return (
    <>
      <MainSidebar />
      {menu}
      <Sidebar.Pusher
        as={Dimmer.Dimmable}
        dimmed={dimmed}
        className={classNames()}>
        <Dimmer simple active={dimmed} />
        <DndProvider backend={HTML5Backend}>
          {children}
          <DrawerPortal
            open={drawerOpen}
            onClose={useCallback(() => setDrawerOpen(false), [])}
          />
          <BottomZone>
            <BottomZoneItem x="left" y="bottom">
              <DrawerButton />
            </BottomZoneItem>
            <BottomZoneItem x="right" y="top" className="flex fullheight">
              {bottomZone}
              <ScrollUpButton />
            </BottomZoneItem>
          </BottomZone>
        </DndProvider>
      </Sidebar.Pusher>
    </>
  );
}
