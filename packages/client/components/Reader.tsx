import classNames from 'classnames';
import _ from 'lodash';
import Link from 'next/link';
import { useRouter } from 'next/router';
import React, {
  useCallback,
  useEffect,
  useLayoutEffect,
  useMemo,
  useRef,
  useState,
} from 'react';
import {
  useFullscreen,
  useHarmonicIntervalFn,
  useIsomorphicLayoutEffect,
  useKeyPressEvent,
  useUpdateEffect,
} from 'react-use';
import useMeasureDirty from 'react-use/lib/useMeasureDirty';
import { useRecoilState, useRecoilValue, useSetRecoilState } from 'recoil';
import {
  Button,
  Checkbox,
  Dimmer,
  Form,
  Grid,
  Header,
  Icon,
  Label,
  Modal,
  Rating,
  Segment,
  Select,
} from 'semantic-ui-react';

import Scroller from '@twiddly/scroller';

import { Query, QueryType, useQueryType } from '../client/queries';
import { useBodyEvent, useRefEvent, useTabActive } from '../hooks/utils';
import { ImageSize, ItemFit, ItemType, ReadingDirection } from '../misc/enums';
import t from '../misc/lang';
import { FieldPath, ServerGallery, ServerPage } from '../misc/types';
import {
  getPageWidth,
  getScreenWidth,
  update,
  urlparse,
  urlstring,
} from '../misc/utility';
import {
  AppState,
  ReaderState,
  useInitialRecoilState,
  useInitialRecoilValue,
} from '../state';
import GalleryCard, {
  GalleryCardData,
  galleryCardDataFields,
} from './item/Gallery';
import { Slider } from './Misc';

function getOptimalImageSize() {
  const w = getPageWidth();
  const s = getScreenWidth();
  if (w > 2400 || s > 2400) return ImageSize.Original;
  if (w > 1600 || s > 1600) return ImageSize.x2400;
  else if (w > 1280 || s > 1600) return ImageSize.x1600;
  else if (w > 980) return ImageSize.x1280;
  else if (w > 768) return ImageSize.x960;
  else return ImageSize.x768;
}

export function windowedPages(
  page: number,
  size: number,
  total: number,
  startIndex: number = 0
) {
  if (!total) return [];

  const start = startIndex - 1;

  page = Math.min(page, total);
  page = Math.max(page, start);

  const pages = [];
  if (page > start) {
    let i = 1;
    while (page - i > start && i < size / 2) {
      pages.unshift(page - i);
      i++;
    }
  }

  pages.push(page);

  if (page < total) {
    let i = 1;
    while (page + i <= total && i < size / 2 + 1) {
      pages.push(page + i);
      i++;
    }
  }
  return pages;
}

function scrollRender(element: HTMLElement, left, top, zoom) {
  const docStyle = document.documentElement.style;

  let engine;
  if (
    global.opera &&
    Object.prototype.toString.call(opera) === '[object Opera]'
  ) {
    engine = 'presto';
  } else if ('MozAppearance' in docStyle) {
    engine = 'gecko';
  } else if ('WebkitAppearance' in docStyle) {
    engine = 'webkit';
  } else if (typeof navigator.cpuClass === 'string') {
    engine = 'trident';
  }

  let vendorPrefix = {
    trident: 'ms',
    gecko: 'Moz',
    webkit: 'Webkit',
    presto: 'O',
  }[engine];

  const helperElem = document.createElement('div');

  var perspectiveProperty = vendorPrefix + 'Perspective';
  var transformProperty = vendorPrefix + 'Transform';

  if (helperElem.style[perspectiveProperty] !== undefined) {
    element.style[transformProperty] =
      'translate3d(' + -left + 'px,' + -top + 'px,0) scale(' + zoom + ')';
  } else if (helperElem.style[transformProperty] !== undefined) {
    element.style[transformProperty] =
      'translate(' + -left + 'px,' + -top + 'px) scale(' + zoom + ')';
  } else {
    element.style.marginLeft = left ? -left / zoom + 'px' : '';
    element.style.marginTop = top ? -top / zoom + 'px' : '';
    element.style.zoom = zoom || '';
  }
}

