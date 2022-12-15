import classNames from 'classnames';
import { DndProvider } from 'react-dnd';
import { HTML5Backend } from 'react-dnd-html5-backend';
import { useRecoilValue } from 'recoil';
import { Button, Container, Dimmer, Sidebar } from 'semantic-ui-react';

import t from '../../client/lang';
import { AppState } from '../../state';
import DrawerPortal, { DrawerButton } from '../Drawer';
import { ScrollUpButton } from '../misc';
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

export function BottomZone({
  children,
  className,
}: {
  children?: React.ReactNode;
  className?: string;
}) {
  return (
    <div id="bottom_zone" className={className}>
      <div>{children}</div>
    </div>
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
  const drawerButtonPosition = useRecoilValue(AppState.drawerButtonPosition);

  return (
    <>
      <MainSidebar />
      {menu}
      <DndProvider backend={HTML5Backend}>
        <Sidebar.Pusher
          as={Dimmer.Dimmable}
          dimmed={dimmed}
          className={classNames()}>
          <Dimmer simple active={dimmed} />
          {centered && <Container>{children}</Container>}
          {!centered && children}
          <DrawerPortal />
        </Sidebar.Pusher>
        <BottomZone className="pusher">
          {bottomZone}
          <BottomZoneItem x="left" y="top" className="flex">
            {bottomZoneLeft}
          </BottomZoneItem>
          <BottomZoneItem x="right" y="top" className="flex">
            {bottomZoneRight}
          </BottomZoneItem>
          <BottomZoneItem x="left" y="bottom">
            {drawerButtonPosition !== 'right' && (
              <DrawerButton basic={basicDrawerButton} />
            )}
            {bottomZoneLeftBottom}
          </BottomZoneItem>
          <BottomZoneItem x="right" y="bottom">
            {bottomZoneRightBottom}
            {drawerButtonPosition === 'right' && (
              <DrawerButton basic={basicDrawerButton} />
            )}
            <ScrollUpButton />
          </BottomZoneItem>
        </BottomZone>
      </DndProvider>
    </>
  );
}
