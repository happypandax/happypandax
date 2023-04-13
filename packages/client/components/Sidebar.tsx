import classNames from 'classnames';
import _ from 'lodash';
import Link from 'next/link';
import { useRouter } from 'next/router';
import {
  createContext,
  forwardRef,
  useCallback,
  useContext,
  useEffect,
  useImperativeHandle,
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

import { useBreakpoints, useHijackHistory } from '../client/hooks/ui';
import { useDocumentEvent } from '../client/hooks/utils';
import t from '../client/lang';
import { urlparse } from '../shared/utility';
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
  active,
  label,
  labelColor,
  onClick,
  icon,
}: {
  href?: string;
  icon?: SemanticICONS | IconProps;
  className?: string;
  label?: string;
  active?: boolean;
  labelColor?: SemanticCOLORS;
  onClick?: React.ComponentProps<typeof Menu.Item>['onClick'];
  children?: React.ReactNode;
}) {
  const context = useContext(SidebarContext);

  const router = useRouter();

  const urlquery = urlparse(router.asPath);

  const menuItem = (
    <Menu.Item
      as={href ? 'a' : undefined}
      onClick={onClick}
      active={active ?? (href ? urlquery.url.startsWith(href) : undefined)}
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
    <Link href={href} passHref legacyBehavior>
      {menuItem}
    </Link>
  ) : (
    menuItem
  );
}

export function MainSidebar({
  hidden,
  fixed = true,
  direction,
  onlyIcons,
  onHide,
}: {
  hidden?: boolean;
  direction?: 'left' | 'right';
  onHide?: () => void;
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
      direction={direction}
      size="small"
      inverted={inverted}
      icon={iconOnly}
      width={width}
      className={classNames('overflow-unset', 'window-height', {
        fixed: fixed,
      })}
      onHide={useCallback(() => {
        onHide?.();
      }, [onHide])}
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
              active={false}
              icon={{ className: 'hpx-standard huge left' }}
              className="center-text small-padding-segment no-left-padding no-right-padding"></SidebarItem>
            <SidebarItem
              href="/add"
              icon={{ name: 'plus square', color: 'teal' }} // <-- use React.memo
            >{t`Import`}</SidebarItem>
          </div>
          <div className="middle-aligned">
            <SidebarItem
              href="/dashboard"
              icon={{ name: 'heart', color: 'red' }} // <-- use React.memo
            >{t`Dashboard`}</SidebarItem>
            <SidebarItem
              href="/library"
              icon={'grid layout'}>{t`Library`}</SidebarItem>
            <SidebarItem
              href="/directory"
              icon={'folder outline'}>{t`Directory`}</SidebarItem>
            <SidebarItem
              href="/management"
              icon={'cubes'}>{t`Management`}</SidebarItem>
          </div>
          <div className="bottom-aligned">
            <SidebarItem
              href="/profile"
              icon={'user alternate'}>{t`Profile`}</SidebarItem>
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

function mainMenuProps(selector = '.main-menu') {
  const fixedEl: HTMLDivElement = document.querySelector(`${selector}.fixed`);
  const r = {
    height: fixedEl?.offsetHeight ?? 0,
    bottom: fixedEl?.getBoundingClientRect?.()?.bottom ?? 0,
    fixed: !!fixedEl,
  };

  if (!r.fixed) {
    const el: HTMLDivElement = document.querySelector(
      `${selector}:not(.fixed)`
    );
    if (el?.offsetHeight) {
      r.height = el.offsetHeight;
    }

    if (el?.getBoundingClientRect?.()?.bottom) {
      r.bottom = el.getBoundingClientRect().bottom;
    }
  }
  return r;
}

export const StickySidebar = forwardRef(function StickySidebar(
  {
    visible,
    menuSelector = '.main-menu',
    ...props
  }: {
    visible?: boolean;
    menuSelector?: string;
  } & React.ComponentProps<typeof Sidebar>,
  fref
) {
  const ref = useRef<HTMLDivElement>();

  const { isMobileMax } = useBreakpoints();

  useImperativeHandle(fref, () => ref.current);

  const computeTop = useCallback(() => {
    if (visible) {
      const mh = mainMenuProps(menuSelector);
      const margin = 5;
      const t = Math.max(0, mh.height + margin);
      ref.current.style.top = `${t}px`;
      if (mh.height && (mh.fixed || !t)) {
        ref.current.style.setProperty(
          'max-height',
          `calc(100% - ${t + margin}px)`,
          'important'
        );
      } else {
        ref.current.style.setProperty(
          'max-height',
          `calc(100% - ${t + margin}px)`,
          'important'
        );
      }
    }
  }, [visible, menuSelector]);

  useEffect(() => {
    ref.current.style.paddingRight = `calc(${
      window.innerWidth - document.body.offsetWidth
    }px + ${ref.current.style.paddingRight ?? 0})`;
    ref.current.style.transition =
      'transform 300ms ease, -webkit-transform 300ms ease, top 0.15s ease-in 0s';
  }, []);

  useEffect(computeTop, [visible]);

  useDocumentEvent('scroll', computeTop, { passive: true }, [computeTop]);

  useHijackHistory(visible);

  return (
    <Ref innerRef={ref}>
      <Sidebar
        as={Segment}
        size={classNames({
          'very wide': !isMobileMax,
          wide: isMobileMax,
        })}
        animation="overlay"
        {...props}
        visible={visible}
        direction="right"
      />
    </Ref>
  );
});