function CanvasImage({
  href,
  fit = ItemFit.Auto,
  stretchFit = false,
  direction = ReadingDirection.TopToBottom,
  wheelZoom,
  focused,
}: {
  href: string;
  fit?: ItemFit;
  stretchFit?: boolean;
  wheelZoom?: boolean;
  direction?: ReadingDirection;
  focused?: boolean;
}) {
  const preload = useRef(new Image());

  if (href && !preload.current.src) {
    preload.current.src = href;
  }

  const ref = useRef<HTMLDivElement>();
  const refContent = useRef<HTMLImageElement>();
  const refMouseDown = useRef<boolean>(false);
  const refIsScrollPanning = useRef<boolean>(false);
  const refScrollPan = useRef<{ x: number; y: number }>({ x: 0, y: 0 });
  const refControlKeyPressed = useRef(false);

  const [zoomLevel, setZoomLevel] = useState<number>(1);
  const [scroller, setScroller] = useState<Scroller>();
  const [itemFit, setItemFit] = useState<ItemFit>();

  const itemContained = useCallback(
    ({ left, top, zoom }, checkLeft = true, checkTop = true) => {
      // check if vancas contains item visually
      const leftContained =
        ref.current.clientWidth >=
        refContent.current.offsetWidth * zoom + Math.abs(left);
      const topContained =
        ref.current.clientHeight >=
        refContent.current.offsetHeight * zoom + Math.abs(top);

      return checkLeft && checkTop
        ? leftContained && topContained
        : checkLeft
        ? leftContained
        : topContained;
    },
    []
  );

  useKeyPressEvent(
    'Control',
    () => {
      refControlKeyPressed.current = true;
    },
    () => {
      refControlKeyPressed.current = false;
    }
  );

  useIsomorphicLayoutEffect(() => {
    const { offsetHeight, offsetWidth } = refContent.current;
    if (fit === ItemFit.Contain) {
      if (offsetWidth >= offsetHeight) {
        setItemFit(ItemFit.Width);
      } else {
        setItemFit(ItemFit.Height);
      }
    } else if (fit === ItemFit.Auto) {
      if (offsetHeight > offsetWidth) {
        setItemFit(ItemFit.Width);
      } else if (offsetWidth > offsetHeight) {
        setItemFit(ItemFit.Height);
      } else {
        setItemFit(undefined);
      }
    } else {
      setItemFit(fit);
    }
  }, [fit]);

  const onPublish = useCallback((left, top, zoom) => {
    if (!ref.current) return;

    let offsetLeft = 0;
    let offsetTop = 0;
    //  make sure item is centered if containted by canvas
    if (itemContained({ left, top, zoom }, true, false)) {
      offsetLeft =
        (ref.current.clientWidth - left) / 2 -
        (refContent.current.offsetWidth * zoom) / 2;
      // console.log([ref.current.clientWidth, refContent.current.offsetWidth]);
      // make sure item is still in view
      // offsetLeft = itemContained(
      //   { left: left - offsetLeft, top, zoom },
      //   true,
      //   false
      // )
      //   ? offsetLeft
      //   : 0;
    }
    if (itemContained({ left, top, zoom }, false, true)) {
      offsetTop =
        (ref.current.clientHeight - top) / 2 -
        (refContent.current.offsetHeight * zoom) / 2;

      // make sure item is still in view
      // offsetTop = itemContained(
      //   { left, top: top - offsetTop, zoom },
      //   false,
      //   true
      // )
      //   ? offsetTop
      //   : 0;
    }

    // console.log([left, top, offsetLeft, offsetTop, zoom]);

    // console.log([left - offsetLeft, top - offsetTop, zoom]);
    scrollRender(refContent.current, left - offsetLeft, top - offsetTop, zoom);
    setZoomLevel(zoom);
  }, []);

  // initialize Scroller
  useIsomorphicLayoutEffect(() => {
    const s = new Scroller(onPublish, {
      scrollingX: true,
      scrollingy: true,
      bouncing: true,
      locking: false,
      zooming: true,
      animating: true,
      animationDuration: 250,
    });

    setScroller(s);
  }, [onPublish]);

  // lock scrolling in direction where item is fully contained
  useIsomorphicLayoutEffect(() => {
    if (!scroller) return;
    if (itemContained(scroller.getValues(), true, false)) {
      scroller.options.scrollingX = false;
    } else {
      scroller.options.scrollingX = true;
    }
    if (itemContained(scroller.getValues(), false, true)) {
      scroller.options.scrollingY = false;
    } else {
      scroller.options.scrollingY = true;
    }
  }, [zoomLevel, scroller]);

  const resetZoom = useCallback(
    (e: React.MouseEvent<HTMLElement> = undefined) => {
      if (e) {
        e.preventDefault();
        e.stopPropagation();
      }
      if (!scroller) return false;
      scroller.scrollTo(0, 0, true, 1);
    },
    [scroller]
  );

  // reset zoom when not current child
  useEffect(() => {
    if (!focused) {
      resetZoom();
    }
  }, [focused]);

  const { width: refWidth, height: refHeight } = useMeasureDirty(ref);

  // initialize dimensions
  useIsomorphicLayoutEffect(() => {
    if (!scroller) return;

    const container = ref.current;
    const content = refContent.current;
    scroller.setPosition(0, 0);
    scroller.setDimensions(
      container.clientWidth,
      container.clientHeight,
      content.offsetWidth * 1.02,
      content.offsetHeight * 1.02
    );
  }, [scroller, refWidth, refHeight, itemFit]);

  // check whether item panning should be possible
  const canPan = useCallback(
    (e = undefined) => {
      let panPossible = !itemContained(scroller.getValues());

      if (panPossible) {
        if (e) e.preventDefault();
        return true;
      }
      return false;
    },
    [zoomLevel, scroller, itemContained, direction]
  );

  useBodyEvent(
    'mousemove',
    (e) => {
      if (!refMouseDown.current) {
        return;
      }
      scroller.doTouchMove(
        [
          {
            pageX: e.pageX,
            pageY: e.pageY,
          },
        ],
        e.timeStamp
      );
    },
    {},
    [scroller]
  );

  useBodyEvent(
    'mouseup',
    (e) => {
      if (!refMouseDown.current) {
        return;
      }

      scroller.doTouchEnd(e.timeStamp);
    },
    {},
    [scroller]
  );

  const onScrollPanEnd = useCallback(
    _.debounce((e: WheelEvent) => {
      refIsScrollPanning.current = false;
    }, 250),
    [scroller]
  );

  useRefEvent(
    ref,
    'wheel',
    (e) => {
      if (wheelZoom || refControlKeyPressed.current) {
        // zoom with scroll

        e.preventDefault();
        e.stopPropagation();
        const { zoom, left, top } = scroller.getValues();
        const change = e.deltaY > 0 ? 0.88 : 1.28;

        const newZoom = zoom * change;

        const zoomingOut = e.deltaY > 0 ? true : false;

        let zoomLeft = e.pageX - ref.current.clientWidth / 2;
        let zoomTop = e.pageY - ref.current.clientHeight / 2;

        if (zoomingOut) {
          // if zooming out, always zoom out from same origin
          zoomLeft = 0;
          zoomTop = 0;
        }

        scroller.zoomTo(newZoom, true, zoomLeft, zoomTop);
      } else {
        // pan with scroll
        if (canPan()) {
          const { left, top, zoom } = scroller.getValues();
          const {
            left: scrollMaxLeft,
            top: scrollMaxTop,
          } = scroller.getScrollMax();

          if (!refIsScrollPanning.current) {
            refIsScrollPanning.current = true;
            refScrollPan.current.x = left;
            refScrollPan.current.y = top;
          }

          const force = 0.15;

          const deltaX =
            e.deltaY > 0
              ? ref.current.clientWidth * force
              : -ref.current.clientWidth * force;

          const deltaY =
            e.deltaY > 0
              ? ref.current.clientHeight * force
              : -ref.current.clientHeight * force;

          const scrollingDown = e.deltaY > 0 ? true : false;

          // check if item has reached boundary (this will always only check the boundary in y-axis since we're assuming height > width for manga)
          // can be improved to take into account reading direction, item fit and aspect ratio
          switch (direction) {
            case ReadingDirection.LeftToRight:
            case ReadingDirection.TopToBottom: {
              if (refScrollPan.current.y === top) {
                if (scrollingDown && refScrollPan.current.y >= scrollMaxTop) {
                  return;
                }
                if (!scrollingDown && refScrollPan.current.y <= 0) {
                  return;
                }
              }
              break;
            }
          }

          e.preventDefault();
          e.stopPropagation();

          // sroll in the reading direction (this will always scroll in y-axis since we're assuming height > width for manga)
          // can be improved to take into account reading direction, item fit and aspect ratio
          switch (direction) {
            case ReadingDirection.LeftToRight:
            case ReadingDirection.TopToBottom:
              refScrollPan.current.y = Math.max(
                0,
                Math.min(refScrollPan.current.y + deltaY, scrollMaxTop)
              );
              break;
            // case ReadingDirection.LeftToRight:
            //   refScrollPan.current.x = Math.max(
            //     0,
            //     Math.min(
            //       refScrollPan.current.x + deltaX,
            //       refContent.current.offsetWidth * (1 - force)
            //     )
            //   );
            //   break;
          }

          scroller.scrollTo(
            refScrollPan.current.x,
            refScrollPan.current.y,
            true
          );

          onScrollPanEnd(e);
        }
      }
    },
    { passive: false },
    [scroller, wheelZoom]
  );

  return (
    <div
      ref={ref}
      draggable="false"
      onDragStart={() => false}
      className="reader-item user-select-none">
      {focused && (
        <div className="actions text-center">
          {zoomLevel !== 1 && (
            <Button
              onClick={resetZoom}
              size="huge"
              icon="zoom"
              className="translucent-black">
              <Icon name="close" />
              {t`Reset zoom`}
            </Button>
          )}
        </div>
      )}
      <img
        draggable="false"
        onLoad={useCallback(
          (e) => {
            if (scroller) {
              const { left, top, zoom } = scroller.getValues();
              onPublish(left, top, zoom);
            }
          },
          [scroller, onPublish]
        )}
        ref={refContent}
        onDragStart={(e) => {
          e.preventDefault();
          e.stopPropagation();
          return false;
        }}
        onMouseDownCapture={useCallback(
          (e) => {
            if (e.defaultPrevented) {
              return;
            }
            if (canPan(e)) {
              scroller.doTouchStart(
                [
                  {
                    pageX: e.pageX,
                    pageY: e.pageY,
                  },
                ],
                e.timeStamp
              );

              refMouseDown.current = true;
            }
          },
          [canPan, scroller]
        )}
        src={href}
        className={classNames('', {
          'fit-width': itemFit === ItemFit.Width,
          'fit-height': itemFit === ItemFit.Height,
          stretch: stretchFit,
        })}
      />
    </div>
  );
}

