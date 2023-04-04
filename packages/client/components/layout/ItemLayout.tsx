import classNames from 'classnames';
import ColorThief from 'colorthief';
import React, { RefObject, useEffect, useMemo, useRef } from 'react';
import { useRecoilValue } from 'recoil';
import { Container, Menu } from 'semantic-ui-react';

import { DataContext } from '../../client/context';
import { useSetupDataState } from '../../client/hooks/item';
import { useRefEvent } from '../../client/hooks/utils';
import { animateCSS } from '../../client/utility';
import { ItemType } from '../../shared/enums';
import { ServerGallery, ServerItemWithProfile } from '../../shared/types';
import { AppState } from '../../state';
import MainMenu, { ConnectionItem, MenuItem } from '../Menu';
import styles from './ItemLayout.module.css';

export function ParallaxDiv({
  children,
  target,

  className,
  ...props
}: { target?: RefObject<HTMLElement | Document> } & Omit<
  React.HTMLProps<HTMLDivElement>,
  'target'
>) {
  const initialRef = useRef(window?.document);
  const targetRef = target ?? initialRef;
  const ref = useRef<HTMLDivElement>();
  const runningAnimationRef = useRef({
    running: false,
    startPos: 0,
    lastOffset: 0,
    velocity: 0.5,
    ease: 0.05,
  });

  useRefEvent(
    targetRef,
    'scroll',
    (ev) => {
      if (!ref.current) {
        return;
      }

      if (!runningAnimationRef.current.running) {
        runningAnimationRef.current.running = true;

        if (runningAnimationRef.current.startPos) {
          runningAnimationRef.current.startPos = ref.current.offsetTop;
        }

        const loop = () => {
          if (!ref.current) {
            return;
          }

          const offset = window.scrollY;
          const delta =
            (offset - runningAnimationRef.current.lastOffset) *
            runningAnimationRef.current.velocity *
            runningAnimationRef.current.ease;

          if (Math.abs(delta) < 0.05) {
            runningAnimationRef.current.lastOffset = offset;
            runningAnimationRef.current.running = false;
            return;
          }

          ref.current.style.transform = `translate(0, ${
            runningAnimationRef.current.startPos -
            runningAnimationRef.current.lastOffset
          }px)`;

          runningAnimationRef.current.lastOffset += delta;
          requestAnimationFrame(loop);
        };
        requestAnimationFrame(loop);
      }
    },
    { passive: true },
    []
  );

  return (
    <div ref={ref} {...props} className={classNames(className)}>
      {children}
    </div>
  );
}

export function LabelFields({
  children,
  className,
  ...props
}: React.HTMLProps<HTMLDivElement>) {
  return (
    <div {...props} className={classNames('ui form', className)}>
      {children}
    </div>
  );
}

export function LabelField({
  label,
  children,
  padded = true,
}: {
  padded?: boolean;
  label?: React.ReactNode;
  children?: React.ReactNode;
}) {
  return (
    <div className="field">
      <label>{label}</label>
      <div
        className={classNames(styles.label_children, {
          [styles.label_children_padded]: padded,
        })}
      >
        {children}
      </div>
    </div>
  );
}

export function ItemMenu({
  data: initialData,
  children,
  type,
}: {
  data: DeepPick<
    ServerGallery,
    'id' | 'metatags.favorite' | 'metatags.read' | 'metatags.inbox'
  >;
  type: ItemType;
  children?: React.ReactNode;
}) {
  const readingQueue = useRecoilValue(AppState.readingQueue);

  const { data, dataContext } = useSetupDataState({
    initialData,
    itemType: type,
    key: 'header',
  });

  return (
    <DataContext.Provider value={dataContext}>
      <MainMenu absolutePosition size="mini" connectionItem={false}>
        {children}
        <Menu.Menu position="right">
          {readingQueue?.includes?.(data?.id) && (
            <MenuItem
              icon={{
                className: 'bookmark',
                color: 'red',
                bordered: true,
                inverted: true,
              }}
              title={`This item is in your reading queue`}
            ></MenuItem>
          )}
          {data?.metatags?.inbox && (
            <MenuItem
              icon={{ name: 'inbox', bordered: true, inverted: true }}
              title={`This item is in your inbox`}
            ></MenuItem>
          )}
          {!data?.metatags?.read && (
            <MenuItem
              icon={{
                name: 'eye slash outline',
                bordered: true,
                inverted: true,
              }}
              title={`This item has not been read yet`}
            ></MenuItem>
          )}
          <ConnectionItem />
        </Menu.Menu>
      </MainMenu>
    </DataContext.Provider>
  );
}

export function ItemHeaderParallax({
  data,
}: {
  data: DeepPick<ServerItemWithProfile, 'id' | 'profile'>;
}) {
  const heroRef = useRef<HTMLDivElement>();
  const heroImgRef = useRef<HTMLImageElement>();
  const colorThief = useMemo(() => new ColorThief(), []);

  useEffect(() => {
    animateCSS(heroImgRef.current, styles.fadeInDownImage, false);
  }, [data?.id]);

  useEffect(() => {
    const setColor = () => {
      const c = colorThief.getColor(heroImgRef.current);
      heroRef.current.style.backgroundColor = `rgb(${c[0]}, ${c[1]}, ${c[2]})`;
    };
    if (heroImgRef.current.complete) {
      setColor();
    } else {
      heroImgRef.current.onload = setColor;
    }
  }, [data?.id]);

  return (
    <div ref={heroRef} className={classNames(styles.header_hero)}>
      <Container className="pos-relative">
        <ParallaxDiv>
          <img
            alt="header image"
            className={classNames('animate__slower')}
            ref={heroImgRef}
            src={data.profile.data}
          />
        </ParallaxDiv>
      </Container>
    </div>
  );
}

export function BlurryBackgroundContainer({
  data,
  ...props
}: React.ComponentProps<typeof Container> & {
  data?: DeepPick<ServerItemWithProfile, 'id' | 'profile'>;
}) {
  const containerRef = useRef<HTMLDivElement>();
  const imgRef = useRef<HTMLImageElement>(new Image());
  const colorThief = useMemo(() => new ColorThief(), []);

  useEffect(() => {
    const setColor = () => {
      const c = colorThief.getColor(imgRef.current);
      containerRef.current.style.backgroundColor = `rgb(${c[0]}, ${c[1]}, ${c[2]})`;
    };
    imgRef.current.src = data.profile.data;
    if (imgRef.current.complete) {
      setColor();
    } else {
      imgRef.current.onload = setColor;
    }
  }, [data?.id]);

  return (
    <div className={styles.blurry_background_parent}>
      <div
        ref={containerRef}
        className={styles.blurry_background_container}
        style={{ backgroundImage: `url(${data.profile.data})` }}
      />
      <Container {...props} />
    </div>
  );
}
