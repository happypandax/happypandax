import {
  useEffect,
  useMemo,
  useRef,
  useState,
  useCallback,
  createContext,
} from 'react';
import React from 'react';
import {
  Segment,
  Menu,
  Label,
  Icon,
  Grid,
  Dimmer,
  Table,
  Header,
  Tab,
  Ref,
  Modal,
  Button,
} from 'semantic-ui-react';

import Scroller from '@twiddly/scroller';
import {
  useEvent,
  useInterval,
  useKey,
  useKeyPress,
  useKeyPressEvent,
  useMount,
} from 'react-use';
import useMeasureDirty from 'react-use/lib/useMeasureDirty';
import classNames from 'classnames';
import t from '../misc/lang';
import { useRefEvent, useDocumentEvent } from '../hooks/utils';
import _ from 'lodash';

export enum ReadingDirection {
  TopToBottom,
  LeftToRight,
}

export enum ItemFit {
  Height,
  Width,
  Contain,
  Auto,
}

export function windowedPages(page: number, size: number, total: number) {
  const start = 0;

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
  wheelPan,
  focused,
}: {
  href: string;
  number: number;
  fit?: ItemFit;
  stretchFit?: boolean;
  wheelPan?: boolean;
  direction?: ReadingDirection;
  focused?: boolean;
}) {
  const preload = useRef(new Image());
  preload.current.src = href;

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

  useEffect(() => {
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

  // initialize Scroller
  useEffect(() => {
    const func = scrollRender.bind(undefined, refContent.current);
    const s = new Scroller(
      (left, top, zoom) => {
        let offsetLeft = 0;
        let offsetTop = 0;
        //  make sure item is centered if containted by canvas
        if (itemContained({ left, top, zoom }, true, false)) {
          offsetLeft =
            (ref.current.clientWidth - left) / 2 -
            (refContent.current.offsetWidth * zoom) / 2;
          // console.log([
          //   ref.current.clientWidth,
          //   refContent.current.offsetWidth,
          // ]);
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
        func(left - offsetLeft, top - offsetTop, zoom);
        setZoomLevel(zoom);
      },
      {
        scrollingX: true,
        scrollingy: true,
        bouncing: true,
        locking: false,
        zooming: true,
        animating: true,
        animationDuration: 250,
      }
    );

    setScroller(s);
  }, []);

  // lock scrolling in direction where item is fully contained
  useEffect(() => {
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
  useEffect(() => {
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

  useDocumentEvent(
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

  useDocumentEvent(
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
      if (!wheelPan || refControlKeyPressed.current) {
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
    [scroller, wheelPan]
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
  wheelPan,
  onFocusChild,
}: {
  children?: any;
  direction?: ReadingDirection;
  focusChild?: number;
  wheelPan?: boolean;
  onFocusChild?: (number) => void;
}) {
  const ref = useRef<HTMLDivElement>();
  const refMouseDownEvent = useRef<React.MouseEvent<HTMLDivElement>>(null);
  const refIsPanning = useRef<boolean>(false);
  const refIsScrollPanning = useRef<boolean>(false);
  const refScrollPan = useRef<{ x: number; y: number }>({ x: 0, y: 0 });
  const refContent = useRef<HTMLDivElement>();
  const refScrollComplete = useRef<() => void>();

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

  useDocumentEvent(
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

  useDocumentEvent(
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

  useDocumentEvent(
    'touchmove',
    (e) => {
      scroller.doTouchMove(e.touches, e.timeStamp);
    },
    {},
    [scroller],
    () => !!window.ontouchstart
  );

  useDocumentEvent(
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

  useRefEvent(
    ref,
    'wheel',
    (e) => {
      if (e.defaultPrevented || !wheelPan) {
        return;
      }

      e.preventDefault();
      e.stopPropagation();

      if (!refIsScrollPanning.current) {
        refIsScrollPanning.current = true;
        const { left, top } = scroller.getValues();
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

      onScrollPanEnd(e);
    },
    { passive: false },
    [scroller, onScrollPanEnd, direction, wheelPan]
  );

  const { width: refWidth, height: refHeight } = useMeasureDirty(ref);

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
        child =
          (scroller.getValues().top + ref.current.clientHeight / 4) /
          ref.current.clientHeight;
        break;
      }
    }
    return Math.floor(child);
  }, [direction, scroller]);

  useEffect(() => {
    if (!scroller) return;
    if (getCurrentChild() === focusChild) return;

    const childrenArray = React.Children.toArray(children);
    const childNumber = Math.max(
      0,
      Math.min(focusChild, childrenArray.length - 1)
    );
    const { left, top } = scroller.getValues();
    if (direction === ReadingDirection.TopToBottom) {
      scroller.scrollTo(left, childNumber * ref.current.clientHeight, true);
    }
  }, [children, focusChild, scroller, getCurrentChild]);

  useEffect(() => {
    if (!scroller) return;
    refScrollComplete.current = () => {
      onFocusChild?.(getCurrentChild());
    };
  }, [onFocusChild, getCurrentChild, scroller]);

  return (
    <div
      ref={ref}
      className="reader-container"
      tabIndex="-1"
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

            switch (direction) {
              case ReadingDirection.TopToBottom: {
                if (e.pageY > ref.current.clientHeight / 2 + deadSpaceY) {
                  onFocusChild?.(childNumber + 1);
                } else if (
                  e.pageY <
                  ref.current.clientHeight / 2 - deadSpaceY
                ) {
                  onFocusChild?.(childNumber - 1);
                }
                break;
              }
              case ReadingDirection.LeftToRight: {
                if (e.pageX > ref.current.clientWidth / 2 + deadSpaceX) {
                  onFocusChild?.(childNumber + 1);
                } else if (e.pageX > ref.current.clientWidth / 2 - deadSpaceX) {
                  onFocusChild?.(childNumber - 1);
                }
                break;
              }
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

export default function Reader() {
  const [pageNumber, setPage] = useState(0);
  const [pageFocus, setPageFocus] = useState(0);
  const [pages, setPages] = useState([]);

  useEffect(() => {
    const windowed = windowedPages(pageNumber, 4, 15);
    setPages([
      {
        number: 1,
        url:
          'https://chraqjj.uqpgakytxkuh.hath.network:2242/h/b08842ef5480f5c4fe4f603bfba172ed8bb7f3d3-257916-1280-1808-jpg/keystamp=1620667800-826b1fe3b7;fileindex=75795344;xres=1280/001.jpg',
      },
      {
        number: 2,
        url:
          'https://zgpiqap.kqpipytyzhaf.hath.network/h/746c8edb7cbefe8725c7ab6215cf79b0257ece9b-365555-1280-1833-jpg/keystamp=1620667800-0c72865141;fileindex=92420511;xres=2400/004.jpg',
      },
      {
        number: 3,
        url:
          'https://bghyplb.kdbxcwmghdty.hath.network/h/c7d9d6ab702826fb4cd17b58bf0f39babed35bfc-337652-1280-1818-jpg/keystamp=1620667800-00111ba459;fileindex=92420512;xres=2400/005.jpg',
      },
    ]);
  }, [pageNumber]);

  const onFocusChild = useCallback(
    (child) => {
      const childNumber = Math.max(0, Math.min(child, pages.length - 1));
      console.log('Focusing child %d', childNumber);
      setPageFocus(childNumber);
    },
    [pages]
  );

  // useInterval(() => {
  //     setPageFocus(Math.floor(Math.random() * (pages.length - 1 - 0 + 1)) + 0);
  // }, 4000);

  return (
    <Segment inverted>
      <Canvas
        wheelPan={true}
        focusChild={pageFocus}
        onFocusChild={onFocusChild}>
        {pages.map((p, idx) => (
          <CanvasImage
            key={p.number}
            href={p.url}
            number={p.number}
            wheelPan={true}
            focused={idx === pageFocus}
          />
        ))}
      </Canvas>
    </Segment>
  );
}