function Canvas({
  children,
  direction = ReadingDirection.TopToBottom,
  focusChild = 0,
  autoNavigateInterval = 5,
  autoNavigate,
  wheelZoom,
  label,
  onFocusChild,
  onEnd,
  stateKey,
}: {
  children?: any;
  direction?: ReadingDirection;
  label?: React.ReactNode;
  autoNavigateInterval?: number;
  focusChild?: number;
  wheelZoom?: boolean;
  stateKey?: string;
  autoNavigate?: boolean;
  onFocusChild?: (number) => void;
  onEnd?: () => void;
}) {
  const ref = useRef<HTMLDivElement>();
  const refMouseDownEvent = useRef<React.MouseEvent<HTMLDivElement>>(null);
  const refIsPanning = useRef<boolean>(false);
  const refIsScrollPanning = useRef<boolean>(false);
  const refScrollPan = useRef<{ x: number; y: number }>({ x: 0, y: 0 });
  const refContent = useRef<HTMLDivElement>();
  const refScrollComplete = useRef<() => void>();
  const [showFullscreen, setShowFullscreen] = useState(false);
  const tabActive = useTabActive();
  const isFullscreen = useFullscreen(ref, showFullscreen, {
    onClose: () => setShowFullscreen(false),
  });

  const setAutoNavigateCounter = useSetRecoilState(
    ReaderState.autoNavigateCounter(stateKey)
  );

  const [scroller, setScroller] = useState<Scroller>();

  useEffect(() => {
    ref.current.focus();
    const s = new Scroller(scrollRender.bind(undefined, refContent.current), {
      scrollingX: false,
      scrollingy: true,
      paging: true,
      animating: true,
      animationDuration: 250,
      scrollingComplete: () => {
        refScrollComplete.current?.();
      },
      speedMultiplier: 1.15,
      penetrationDeceleration: 0.1,
      penetrationAcceleration: 0.12,
    });

    setScroller(s);
  }, []);

  useBodyEvent(
    'mousemove',
    (e) => {
      if (!refIsPanning.current) {
        return;
      }
      scroller.doTouchMove(
        [
          {
            pageX: e.pageX,
            pageY: e.pageY,
          },
        ],
        e.timeStamp
      );
    },
    {},
    [scroller]
  );

  useBodyEvent(
    'mouseup',
    (e) => {
      if (!refIsPanning.current) {
        return;
      }

      scroller.doTouchEnd(e.timeStamp);
      refIsPanning.current = false;
    },
    {},
    [scroller]
  );

  useRefEvent(
    ref,
    'touchstart',
    (e) => {
      scroller.doTouchStart(e.touches, e.timeStamp);
      e.preventDefault();
    },
    { passive: false },
    [scroller],
    () => !!window.ontouchstart
  );

  useBodyEvent(
    'touchmove',
    (e) => {
      scroller.doTouchMove(e.touches, e.timeStamp);
    },
    {},
    [scroller],
    () => !!window.ontouchstart
  );

  useBodyEvent(
    'touchend',
    (e) => {
      scroller.doTouchEnd(e.timeStamp);
    },
    {},
    [scroller],
    () => !!window.ontouchstart
  );

  const onScrollPanEnd = useCallback(
    _.debounce((e: WheelEvent) => {
      refIsScrollPanning.current = false;
    }, 250),
    [scroller]
  );

  const { width: refWidth, height: refHeight } = useMeasureDirty(ref);

  // set scroll area dimensions
  useEffect(() => {
    if (!scroller) return;

    const rect = ref.current.getBoundingClientRect();
    const container = ref.current;
    const content = refContent.current;
    scroller.setPosition(
      rect.left + container.clientLeft,
      rect.top + container.clientTop
    );
    scroller.setDimensions(
      container.clientWidth,
      container.clientHeight,
      content.offsetWidth,
      content.offsetHeight
    );
  }, [children, scroller, refWidth, refHeight]);

  const getCurrentChild = useCallback(() => {
    let child = 0;
    if (!scroller) return child;
    switch (direction) {
      case ReadingDirection.TopToBottom: {
        child = Math.abs(scroller.getValues().top) / ref.current.clientHeight;
        break;
      }
    }
    return Math.floor(child);
  }, [direction, scroller]);

  const endReached = useCallback(() => {
    onEnd?.();
    setShowFullscreen(false);
  }, [onEnd]);

  const checkIfEnd = useCallback(() => {
    const { top } = scroller.getValues();
    // check if item has reached the end (this will always only check the boundary in y-axis since we're assuming height > width for manga)
    // can be improved to take into account reading direction, item fit and aspect ratio

    if (getCurrentChild() === React.Children.count(children) - 1) {
      // if last page
      const { top: scrollMaxTop } = scroller.getScrollMax();
      switch (direction) {
        case ReadingDirection.LeftToRight:
        case ReadingDirection.TopToBottom: {
          if (refScrollPan.current.y >= scrollMaxTop) {
            endReached();
          }
          break;
        }
      }
    }
  }, [children, endReached, scroller, direction, getCurrentChild, focusChild]);

  const getNextChild = useCallback(() => {
    switch (direction) {
      case ReadingDirection.LeftToRight:
      case ReadingDirection.TopToBottom:
        return focusChild + 1;
    }
  }, [direction, focusChild]);

  const scrollToChild = useCallback(
    (childNumber: number, animate = true) => {
      const { left, top } = scroller.getValues();

      switch (direction) {
        case ReadingDirection.TopToBottom:
          scroller.scrollTo(
            left,
            childNumber * ref.current.clientHeight,
            animate
          );
          break;
        case ReadingDirection.LeftToRight:
          scroller.scrollTo(
            childNumber * ref.current.clientWidth,
            top,
            animate
          );
          break;
      }

      if (React.Children.count(children) === childNumber) {
        endReached();
      }
    },
    [scroller, children, endReached]
  );

  // make sure focused child is in viewport
  useLayoutEffect(() => {
    if (!scroller) return;
    if (getCurrentChild() === focusChild) return;

    const childrenArray = React.Children.toArray(children);
    const childNumber = Math.max(
      0,
      Math.min(focusChild, childrenArray.length - 1)
    );

    scrollToChild(childNumber, false);
  }, [scrollToChild, getCurrentChild, focusChild, children]);

  // reset scroll to current child
  useEffect(() => {
    if (!scroller) return;
    refScrollComplete.current = () => {
      const child = getCurrentChild();
      if (!isNaN(child)) {
        onFocusChild?.(child);
      }
    };
  }, [onFocusChild, getCurrentChild, scroller]);

  // auto navigate
  useIsomorphicLayoutEffect(() => {
    if (
      tabActive &&
      autoNavigate &&
      focusChild < React.Children.count(children) - 1
    ) {
      let c = autoNavigateInterval;
      const t = setInterval(() => {
        if (refIsPanning.current) return;
        c--;
        setAutoNavigateCounter(c);
        if (!c) {
          scrollToChild(getNextChild(), true);
          c = autoNavigateInterval;
        }
      }, 1000);

      return () => clearInterval(t);
    }
  }, [
    autoNavigate,
    tabActive,
    getNextChild,
    children,
    focusChild,
    autoNavigateInterval,
  ]);

  useRefEvent(
    ref,
    'wheel',
    (e) => {
      if (e.defaultPrevented || wheelZoom) {
        return;
      }

      e.preventDefault();
      e.stopPropagation();

      if (!refIsScrollPanning.current) {
        const { left, top } = scroller.getValues();
        refIsScrollPanning.current = true;
        refScrollPan.current.x = left;
        refScrollPan.current.y = top;
      }

      const force = 0.33;

      const deltaX =
        e.deltaY > 0
          ? ref.current.clientWidth * force
          : -ref.current.clientWidth * force;

      const deltaY =
        e.deltaY > 0
          ? ref.current.clientHeight * force
          : -ref.current.clientHeight * force;

      switch (direction) {
        case ReadingDirection.TopToBottom:
          refScrollPan.current.y = Math.max(
            ref.current.clientHeight * force,
            Math.min(
              refScrollPan.current.y + deltaY,
              refContent.current.offsetHeight * (1 - force)
            )
          );
          break;
        case ReadingDirection.LeftToRight:
          refScrollPan.current.x = Math.max(
            ref.current.clientWidth * force,
            Math.min(
              refScrollPan.current.x + deltaX,
              refContent.current.offsetWidth * (1 - force)
            )
          );
          break;
      }

      scroller.scrollTo(refScrollPan.current.x, refScrollPan.current.y, true);

      const scrollingDown = e.deltaY > 0 ? true : false;
      if (scrollingDown) {
        // TODO: doesn't work
        checkIfEnd();
      }

      onScrollPanEnd(e);
    },
    { passive: false },
    [scroller, onScrollPanEnd, direction, wheelZoom, checkIfEnd]
  );

  return (
    <div
      ref={ref}
      className="reader-container"
      tabIndex={-1}
      onDoubleClick={useCallback(() => {
        setShowFullscreen(!showFullscreen);
      }, [showFullscreen])}
      onClick={useCallback(
        (e) => {
          ref.current.focus();
          // distinguish drag from click
          const delta = 5; // allow a small drag
          const diffX = Math.abs(e.pageX - refMouseDownEvent.current.pageX);
          const diffY = Math.abs(e.pageY - refMouseDownEvent.current.pageY);
          if (diffX < delta && diffY < delta) {
            const childrenArray = React.Children.toArray(children);
            const childNumber = Math.max(
              0,
              Math.min(focusChild, childrenArray.length - 1)
            );

            const deadSpaceX = ref.current.clientWidth * 0.1;
            const deadSpaceY = ref.current.clientHeight * 0.1;
            let nextChildNumber = null as number;

            switch (direction) {
              case ReadingDirection.TopToBottom: {
                if (e.pageY > ref.current.clientHeight / 2 + deadSpaceY) {
                  nextChildNumber = childNumber + 1;
                } else if (
                  e.pageY <
                  ref.current.clientHeight / 2 - deadSpaceY
                ) {
                  nextChildNumber = childNumber - 1;
                }
                break;
              }
              case ReadingDirection.LeftToRight: {
                if (e.pageX > ref.current.clientWidth / 2 + deadSpaceX) {
                  nextChildNumber = childNumber + 1;
                } else if (e.pageX > ref.current.clientWidth / 2 - deadSpaceX) {
                  nextChildNumber = childNumber - 1;
                }
                break;
              }
            }

            if (nextChildNumber !== null) {
              scrollToChild(nextChildNumber, true);
            }
          }
        },
        [direction, focusChild, onFocusChild, children]
      )}
      onMouseDown={useCallback(
        (e) => {
          refMouseDownEvent.current = e;
          if (e.defaultPrevented) {
            return;
          }
          scroller.doTouchStart(
            [
              {
                pageX: e.pageX,
                pageY: e.pageY,
              },
            ],
            e.timeStamp
          );
          refIsPanning.current = true;
        },
        [scroller]
      )}>
      <div className="top-content text-center">{!!label && label}</div>
      <div
        ref={refContent}
        className={classNames(
          'user-select-none reader-content no-scrollbar',
          'column'
        )}>
        {children}
      </div>
    </div>
  );
}

