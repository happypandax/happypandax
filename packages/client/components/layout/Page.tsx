import classNames from 'classnames';
import { DndProvider } from 'react-dnd';
import { HTML5Backend } from 'react-dnd-html5-backend';
import { Button, Container, Dimmer, Portal, Sidebar } from 'semantic-ui-react';

import t from '../../misc/lang';
import DrawerPortal, { DrawerButton } from '../Drawer';
import { ScrollUpButton } from '../Misc';
import MainSidebar from '../Sidebar';

export function PageSettingsButton(props: React.ComponentProps<typeof Button>) {
  return (
    <Button
      icon="cog"
      primary
      circular
      basic
      color="black"
      title={t`Settings`}
      {...props}
    />
  );
}

export function BottomZoneItem({
  children,
  x,
  y,
  className,
}: {
  className?: string;
  children?: React.ReactNode;
  x: 'left' | 'right' | 'center';
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
  basicDrawerButton,
  bottomZoneRight,
  bottomZoneLeft,
  bottomZoneLeftBottom,
  bottomZoneRightBottom,
  centered,
  bottomZone,
  children,
}: {
  basicDrawerButton?: boolean;
  centered?: boolean;
  dimmed?: boolean;
  menu?: React.ReactNode;
  bottomZoneLeft?: React.ReactNode;
  bottomZoneLeftBottom?: React.ReactNode;
  bottomZoneRightBottom?: React.ReactNode;
  bottomZoneRight?: React.ReactNode;
  bottomZone?: React.ReactNode;
  children?: React.ReactNode;
}) {

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
          {centered && <Container>{children}</Container>}
          {!centered && children}
          <DrawerPortal
          />
          <BottomZone>
            {bottomZone}
            <BottomZoneItem x="left" y="top" className="flex">
              {bottomZoneLeft}
            </BottomZoneItem>
            <BottomZoneItem x="right" y="top" className="flex">
              {bottomZoneRight}
            </BottomZoneItem>
            <BottomZoneItem x="left" y="bottom">
              <DrawerButton basic={basicDrawerButton} />
              {bottomZoneLeftBottom}
            </BottomZoneItem>
            <BottomZoneItem x="right" y="bottom">
              {bottomZoneRightBottom}
              <ScrollUpButton />
            </BottomZoneItem>
          </BottomZone>
        </DndProvider>
      </Sidebar.Pusher>
    </>
  );
}
