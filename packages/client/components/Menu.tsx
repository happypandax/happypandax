import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useState,
} from 'react';
import { Icon, IconProps, Menu, Popup } from 'semantic-ui-react';
import classNames from 'classnames';
import Link from 'next/link';
import _ from 'lodash';
import {
  SemanticCOLORS,
  SemanticICONS,
} from 'semantic-ui-react/dist/commonjs/generic';
import t from '../misc/lang';
import styles from './Menu.module.css';

const MenuContext = createContext({});

function MenuItem({
  className,
  icon,
}: {
  icon?: SemanticICONS | IconProps;
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
    <Popup
      content="Options"
      on="click"
      trigger={<Menu.Item icon={icon} fitted position={position} />}
    />
  );
}

export function MainMenu({
  hidden,
  borderless,
  fixed,
}: {
  hidden?: boolean;
  borderless?: boolean;
  fixed?: boolean;
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
      <ConnectionItem />
    </Menu>
  );
}

export default MainMenu;