export type ReaderData = Optional<
  DeepPick<
    ServerPage,
    | 'id'
    | 'name'
    | 'number'
    | 'metatags.favorite'
    | 'metatags.inbox'
    | 'metatags.trash'
    | 'profile'
    | 'path'
  >,
  'profile'
>;

const pageFields: FieldPath<ServerPage>[] = [
  'id',
  'name',
  'number',
  'metatags.favorite',
  'metatags.inbox',
  'metatags.trash',
  'path',
];

export default function Reader({
  item,
  initialData,
  pageCount: initialPageCount = 0,
  windowSize: initialWindowSize = 10,
  remoteWindowSize: initialRemoteWindowSize,
  startPage = 1,
  onPage,
  autoNavigate: initialAutoNavigate,
  autoNavigateInterval: initialAutoNavigateInterval,
  stretchFit: initialStretchfit,
  fit: initialFit,
  wheelZoom: initialWheelZoom,
  direction: initialDirection,
  scaling: initialScaling,
  stateKey,
  padded,
  children,
}: {
  item: DeepPick<ServerGallery, 'id'>;
  initialData: ReaderData[];
  pageCount?: number;
  autoNavigateInterval?: number;
  fit?: ItemFit;
  stretchFit?: boolean;
  autoNavigate?: boolean;
  direction?: ReadingDirection;
  scaling?: ImageSize | 0;
  windowSize?: number;
  remoteWindowSize?: number;
  onPage?: (page: ReaderData) => void;
  startPage?: number;
  wheelZoom?: boolean;
  padded?: boolean;
  stateKey?: string;
  children?: React.ReactNode;
}) {
  const scaling = useInitialRecoilValue(
    ReaderState.scaling(stateKey),
    initialScaling
  );
  const wheelZoom = useInitialRecoilValue(
    ReaderState.wheelZoom(stateKey),
    initialWheelZoom
  );
  const stretchFit = useInitialRecoilValue(
    ReaderState.stretchFit(stateKey),
    initialStretchfit
  );
  const autoNavigate = useInitialRecoilValue(
    ReaderState.autoNavigate(stateKey),
    initialAutoNavigate
  );
  const autoNavigateInterval = useInitialRecoilValue(
    ReaderState.autoNavigateInterval(stateKey),
    initialAutoNavigateInterval
  );
  const fit = useInitialRecoilValue(ReaderState.fit(stateKey), initialFit);
  const direction = useInitialRecoilValue(
    ReaderState.direction(stateKey),
    initialDirection
  );

  const [isEnd, setIsEnd] = useInitialRecoilState(
    ReaderState.endReached(stateKey),
    false
  );

  const [pageCount, setPageCount] = useInitialRecoilState(
    ReaderState.pageCount(stateKey),
    initialPageCount
  );

  const [pageNumber, setPageNumber] = useInitialRecoilState(
    ReaderState.pageNumber(stateKey),
    startPage
  );

  const [pageFocus, setPageFocus] = useState(0);
  const [pages, setPages] = useState(initialData ?? []);

  const [windowSize, setWindowSize] = useState(
    Math.min(initialWindowSize, initialData ? initialData.length : pageCount)
  );
  const [remoteWindowSize, setRemoteWindowSize] = useState(
    Math.max(40, initialRemoteWindowSize ?? Math.ceil(windowSize * 2))
  );

  // indexes of pages that is currently active
  const [pageWindow, setPageWindow] = useState([] as number[]);

  const fetchingMoreRef = useRef({
    fetching: false,
    previousNumber: pageNumber,
  });
  const fetchingImagesRef = useRef<number[]>();

  // initial props

  useEffect(() => {
    setPageCount(initialPageCount);
  }, [initialPageCount]);

  useEffect(() => {
    setPages(initialData);
  }, [initialData]);

  useEffect(() => {
    setWindowSize(
      Math.min(initialWindowSize, initialData ? initialData.length : pageCount)
    );
  }, [initialWindowSize, pageCount, initialData]);

  useEffect(() => {
    setRemoteWindowSize(
      Math.max(40, initialRemoteWindowSize ?? Math.ceil(windowSize * 2))
    );
  }, [initialRemoteWindowSize]);

  //

  const { data } = useQueryType(
    QueryType.PAGES,
    {
      gallery_id: item.id,
      number: startPage,
      window_size: remoteWindowSize,
      fields: pageFields,
    },
    { enabled: !!!initialData }
  );

  useEffect(() => {
    if (data && !!!initialData) {
      setPages(data.data.items as ReaderData[]);
      setPageCount(data.data.count);
    }
  }, [data, initialData]);

  //

  useEffect(() => {
    if (pages.length && pageWindow.length) {
      // there should be no issue with the page being wrong here
      onPage?.(pages[pageWindow[pageFocus]]);
    }
  }, [pageNumber]);

  useEffect(() => {
    if (pageNumber > pageCount) {
      console.log([pageNumber, pageCount, pageFocus]);
      setPageNumber(1);
    }
  }, [pageCount]);

  useUpdateEffect(() => {
    setPages([]);
    setPageWindow([]);
  }, [scaling]);

  useUpdateEffect(() => {
    setPageNumber(1);
    setPageFocus(0);
    setPages([]);
    setPageWindow([]);
    setIsEnd(false);
  }, [scaling, item]);

  // Two layers of "windows", one for the actual pages fetched from the server (remote), another for the active pages to be loaded (images) for the client (local)
  // When the local window runs out of pages, the remote window readjusts and fetches more pages if needed

  // // Remote window, track page focus and fetch missing pages from the server when needed
  useUpdateEffect(() => {
    if (isNaN(pageFocus)) {
      return;
    }

    let fetchMore: 'left' | 'right' = undefined;

    if (pageWindow.length) {
      // how close to the edge of the local window needed to be before more pages should be fetched
      const offset = Math.min(Math.floor(windowSize / 2), 3);

      const leftPageFocusOffset = Math.max(pageFocus - offset, 0);
      const rightPageFocusOffset = Math.min(
        pageFocus + offset,
        pageWindow.length - 1
      );

      // when close to the left side and the page on the left side is not the first, fetch more
      if (
        pageWindow[leftPageFocusOffset] === 0 &&
        pages[pageWindow[leftPageFocusOffset]].number !== 1
      ) {
        fetchMore = 'left';
      }
      // when close to the right side and the page on the right side is not the last, fetch more
      else if (
        pageWindow[rightPageFocusOffset] === pages.length - 1 &&
        pages[pageWindow[rightPageFocusOffset]].number !== pageCount
      ) {
        fetchMore = 'right';
      }
    } else if (pages.length || pageCount) {
      fetchMore = 'left';
    }

    const pNumber = pageWindow.length
      ? pages[pageWindow[pageFocus]].number
      : pageNumber;

    if (
      fetchMore &&
      !fetchingMoreRef.current.fetching &&
      (!pages.length || fetchingMoreRef.current.previousNumber !== pNumber)
    ) {
      // when the focus gets corrected by the local window, this hook will retrigger so we need to make sure we don't refetch
      fetchingMoreRef.current.previousNumber = pNumber;

      fetchingMoreRef.current.fetching = true;
      Query.get(QueryType.PAGES, {
        gallery_id: item.id,
        number: pNumber,
        fields: pageFields,
        window_size: remoteWindowSize,
      })
        .then((r) => {
          // required, or pageWindow hook won't see it in time
          fetchingMoreRef.current.fetching = false;
          setPages(r.data.items as ReaderData[]);
          setPageCount(r.data.count);
        })
        .finally(() => {
          // in case of error
          fetchingMoreRef.current.fetching = false;
        });
    }
  }, [pageWindow, pageFocus]);

  // Local window, set window of active local pages based on page number
  useEffect(() => {
    if (fetchingMoreRef.current.fetching) {
      return;
    }

    const idx = Math.max(
      0,
      pages.findIndex((p) => p.number === pageNumber)
    );

    const windowed = windowedPages(
      idx,
      windowSize,
      Math.max(pages.length - 1, 0)
    );

    // correct focus, this is after more pages have been fetched, then the focus can point to the wrong page
    windowed.forEach((n, i) => {
      if (pages[n].number === pageNumber && i !== pageFocus) {
        setPageFocus(i);
      }
    });

    if (!_.isEqual(pageWindow, windowed)) {
      setPageWindow(windowed);
    }
  }, [windowSize, pageNumber, pages, pageWindow]);

  // fetch missing images for windowed pages

  useEffect(() => {
    if (!fetchingImagesRef.current) {
      fetchingImagesRef.current = [];
    }

    // only if not already fetching
    if (
      pageWindow.length &&
      !fetchingImagesRef.current.includes(
        pages[pageWindow[pageWindow.length - 1]].id
      )
    ) {
      // only pages that dont have profile data and not currently fetching
      const fetch_ids: number[] = [];
      pageWindow
        .map((i) => pages[i])
        .filter((p) => !p?.profile?.data)
        .forEach((p) => {
          if (!fetchingImagesRef.current.includes(p.id)) {
            fetchingImagesRef.current.push(p.id);
            fetch_ids.push(p.id);
          }
        });

      if (fetch_ids.length) {
        // this updates page with new fetched profile

        // TODO: pages is part of state so may be stale, consider ref?

        let size = ImageSize.x1280;
        if (scaling !== undefined) {
          size = scaling === 0 ? getOptimalImageSize() : scaling;
        }

        Query.get(QueryType.PROFILE, {
          item_type: ItemType.Page,
          item_ids: fetch_ids,
          profile_options: {
            size,
          },
        }).then((r) => {
          const spec = {};

          Object.entries(r.data).forEach(([k, v]) => {
            const pid = parseInt(k);
            const pidx = pages.findIndex((x) => x.id === pid);

            const r_idx = fetchingImagesRef.current.indexOf(pid);
            if (r_idx !== -1) {
              fetchingImagesRef.current.splice(r_idx, 1);
            }

            if (pidx !== -1) {
              spec[pidx] = {
                $set: {
                  ...pages[pidx],
                  profile: v,
                },
              };
            }
          });

          if (Object.keys(spec).length) {
            setPages(update(pages, spec));
          }
        });
      }
    }
  }, [pageWindow, pages, scaling]);

  const onFocusChild = useCallback(
    (child) => {
      const childNumber = Math.max(0, Math.min(child, pageWindow.length - 1));
      setPageFocus(childNumber);

      // make sure page number is in sync
      if (pages.length && pageWindow.length) {
        const page = pages[pageWindow[childNumber]];
        if (page.number !== pageNumber) {
          setPageNumber(page.number);
        }
      } else {
        setPageNumber(0);
      }
    },
    [pageWindow, pages]
  );

  return (
    <Dimmer.Dimmable
      as={Segment}
      inverted
      blurring
      dimmed={isEnd}
      className={classNames({ 'no-padding-segment': !padded }, 'no-margins')}>
      <Dimmer
        active={isEnd}
        className="fluid-dimmer"
        onClickOutside={useCallback(() => {
          setIsEnd(false);
        }, [])}>
        {children}
      </Dimmer>
      <Canvas
        stateKey={stateKey}
        wheelZoom={wheelZoom}
        direction={direction}
        autoNavigate={autoNavigate}
        autoNavigateInterval={autoNavigateInterval}
        label={useMemo(
          () => (
            <Label size="big" className="translucent-black">
              {pageNumber}/{pageCount}
            </Label>
          ),
          [pageNumber, pageCount]
        )}
        focusChild={pageFocus}
        onFocusChild={onFocusChild}
        onEnd={useCallback(() => {
          if (!fetchingMoreRef.current.fetching) {
            // is probably fetching more pages, don't end yet
            if (pageCount && !pageWindow.length) {
              return;
            }
            setIsEnd(true);
          }
        }, [pageCount, pageWindow])}>
        {pageWindow.map((i, idx) => (
          <CanvasImage
            key={`${pages[i].id}-${stretchFit}`}
            href={pages[i]?.profile?.data}
            fit={fit}
            stretchFit={stretchFit}
            direction={direction}
            wheelZoom={wheelZoom}
            focused={idx === pageFocus}
          />
        ))}
      </Canvas>
    </Dimmer.Dimmable>
  );
}

