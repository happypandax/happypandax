import classNames from 'classnames';
import { useCallback, useEffect } from 'react';
import { DndProvider } from 'react-dnd';
import { HTML5Backend } from 'react-dnd-html5-backend';
import { useRecoilState, useRecoilValue } from 'recoil';
import { Button, Container, Dimmer, Sidebar } from 'semantic-ui-react';

import { useBreakpoints } from '../../client/hooks/ui';
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
  fluid,
  className,
}: {
  children?: React.ReactNode;
  fluid?: boolean;
  className?: string;
}) {
  return (
    <div
      id="bottom_zone"
      className={classNames(className, {
        fluid,
      })}
    >
      <div>{children}</div>
    </div>
  );
}

function useBodyStyles() {
  const { isTablet, isMobileMax, isComputer, isWidescreenMonitor } =
    useBreakpoints();
  const sidebarPosition = useRecoilValue(AppState.sidebarPosition);
  const sidebarHidden = useRecoilValue(AppState.sidebarHidden);

  useEffect(() => {
    const body = document.body;
    body.classList.toggle('tablet', isTablet);
    body.classList.toggle('mobile', isMobileMax);
    body.classList.toggle('computer', isComputer);
    body.classList.toggle('widescreen', isWidescreenMonitor);

    body.classList.toggle('sidebar-left', sidebarPosition === 'left');
    body.classList.toggle('sidebar-right', sidebarPosition === 'right');
    body.classList.toggle('sidebar-hidden', sidebarHidden);
  }, [
    isTablet,
    isMobileMax,
    isComputer,
    isWidescreenMonitor,
    sidebarPosition,
    sidebarHidden,
  ]);
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
  useBodyStyles();

  const drawerButtonPosition = useRecoilValue(AppState.drawerButtonPosition);
  const { isTabletMax } = useBreakpoints();
  const [sidebarHidden, setSidebarHidden] = useRecoilState(
    AppState.sidebarHidden
  );
  const [sidebarPosition, setSidebarPosition] = useRecoilState(
    AppState.sidebarPosition
  );
  const sidebarForcePosition = useRecoilValue(AppState.sidebarForcePosition);

  useEffect(() => {
    if (isTabletMax) {
      console.debug({ isMobileMax: isTabletMax });
      setSidebarHidden(isTabletMax);
    } else {
      console.debug({ isMobileMax: isTabletMax });
      setSidebarHidden(false);
    }
    if (!sidebarForcePosition) {
      setSidebarPosition(isTabletMax ? 'right' : 'left');
    }
  }, [isTabletMax, sidebarForcePosition]);

  useEffect(() => {
    if (sidebarForcePosition) {
      setSidebarPosition(sidebarForcePosition);
    }
  }, [sidebarForcePosition]);

  const sidebarEl = (
    <MainSidebar
      hidden={sidebarHidden}
      direction={sidebarPosition}
      onlyIcons={isTabletMax ? true : undefined}
      onHide={useCallback(() => {
        if (isTabletMax) {
          setSidebarHidden(true);
        }
      }, [isTabletMax])}
    />
  );

  const innerSidebar = isTabletMax || sidebarPosition === 'right';

  return (
    <>
      {!innerSidebar && sidebarEl}
      {menu}
      <DndProvider backend={HTML5Backend}>
        <Sidebar.Pusher
          as={Dimmer.Dimmable}
          dimmed={dimmed}
          className={classNames()}
        >
          {innerSidebar && sidebarEl}
          <Dimmer simple active={dimmed} />
          {centered && <Container>{children}</Container>}
          {!centered && children}
          <DrawerPortal />
        </Sidebar.Pusher>
        <BottomZone className="pusher" fluid={sidebarHidden}>
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
