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
import { useEvent, useInterval, useMount } from 'react-use';
import useMeasureDirty from 'react-use/lib/useMeasureDirty';
import classNames from 'classnames';
import t from '../misc/lang';
import { useRefEvent, useDocumentEvent } from '../hooks/utils';

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
  fit = ItemFit.Width,
  direction = ReadingDirection.TopToBottom,
  focused,
}: {
  href: string;
  number: number;
  fit?: ItemFit;
  direction?: ReadingDirection;
  focused?: boolean;
}) {
  const preload = useRef(new Image());
  preload.current.src = href;

  const ref = useRef<HTMLDivElement>();
  const refContent = useRef<HTMLImageElement>();
  const refMouseDown = useRef<boolean>(false);

  const [zoomLevel, setZoomLevel] = useState<number>(1);
  const [scroller, setScroller] = useState<Scroller>();

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

  // initialize Scroller
  useEffect(() => {
    const func = scrollRender.bind(undefined, refContent.current);
    const s = new Scroller(
      (left, top, zoom) => {
        let offsetLeft = 0;
        let offsetTop = 0;
        //  make sure item is centered if containted by canvas
        if (!s.__isAnimating) {
          if (itemContained({ left, top, zoom }, true, false)) {
            offsetLeft =
              ref.current.clientWidth / 2 -
              (refContent.current.offsetWidth * zoom) / 2;
            // make sure item is still in view
            offsetLeft = itemContained(
              { left: left - offsetLeft, top, zoom },
              true,
              false
            )
              ? offsetLeft
              : 0;
          }
          if (itemContained({ left, top, zoom }, false, true)) {
            offsetTop =
              ref.current.clientHeight / 2 -
              (refContent.current.offsetHeight * zoom) / 2;

            // make sure item is still in view
            offsetTop = itemContained(
              { left, top: top - offsetTop, zoom },
              false,
              true
            )
              ? offsetTop
              : 0;
          }
        }
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

  const resetZoom = useCallback(() => {
    if (!scroller) return false;
    scroller.scrollTo(0, 0, true, 1);
  }, [scroller]);

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

    const rect = ref.current.getBoundingClientRect();
    const container = ref.current;
    const content = refContent.current;
    scroller.setPosition(0, 0);
    scroller.setDimensions(
      container.clientWidth,
      container.clientHeight,
      content.offsetWidth * 1.02,
      content.offsetHeight * 1.02
    );
  }, [scroller, refWidth, refHeight]);

  // check whether item panning should be possible
  const canPan = useCallback(
    (e) => {
      let panPossible = !itemContained(scroller.getValues());
      if (panPossible) {
        // TODO: check whether item is at boundary in the direction we're reading
      }

      if (panPossible) {
        e.preventDefault();
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

  useRefEvent(
    ref,
    'wheel',
    (e) => {
      e.preventDefault();
      e.stopPropagation();
      const { zoom } = scroller.getValues();
      e.detail;
      const change = e.deltaY > 0 ? 0.8 : 1.33;

      const newZoom = zoom * change;

      const zoomingOut = e.deltaY > 0 ? true : false;

      let zoomLeft = e.pageX;
      let zoomTop = e.pageY;

      if (zoomingOut) {
        // if zooming out, make origin at center of canvas
        zoomLeft = ref.current.clientWidth / 2;
        zoomTop = ref.current.clientHeight / 2;
      }

      scroller.zoomTo(newZoom, true, zoomLeft, zoomTop);
    },
    { passive: false },
    [scroller]
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
          'fit-width': fit === ItemFit.Width,
          'fit-height': fit === ItemFit.Height,
          'fit-contain': fit === ItemFit.Contain,
        })}
      />
    </div>
  );
}

function Canvas({
  children,
  direction = ReadingDirection.TopToBottom,
  focusChild = 0,
  onFocusChild,
}: {
  children?: any;
  direction?: ReadingDirection;
  focusChild?: number;
  onFocusChild?: (number) => void;
}) {
  const ref = useRef<HTMLDivElement>();
  const refMouseDownEvent = useRef<React.MouseEvent<HTMLDivElement>>(null);
  const refIsPanning = useRef<boolean>(false);
  const refContent = useRef<HTMLDivElement>();
  const refScrollComplete = useRef<() => void>();

  const [scroller, setScroller] = useState<Scroller>();

  useEffect(() => {
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
      className="reader-container user-select-none"
      onClick={useCallback(
        (e) => {
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

            switch (direction) {
              case ReadingDirection.TopToBottom: {
                if (e.pageY > ref.current.clientHeight / 2) {
                  onFocusChild?.(childNumber + 1);
                } else {
                  onFocusChild?.(childNumber - 1);
                }
                break;
              }
              case ReadingDirection.LeftToRight: {
                if (e.pageX > ref.current.clientWidth / 2) {
                  onFocusChild?.(childNumber + 1);
                } else {
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
          'https://jhxnekt.ofkqjcvmzmnk.hath.network/h/b08842ef5480f5c4fe4f603bfba172ed8bb7f3d3-257916-1280-1808-jpg/keystamp=1620249900-61bce7e5e8;fileindex=75795344;xres=1280/001.jpg',
      },
      {
        number: 2,
        url:
          'https://vzhwsoo.erfaubxxqhnl.hath.network:2243/h/e70d7f13d7a1a89274d5116300045b4dd365c7d1-354604-1280-1808-jpg/keystamp=1620495900-710fe45b8a;fileindex=92521227;xres=1280/298.jpg',
      },
      {
        number: 3,
        url:
          'https://rlpqxlg.wbybqtnmgqkg.hath.network/h/f018966783720a48e2512272f15a4f53a7289e6f-394452-1280-1808-jpg/keystamp=1620495900-0969018ada;fileindex=92521228;xres=1280/299.jpg',
      },
    ]);
  }, [pageNumber]);

  const onFocusChild = useCallback((child) => {
    console.log('Focusing child %d', child);
    setPageFocus(child);
  }, []);

  // useInterval(() => {
  //     setPageFocus(Math.floor(Math.random() * (pages.length - 1 - 0 + 1)) + 0);
  // }, 4000);

  return (
    <Segment inverted>
      <Canvas focusChild={pageFocus} onFocusChild={onFocusChild}>
        {pages.map((p, idx) => (
          <CanvasImage
            key={p.number}
            href={p.url}
            number={p.number}
            focused={idx === pageFocus}
          />
        ))}
      </Canvas>
    </Segment>
  );
}