const gdata = (id: number, title = 'title_test', artist = 'testy') => ({
  id,
  preferred_title: { name: title },
  artists: [{ preferred_name: { name: artist } }],
});

function ReadNext({
  random,
  nextChapter,
  nextInReadingList,
  stateKey,
}: {
  random?: DeepPick<ServerGallery, 'id'>;
  nextChapter?: GalleryCardData;
  nextInReadingList?: GalleryCardData;
  stateKey?: string;
}) {
  const router = useRouter();
  const isEnd = useRecoilValue(ReaderState.endReached(stateKey));

  const [countDownEnabled, setCountDownEnabled] = useState<
    'queue' | 'chapter' | 'readinglist'
  >();

  const [countdown, setCountdown] = useState(15);
  const readingQueue = useRecoilValue(AppState.readingQueue);

  const { data: queueData, isLoading } = useQueryType(
    QueryType.ITEM,
    {
      item_type: ItemType.Gallery,
      item_id: readingQueue?.[0],
      profile_options: { size: ImageSize.Medium },
      fields: galleryCardDataFields,
    },
    { enabled: !!readingQueue.length }
  );

  useHarmonicIntervalFn(
    () => {
      if (countdown === 1) {
        let nextId = 0;
        switch (countDownEnabled) {
          case 'chapter':
            nextId = nextChapter.id;
            break;
          case 'queue':
            nextId = queueData.data.id;
            break;
          case 'readinglist':
            nextId = nextInReadingList.id;
            break;
        }

        if (nextId) {
          router.push(
            urlstring(`/item/gallery/${nextId}/page/1`, urlparse().query as any)
          );
        }
      }
      setCountdown(Math.max(countdown - 1, 0));
    },
    isEnd && !isLoading && countDownEnabled && countdown ? 1000 : null
  );

  useEffect(() => {
    const t = 15;
    if (queueData) {
      setCountDownEnabled('queue');
      setCountdown(t);
    } else if (nextChapter) {
      setCountDownEnabled('chapter');
      setCountdown(t);
    } else if (nextInReadingList) {
      setCountDownEnabled('readinglist');
      setCountdown(t);
    } else {
      setCountDownEnabled(undefined);
    }
  }, [isEnd, nextChapter, nextInReadingList, queueData]);

  return (
    <Grid
      centered
      columns="equal"
      onClick={() => {
        setCountDownEnabled(undefined);
      }}>
      <Grid.Row>
        <Grid.Column textAlign="center">
          <Header
            textAlign="center"
            size="medium">{t`Read the next one`}</Header>
          {!!random && (
            <Link
              passHref
              href={urlstring(
                `/item/gallery/${random.id}/page/1`,
                urlparse().query as any
              )}>
              <Button as="a">{t`Pick a random`}</Button>
            </Link>
          )}
        </Grid.Column>
      </Grid.Row>
      <Grid.Row>
        {!!queueData && (
          <Grid.Column textAlign="center">
            <Segment tertiary basic>
              <Header textAlign="center" size="small">
                {t`Next in queue...`}{' '}
                {countDownEnabled === 'queue'
                  ? '(' + t`in ${countdown}` + ')'
                  : ''}
              </Header>
              <GalleryCard
                size="medium"
                data={queueData.data as ServerGallery}
              />
            </Segment>
          </Grid.Column>
        )}

        {!!nextChapter && (
          <Grid.Column textAlign="center">
            <Segment tertiary basic>
              <Header textAlign="center" size="small">
                {t`Next chapter...`}{' '}
                {countDownEnabled === 'chapter'
                  ? '(' + t`in ${countdown}` + ')'
                  : ''}
              </Header>
              <GalleryCard size="medium" data={nextChapter} />
            </Segment>
          </Grid.Column>
        )}

        {!!nextInReadingList && (
          <Grid.Column textAlign="center">
            <Segment tertiary basic>
              <Header textAlign="center" size="small">
                {t`Next in reading list...`}{' '}
                {countDownEnabled === 'readinglist'
                  ? '(' + t`in ${countdown}` + ')'
                  : ''}
              </Header>
              <GalleryCard size="medium" data={nextInReadingList} />
            </Segment>
          </Grid.Column>
        )}
      </Grid.Row>
    </Grid>
  );
}

