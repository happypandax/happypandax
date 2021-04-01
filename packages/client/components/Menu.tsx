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
      className={classNames({ pulse: connectState === 'connecting' })}
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
  fixed,
}: {
  hidden?: boolean;
  fixed?: boolean;
}) {
  if (hidden) return <></>;

  return (
    <Menu
      size="tiny"
      fluid
      borderless
      fixed={fixed ? 'top' : undefined}
      secondary={!fixed}
      className={classNames()}>
      <ConnectionItem />
    </Menu>
  );
}

export default MainMenu;
