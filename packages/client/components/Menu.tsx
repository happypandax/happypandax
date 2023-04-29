import classNames from 'classnames';
import { useCallback, useEffect, useRef, useState } from 'react';
import { useUpdateEffect } from 'react-use';
import { useRecoilState, useRecoilValue } from 'recoil';
import { Icon, IconProps, Menu, Ref } from 'semantic-ui-react';
import { SemanticICONS } from 'semantic-ui-react/dist/commonjs/generic';

import { useBreakpoints } from '../client/hooks/ui';
import { useDocumentEvent } from '../client/hooks/utils';
import { AppState } from '../state';
import { useGlobalValue } from '../state/global';
import styles from './Menu.module.css';
import { NotificationAlert, NotificationsPopup } from './popup/Notification';

export function MenuItem({
  className,
  icon,
  size = 'large',
  children,
  ...props
}: {
  icon?: SemanticICONS | IconProps;
  children?: React.ReactNode;
  className?: string;
  size?: IconProps['size'];
} & React.ComponentProps<typeof Menu.Item>) {
  //   const context = useContext(MenuContext);

  return (
    <Menu.Item className={classNames(className)} {...props}>
      {!!icon && (
        <Icon
          size={size}
          {...(typeof icon === 'string' ? { name: icon } : icon)}
          className={classNames(
            'left',
            typeof icon !== 'string' ? icon.className : ''
          )}
        />
      )}
      {children}
    </Menu.Item>
  );
}

export function ConnectionItem({
  position = 'right',
}: {
  position?: 'left' | 'right';
}) {
  const ref = useRef();
  const connected = useGlobalValue('connected');

  const [connectState, setConnectState] = useState<
    'connected' | 'connecting' | 'disconnected'
  >(connected ? 'connected' : 'connecting');

  useUpdateEffect(() => {
    if (!connected) {
      setConnectState('disconnected');
    } else {
      setConnectState('connected');
    }
  }, [connected]);

  const icon = (
    <Icon
      name="circle"
      color={
        connectState === 'connected'
          ? 'green'
          : connectState === 'connecting'
          ? 'orange'
          : 'red'
      }
      size="large"
      className={classNames(styles.connectionitem, {
        pulse: connectState === 'connecting',
      })}
    />
  );

  return (
    <>
      <NotificationAlert context={ref} />
      <NotificationsPopup
        trigger={
          <Ref innerRef={ref}>
            <Menu.Item icon={icon} fitted position={position} />
          </Ref>
        }
      />
    </>
  );
}

export function SidebarMenuItem() {
  const [hidden, setHidden] = useRecoilState(AppState.sidebarHidden);

  return (
    <>
      {hidden && (
        <MenuItem
          icon={{ className: 'hpx-standard huge left' }}
          onClick={() => setHidden(false)}
        />
      )}
    </>
  );
}

export function MainMenu({
  hidden,
  borderless,
  secondary,
  pointing,
  tabular,
  fixed,
  size = 'tiny',
  stackable,
  absolutePosition,
  connectionItem = true,
  children,
}: {
  hidden?: boolean;
  size?: React.ComponentProps<typeof Menu>['size'];
  borderless?: boolean;
  stackable?: boolean;
  secondary?: boolean;
  tabular?: boolean;
  pointing?: boolean;
  absolutePosition?: boolean;
  fixed?: React.ComponentProps<typeof Menu>['fixed'] | boolean;
  connectionItem?: boolean;
  children?: React.ReactNode;
}) {
  const ref = useRef<HTMLDivElement>();

  const sidebarPosition = useRecoilValue(AppState.sidebarPosition);
  const { isMobileMax } = useBreakpoints();

  const [isFixed, setIsFixed] = useState<
    React.ComponentProps<typeof Menu>['fixed'] | boolean
  >();

  const fixMenu = useCallback(() => {
    if (!ref.current) {
      return;
    }
    if (window.scrollY > ref.current.offsetHeight * 1.4) {
      if (isFixed !== fixed) {
        setIsFixed(fixed);
      }
    } else {
      if (isFixed !== undefined) {
        setIsFixed(undefined);
      }
    }
  }, [fixed, isFixed]);

  useEffect(() => fixMenu(), []);

  useDocumentEvent(
    'scroll',
    () => {
      fixMenu();
    },
    { passive: true },
    [fixMenu]
  );

  if (hidden) return <></>;

  const isStacking = isMobileMax && stackable;

  const el = (fixed) => (
    <Menu
      size={size}
      fluid
      borderless={borderless}
      fixed={fixed === true ? 'top' : fixed ?? undefined}
      secondary={secondary ?? !fixed}
      pointing={pointing}
      tabular={tabular}
      className={classNames(
        'main-menu',
        'pusher no-margins standard-z-index',
        absolutePosition ? 'pos-absolute' : 'pos-relative',
        {
          stackable2: stackable,
        }
      )}>
      {isStacking && (
        <Menu
          size={size}
          fluid
          secondary
          borderless={borderless}
          pointing={pointing}
          tabular={tabular}>
          {sidebarPosition === 'left' && <SidebarMenuItem />}
          {connectionItem && isFixed && fixed && <ConnectionItem />}
          {connectionItem && !isFixed && !fixed && <ConnectionItem />}
          {sidebarPosition === 'right' && <SidebarMenuItem />}
        </Menu>
      )}
      {!isStacking && sidebarPosition === 'left' && <SidebarMenuItem />}
      {children}
      {!isStacking && connectionItem && isFixed && fixed && <ConnectionItem />}
      {!isStacking && connectionItem && !isFixed && !fixed && (
        <ConnectionItem />
      )}
      {!isStacking && sidebarPosition === 'right' && <SidebarMenuItem />}
    </Menu>
  );

  return (
    <>
      {!!isFixed && el(undefined)}
      <Ref innerRef={ref}>{el(isFixed)}</Ref>
    </>
  );
}

export default MainMenu;