function EndRating() {
  return (
    <Grid as={Segment} basic textAlign="center">
      <Grid.Row>
        <Grid.Column>
          <Icon className="meh outline" size="big" />
        </Grid.Column>
        <Grid.Column>
          <Icon
            className="meh rolling eyes outline"
            size="big"
            color="yellow"
          />
        </Grid.Column>
        <Grid.Column>
          <Icon className="flushed outline" size="big" color="orange" />
        </Grid.Column>
        <Grid.Column>
          <Icon className="grin hearts outline" size="big" color="red" />
        </Grid.Column>
      </Grid.Row>
      <Grid.Row>
        <Rating size="massive" icon="star" maxRating={10} />
      </Grid.Row>
    </Grid>
  );
}

export function EndContent({
  sameArtist = [],
  series = [],
  readingList = [],
  item,
  stateKey,
  ...readNextProps
}: {
  item?: PartialExcept<ServerGallery, 'id'>;
  sameArtist?: GalleryCardData[];
  series?: GalleryCardData[];
  readingList?: GalleryCardData[];
  stateKey?: string;
} & React.ComponentProps<typeof ReadNext>) {
  const endReached = useRecoilValue(ReaderState.endReached(stateKey));
  const [_readingQueue, setReadingQueue] = useRecoilState(
    AppState.readingQueue
  );
  const readingQueue = _readingQueue.filter((n) => n !== item?.id);

  useEffect(() => {
    if (endReached) {
      if (_readingQueue.includes(item.id)) {
        setReadingQueue(readingQueue);
      }
    }
  }, [endReached, item]);

  const { data: queueData } = useQueryType(
    QueryType.ITEM,
    {
      item_type: ItemType.Gallery,
      item_id: readingQueue,
      profile_options: { size: ImageSize.Small },
      fields: galleryCardDataFields,
    },
    { enabled: !!readingQueue.length }
  );

  return (
    <Grid as={Segment} centered fluid className="max-h-full overflow-auto">
      <Grid.Row>
        <Grid.Column width={16}>
          <Header
            textAlign="center"
            size="large">{t`What did you think?`}</Header>
        </Grid.Column>
        <Grid.Column width={16} textAlign="center">
          <EndRating />
        </Grid.Column>
      </Grid.Row>
      <Grid.Row>
        <Grid.Column>
          <ReadNext
            {...readNextProps}
            stateKey={stateKey}
            nextInReadingList={readingList?.[0]}
          />
        </Grid.Column>
      </Grid.Row>
      <Grid.Row>
        <Grid.Column>
          <Slider
            stateKey="this_queue"
            defaultOpen={false}
            label={t`Queue`}
            color="red">
            {((queueData?.data as any) as ServerGallery[])?.map?.((g) => (
              <GalleryCard key={g.id} size="small" data={g} />
            ))}
          </Slider>
        </Grid.Column>
      </Grid.Row>
      {!!series.length && (
        <Grid.Row>
          <Grid.Column>
            <Slider stateKey="series" label={t`Series`} color="teal">
              {series.map((i) => (
                <GalleryCard key={i.id} size="small" data={i} />
              ))}
            </Slider>
          </Grid.Column>
        </Grid.Row>
      )}
      <Grid.Row>
        <Grid.Column>
          <Slider
            stateKey="reading_list"
            autoplay
            label={t`Reading list`}
            defaultShow={false}
            color="violet">
            {readingList.map((i) => (
              <GalleryCard key={i.id} size="small" data={i} />
            ))}
          </Slider>
        </Grid.Column>
      </Grid.Row>
      <Grid.Row>
        <Grid.Column>
          <Slider
            stateKey="same_artist"
            label={t`From same artist`}
            defaultShow={!sameArtist?.length}
            color="blue">
            {sameArtist.map((i) => (
              <GalleryCard key={i.id} size="small" data={i} />
            ))}
          </Slider>
        </Grid.Column>
      </Grid.Row>
      <Grid.Row>
        <Grid.Column>
          <Slider autoplay stateKey="similar" label={t`Just like this one`}>
            <GalleryCard size="small" data={gdata(8)} />
            <GalleryCard size="small" data={gdata(9)} />
            <GalleryCard size="small" data={gdata(10)} />
            <GalleryCard size="small" data={gdata(11)} />
          </Slider>
        </Grid.Column>
      </Grid.Row>
    </Grid>
  );
}

