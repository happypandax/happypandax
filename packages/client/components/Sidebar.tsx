import classNames from 'classnames';
import _ from 'lodash';
import Link from 'next/link';
import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useRef,
  useState,
} from 'react';
import {
  Icon,
  IconProps,
  Label,
  Menu,
  Ref,
  Segment,
  Sidebar,
} from 'semantic-ui-react';
import {
  SemanticCOLORS,
  SemanticICONS,
} from 'semantic-ui-react/dist/commonjs/generic';

import { useDocumentEvent } from '../hooks/utils';
import t from '../misc/lang';
import { AppState, useInitialRecoilState } from '../state/index';
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
  const [width, setWidth] = useInitialRecoilState(
    AppState.sidebarWidth,
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
              href="/favorites"
              icon={{ name: 'heart', color: 'red' }} // <-- use React.memo
            >{t`Favorites`}</SidebarItem>
            <SidebarItem
              href="/library"
              icon={'grid layout'}>{t`Library`}</SidebarItem>
            <SidebarItem
              href="/management"
              icon={'cubes'}>{t`Management`}</SidebarItem>
            <SidebarItem
              href="/directory"
              icon={'folder outline'}>{t`Directory`}</SidebarItem>
          </div>
          <div className="bottom-aligned">
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

function mainMenuProps() {
  const fixedEl: HTMLDivElement = document.querySelector('.main-menu.fixed');
  const r = {
    height: fixedEl?.offsetHeight ?? 0,
    fixed: !!fixedEl,
  };

  if (!r.fixed) {
    const el: HTMLDivElement = document.querySelector('.main-menu:not(.fixed)');
    if (el.offsetHeight) {
      r.height = el.offsetHeight;
    }
  }
  console.log(r);
  return r;
}

export function StickySidebar({
  visible,
  ...props
}: {
  visible?: boolean;
} & React.ComponentProps<typeof Sidebar>) {
  const ref = useRef<HTMLDivElement>();

  const computeTop = useCallback(() => {
    if (visible) {
      const mh = mainMenuProps();
      const t = Math.max(0, window.scrollY + (mh.fixed ? 0 : -mh.height));
      ref.current.style.top = `${t}px`;
      if (mh.height && (mh.fixed || !t)) {
        ref.current.style.setProperty('max-height', '94.5vh', 'important');
      } else {
        ref.current.style.setProperty('max-height', '98vh', 'important');
      }
    }
  }, [visible]);

  useEffect(() => {
    ref.current.style.setProperty('max-height', '98vh', 'important');
    ref.current.style.paddingRight = `calc(${
      window.innerWidth - document.body.offsetWidth
    }px + ${ref.current.style.paddingRight ?? 0})`;
    ref.current.style.transition =
      'transform 300ms ease, -webkit-transform 300ms ease, top 0.15s ease-in 0s';
  }, []);

  useEffect(computeTop, [visible]);

  useDocumentEvent('scroll', computeTop, { passive: true }, [computeTop]);

  return (
    <Ref innerRef={ref}>
      <Sidebar
        as={Segment}
        size="very wide"
        animation="overlay"
        {...props}
        visible={visible}
        direction="right"
      />
    </Ref>
  );
}
