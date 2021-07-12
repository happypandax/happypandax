import classNames from 'classnames';
import { createContext, useEffect, useRef, useState } from 'react';
import { Icon, IconProps, Menu, Popup, Ref } from 'semantic-ui-react';
import { SemanticICONS } from 'semantic-ui-react/dist/commonjs/generic';

import { QueryType, useQueryType } from '../client/queries';
import { useInterval } from '../hooks/utils';
import styles from './Menu.module.css';

const MenuContext = createContext({});

export function NotificationPopup({
  context,
}: {
  context: React.ComponentProps<typeof Popup>['context'];
}) {
  const [show, setShow] = useState(false);
  return (
    <Popup open={show} context={context} position="bottom right">
      notifcation
    </Popup>
  );
}

export function MenuItem({
  className,
  icon,
  children,
}: {
  icon?: SemanticICONS | IconProps;
  children?: React.ReactNode;
  className?: string;
}) {
  //   const context = useContext(MenuContext);

  return (
    <Menu.Item className={classNames(className)}>
      {!!icon && (
        <Icon
          size="large"
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

function ConnectionItem({
  position = 'right',
}: {
  position?: 'left' | 'right';
}) {
  const ref = useRef();
  const { error, data, refetch } = useQueryType(QueryType.SERVER_STATUS);

  const [connectState, setConnectState] = useState<
    'connected' | 'connecting' | 'disconnected'
  >(data?.data?.connected ? 'connected' : 'connecting');

  useEffect(() => {
    if (error || !data?.data?.connected) {
      setConnectState('disconnected');
    } else if (data?.data?.connected) {
      setConnectState('connected');
    }
  }, [error, data]);

  useInterval(
    () => {
      if (connectState === 'connecting') {
        return;
      }

      if (connectState !== 'connected') {
        setConnectState('connecting');
      }

      refetch();
    },
    connectState === 'disconnected' ? 2000 : 10000,
    [connectState]
  );

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
      <NotificationPopup context={ref} />
      <Popup
        content="Options"
        on="click"
        position="bottom right"
        trigger={
          <Ref innerRef={ref}>
            <Menu.Item icon={icon} fitted position={position} />
          </Ref>
        }
      />
    </>
  );
}

export function MainMenu({
  hidden,
  borderless,
  fixed,
  children,
}: {
  hidden?: boolean;
  borderless?: boolean;
  fixed?: boolean;
  children?: React.ReactNode;
}) {
  if (hidden) return <></>;

  return (
    <Menu
      size="tiny"
      fluid
      borderless={borderless}
      fixed={fixed ? 'top' : undefined}
      secondary={!fixed}
      className={classNames(
        'pusher no-margins standard-z-index post-relative'
      )}>
      {children}
      <ConnectionItem />
    </Menu>
  );
}

export default MainMenu;
