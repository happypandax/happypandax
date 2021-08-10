import classNames from 'classnames';
import _ from 'lodash';
import Link from 'next/link';
import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useState,
} from 'react';
import { Icon, IconProps, Label, Menu, Sidebar } from 'semantic-ui-react';
import {
  SemanticCOLORS,
  SemanticICONS,
} from 'semantic-ui-react/dist/commonjs/generic';

import t from '../misc/lang';
import AboutModal from './About';
import SettingsModal from './Settings';

const SidebarContext = createContext({
  iconOnly: false,
});

function SidebarItem({
  href,
  className,
  children,
  label,
  labelColor,
  onClick,
  icon,
}: {
  href?: string;
  icon?: SemanticICONS | IconProps;
  className?: string;
  label?: string;
  labelColor?: SemanticCOLORS;
  onClick?: React.ComponentProps<typeof Menu.Item>['onClick'];
  children?: React.ReactNode;
}) {
  const context = useContext(SidebarContext);

  const menuItem = (
    <Menu.Item
      as={href ? 'a' : undefined}
      onClick={onClick}
      className={classNames(className)}>
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
      {!context.iconOnly && children}
      {label && (
        <Label color={labelColor} floating>
          {label}
        </Label>
      )}
    </Menu.Item>
  );

  return href ? (
    <Link href={href} passHref>
      {menuItem}
    </Link>
  ) : (
    menuItem
  );
}

function DownloadSidebarItem() {
  return (
    <SidebarItem
      href="/downloads"
      icon={'download'}
      label="23"
      labelColor="yellow">{t`Downloads`}</SidebarItem>
  );
}

function MetadataSidebarItem() {
  return (
    <SidebarItem
      href="/metadata"
      icon={'cloud'}
      label="23"
      labelColor="yellow">{t`Metadata`}</SidebarItem>
  );
}

function TrashSidebarItem() {
  return (
    <SidebarItem
      href="/trash"
      icon={'trash'}
      label="23"
      labelColor="red">{t`Downloads`}</SidebarItem>
  );
}

export function MainSidebar({
  hiiden: hidden,
  fixed = true,
  onlyIcons,
}: {
  hiiden?: boolean;
  fixed?: boolean;
  onlyIcons?: boolean;
}) {
  const [iconOnly, setIconOnly] = useState(true);
  const [inverted, setInverted] = useState(!fixed);
  const [width, setWidth] = useState<'very thin' | 'thin'>(
    iconOnly ? 'very thin' : 'thin'
  );
  const [animation, setAnimation] = useState<'push' | 'overlay'>(
    fixed ? 'push' : 'overlay'
  );

  useEffect(() => {
    setWidth(iconOnly ? 'very thin' : 'thin');
  }, [iconOnly]);

  useEffect(() => {
    if (onlyIcons !== undefined) {
      setIconOnly(onlyIcons);
    }
  }, [onlyIcons]);

  useEffect(() => {
    setAnimation(fixed ? 'push' : 'overlay');
    setInverted(!fixed);
  }, [fixed]);

  return (
    <Sidebar
      visible={!hidden}
      as={Menu}
      animation={animation}
      vertical
      size="small"
      inverted={inverted}
      icon={iconOnly}
      width={width}
      className={classNames('overflow-unset', 'window-height', {
        fixed: fixed,
      })}
      onMouseEnter={useCallback(() => {
        if (!onlyIcons) setIconOnly(false);
      }, [onlyIcons])}
      onMouseLeave={useCallback(
        _.debounce(() => {
          if (!onlyIcons) setIconOnly(true);
        }, 100),
        [onlyIcons]
      )}>
      <SidebarContext.Provider value={{ iconOnly }}>
        <div className="flex-container">
          <div className="top-aligned">
            <SidebarItem
              href="/"
              icon={{ className: 'hpx-standard huge left' }}
              className="center-text small-padding-segment no-left-padding no-right-padding"></SidebarItem>
            <SidebarItem
              href="/add"
              icon={{ name: 'plus square', color: 'teal' }} // <-- use React.memo
            >{t`Import`}</SidebarItem>
          </div>
          <div className="middle-aligned">
            <SidebarItem
              href="/favorite"
              icon={{ name: 'heart', color: 'red' }} // <-- use React.memo
            >{t`Favorites`}</SidebarItem>
            <SidebarItem
              href="/library"
              icon={'grid layout'}>{t`Library`}</SidebarItem>
            <SidebarItem
              href="/directory"
              icon={'cubes'}>{t`Directory`}</SidebarItem>
            <DownloadSidebarItem />
            <MetadataSidebarItem />
            <SidebarItem href="/tasks" icon={'tasks'}>{t`Tasks`}</SidebarItem>
          </div>
          <div className="bottom-aligned">
            <TrashSidebarItem />
            <SettingsModal
              trigger={
                <SidebarItem icon={'settings'}>{t`Preferences`}</SidebarItem>
              }
            />
            <AboutModal
              trigger={<SidebarItem icon={'info'}>{t`About`}</SidebarItem>}
            />
          </div>
        </div>
      </SidebarContext.Provider>
    </Sidebar>
  );
}

export default MainSidebar;
