import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useState,
} from 'react';
import { Icon, IconProps, Menu, Popup, Ref } from 'semantic-ui-react';
import classNames from 'classnames';
import Link from 'next/link';
import _ from 'lodash';
import {
  SemanticCOLORS,
  SemanticICONS,
} from 'semantic-ui-react/dist/commonjs/generic';
import t from '../misc/lang';
import styles from './Menu.module.css';
import { useRef } from 'react';

const MenuContext = createContext({});

export function NotificationPopup({
  context,
}: {
  context: React.ComponentProps<typeof Popup>['context'];
}) {
  const [show, setShow] = useState(true);
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
  const [connectState, setConnectState] = useState<
    'connected' | 'connecting' | 'disconnected'
  >('connecting');
  const ref = useRef();

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
