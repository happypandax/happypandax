import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useState,
} from 'react';
import { Icon, IconProps, Menu, Sidebar, Label } from 'semantic-ui-react';
import classNames from 'classnames';
import Link from 'next/link';
import _ from 'lodash';
import {
  SemanticCOLORS,
  SemanticICONS,
} from 'semantic-ui-react/dist/commonjs/generic';
import t from '../misc/lang';

const SidebarContext = createContext({
  iconOnly: false,
});

function SidebarItem({
  href,
  className,
  children,
  label,
  labelColor,
  icon,
}: {
  href?: string;
  icon?: SemanticICONS | IconProps;
  className?: string;
  label?: string;
  labelColor?: SemanticCOLORS;
  children?: React.ReactNode;
}) {
  const context = useContext(SidebarContext);

  return (
    <Link href={href} passHref>
      <Menu.Item as={href ? 'a' : undefined} className={classNames(className)}>
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
    </Link>
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

export function MainSidebar({
  hiiden: hidden,
  fixed = true,
  onlyIcons,
}: {
  hiiden?: boolean;
  fixed?: boolean;
  onlyIcons?: boolean;
}) {
  const [iconOnly, setIconOnly] = useState(onlyIcons);
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
    setIconOnly(onlyIcons);
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
              icon={{ name: 'plus square outline', color: 'teal' }} // <-- use React.memo
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
              href="/management"
              icon={'cubes'}>{t`Management`}</SidebarItem>
            <DownloadSidebarItem />
            <MetadataSidebarItem />
            <SidebarItem href="/tasks" icon={'tasks'}>{t`Tasks`}</SidebarItem>
          </div>
          <div className="bottom-aligned">
            <SidebarItem href="/trash" icon={'trash'}>{t`About`}</SidebarItem>
            <SidebarItem
              href="/preferences"
              icon={'settings'}>{t`Preferences`}</SidebarItem>
            <SidebarItem href="/about" icon={'info'}>{t`About`}</SidebarItem>
          </div>
        </div>
      </SidebarContext.Provider>
    </Sidebar>
  );
}

export default MainSidebar;