const sizeOptions = [
  { key: 'auto', text: t`Auto`, value: ItemFit.Auto },
  { key: 'contain', text: t`Contain`, value: ItemFit.Contain },
  { key: 'height', text: t`Height`, value: ItemFit.Height },
  { key: 'width', text: t`Width`, value: ItemFit.Width },
];

const scalingOptions = [
  { key: 0, text: t`Auto`, value: 0 },
  { key: ImageSize.Original, text: t`Original`, value: ImageSize.Original },
  { key: ImageSize.x2400, text: t`x2400`, value: ImageSize.x2400 },
  { key: ImageSize.x1600, text: t`x1600`, value: ImageSize.x1600 },
  { key: ImageSize.x1280, text: t`x1280`, value: ImageSize.x1280 },
  { key: ImageSize.x960, text: t`x960`, value: ImageSize.x960 },
  { key: ImageSize.x768, text: t`x768`, value: ImageSize.x768 },
];

const directionOptions = [
  {
    key: ReadingDirection.TopToBottom,
    text: t`↓ Top to Bottom`,
    value: ReadingDirection.TopToBottom,
  },
  {
    key: ReadingDirection.LeftToRight,
    text: t`→ Left to Right`,
    value: ReadingDirection.LeftToRight,
  },
];

export function ReaderSettings({
  stateKey,
  ...props
}: React.ComponentProps<typeof Segment> & { stateKey?: string }) {
  const [fit, setFit] = useRecoilState(ReaderState.fit(stateKey));
  const [stretchFit, setStretchFit] = useRecoilState(
    ReaderState.stretchFit(stateKey)
  );
  const [autoNavigateInterval, setAutoNavigateInterval] = useRecoilState(
    ReaderState.autoNavigateInterval(stateKey)
  );
  const [scaling, setScaling] = useRecoilState(ReaderState.scaling(stateKey));
  const [wheelZoom, setWheelZoom] = useRecoilState(
    ReaderState.wheelZoom(stateKey)
  );
  const [direction, setDirection] = useRecoilState(
    ReaderState.direction(stateKey)
  );

  return (
    <Segment basic size="tiny" {...props}>
      <Form size="small">
        <Form.Field
          control={Select}
          disabled
          label={t`Direction`}
          nChange={useCallback((ev, data) => {
            ev.preventDefault();
            setDirection(data.value);
          }, [])}
          value={direction}
          placeholder={t`Direction`}
          defaultValue={ReadingDirection.TopToBottom}
          options={directionOptions}
        />

        <Form.Group>
          <Form.Field
            control={Select}
            label={t`Fit`}
            placeholder={t`Fit`}
            onChange={useCallback((ev, data) => {
              ev.preventDefault();
              setFit(data.value);
            }, [])}
            value={fit}
            defaultValue={ItemFit.Auto}
            options={sizeOptions}
            width={10}
          />

          <Form.Field width={6}>
            <Checkbox
              label={t`Stretch`}
              checked={stretchFit}
              onChange={useCallback((ev, data) => {
                ev.preventDefault();
                setStretchFit(data.checked);
              }, [])}
            />
          </Form.Field>
        </Form.Group>

        <Form.Field
          control={Select}
          label={t`Scaling`}
          onChange={useCallback((ev, data) => {
            ev.preventDefault();
            setScaling(data.value);
          }, [])}
          value={scaling}
          placeholder={t`Scaling`}
          defaultValue={0}
          options={scalingOptions}
        />

        <Form.Field
          onChange={useCallback((ev) => {
            ev.preventDefault();
            const v = parseFloat(ev.target.value);
            setAutoNavigateInterval(Math.max(3, isNaN(v) ? 12 : v));
          }, [])}>
          <label>{t`Auto navigate interval (seconds)`}</label>
          <input value={autoNavigateInterval} type="number" min={0} />
        </Form.Field>

        <Form.Field>
          <label>{t`Zoom with mouse wheel`}</label>
          <Checkbox
            toggle
            checked={wheelZoom}
            onChange={useCallback((ev, data) => {
              ev.preventDefault();
              setWheelZoom(data.checked);
            }, [])}
          />
        </Form.Field>
      </Form>
    </Segment>
  );
}

