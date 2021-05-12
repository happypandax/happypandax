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
  useFullscreen,
  useKey,
  useKeyPress,
  useKeyPressEvent,
  useMount,
} from 'react-use';
import useMeasureDirty from 'react-use/lib/useMeasureDirty';
import classNames from 'classnames';
import t from '../misc/lang';
import { useRefEvent, useDocumentEvent, useInterval } from '../hooks/utils';
import _ from 'lodash';
import { useLayoutEffect } from 'react';

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
  autoNavigateInterval = 5000,
  autoNavigate,
  wheelZoom,
  label,
  onFocusChild,
}: {
  children?: any;
  direction?: ReadingDirection;
  label?: React.ReactNode;
  autoNavigateInterval?: number;
  focusChild?: number;
  wheelZoom?: boolean;
  autoNavigate?: boolean;
  onFocusChild?: (number) => void;
}) {
  const ref = useRef<HTMLDivElement>();
  const refMouseDownEvent = useRef<React.MouseEvent<HTMLDivElement>>(null);
  const refIsPanning = useRef<boolean>(false);
  const refIsScrollPanning = useRef<boolean>(false);
  const refScrollPan = useRef<{ x: number; y: number }>({ x: 0, y: 0 });
  const refContent = useRef<HTMLDivElement>();
  const refScrollComplete = useRef<() => void>();
  const [showFullscreen, setShowFullscreen] = useState(false);
  const isFullscreen = useFullscreen(ref, showFullscreen, {
    onClose: () => setShowFullscreen(false),
  });

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
      if (e.defaultPrevented || wheelZoom) {
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
    [scroller, onScrollPanEnd, direction, wheelZoom]
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
        child =
          (scroller.getValues().top + ref.current.clientHeight / 4) /
          ref.current.clientHeight;
        break;
      }
    }
    return Math.floor(child);
  }, [direction, scroller]);

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
    },
    [scroller]
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
      onFocusChild?.(child);
    };
  }, [onFocusChild, getCurrentChild, scroller]);

  // auto navigate
  useInterval(
    () => {
      scrollToChild(getNextChild(), true);
    },
    autoNavigate ? autoNavigateInterval : null,
    [getNextChild]
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

const PLACEHOLDERS = _.range(59).map((p) => ({
  number: p + 1,
  url: `https://via.placeholder.com/1400x2200/cc${(10 * (p + 1)).toString(
    16
  )}cc/ffffff?text=Page+${p + 1}`,
}));

export default function Reader() {
  const windowSize = 6;
  const [pageCount, setPageCount] = useState(PLACEHOLDERS.length);
  const [pageNumber, setPageNumber] = useState(1);
  const [pageFocus, setPageFocus] = useState(0);
  const [pages, setPages] = useState([]);

  useEffect(() => {
    const windowed = windowedPages(pageNumber, windowSize, pageCount);
    setPages(
      windowed.map((n, i) => {
        if (n === pageNumber) {
          setPageFocus(i % windowSize);
        }
        return PLACEHOLDERS[n - 1];
      })
    );
  }, [pageCount, pageNumber]);

  useEffect(() => {
    if (pages.length) {
      if (pages[pageFocus].number !== pageNumber) {
        setPageNumber(pages[pageFocus].number);
      }
    }
  }, [pageFocus, pages, pageNumber]);

  const onFocusChild = useCallback(
    (child) => {
      const childNumber = Math.max(0, Math.min(child, pages.length - 1));
      setPageFocus(childNumber);
    },
    [pages]
  );

  return (
    <Segment inverted>
      <Canvas
        autoNavigate={false}
        wheelZoom={false}
        label={useMemo(
          () => (
            <Label size="big" className="translucent-black">
              {pageNumber}/{pageCount}
            </Label>
          ),
          [pageNumber, pageCount]
        )}
        focusChild={pageFocus}
        onFocusChild={onFocusChild}>
        {pages.map((p, idx) => (
          <CanvasImage
            key={p.number}
            href={p.url}
            fit={ItemFit.Width}
            wheelZoom={false}
            focused={idx === pageFocus}
          />
        ))}
      </Canvas>
    </Segment>
  );
}