export function ReaderSettingsButton({
  stateKey,
  ...props
}: React.ComponentProps<typeof Button> & {
  stateKey?: string;
}) {
  return (
    <Modal
      size="mini"
      closeIcon
      trigger={<Button icon="setting" secondary basic circular {...props} />}>
      <Modal.Header>
        <Icon name="setting" /> {t`Reader Settings`}
      </Modal.Header>
      <Modal.Content>
        <ReaderSettings stateKey={stateKey} className="no-padding-segment" />
      </Modal.Content>
    </Modal>
  );
}

export function ReaderAutoNavigateButton({
  stateKey,
  ...props
}: React.ComponentProps<typeof Button> & {
  stateKey?: string;
}) {
  const [autoNavigate, setAutoNavigate] = useRecoilState(
    ReaderState.autoNavigate(stateKey)
  );

  const pageNumber = useRecoilValue(ReaderState.pageNumber(stateKey));
  const pageCount = useRecoilValue(ReaderState.pageCount(stateKey));
  const autoNavigateCounter = useRecoilValue(
    ReaderState.autoNavigateCounter(stateKey)
  );

  return (
    <Button
      icon={
        autoNavigate ? (pageNumber === pageCount ? 'pause' : 'play') : 'pause'
      }
      content={
        autoNavigate && autoNavigateCounter && autoNavigateCounter <= 10
          ? autoNavigateCounter
          : undefined
      }
      secondary
      color={
        autoNavigate
          ? pageNumber === pageCount
            ? 'orange'
            : 'green'
          : undefined
      }
      basic
      circular
      {...props}
      onClick={useCallback(() => {
        setAutoNavigate(!autoNavigate);
      }, [autoNavigate])}
    />
  );
}