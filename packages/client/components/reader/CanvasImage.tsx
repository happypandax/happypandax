import classNames from 'classnames';
import _ from 'lodash';
import { makeAutoObservable, reaction, toJS } from 'mobx';
import { observer } from 'mobx-react-lite';
import React, { RefObject, useCallback, useMemo } from 'react';
import { useUnmount } from 'react-use';
import { Button, Icon } from 'semantic-ui-react';

import Scroller from '@twiddly/scroller';

import {
  useBodyEvent,
  useEffectAction,
  useRefEvent,
  useTrackDimensions,
} from '../../client/hooks/utils';
import t from '../../client/lang';
import { ItemFit, ReadingDirection } from '../../shared/enums';

import type { CanvasState } from './Canvas';
export function scrollRender(element: HTMLElement, left, top, zoom) {
  if (!element) return;

  const docStyle = document.documentElement.style;

  let engine;
  if (
    // @ts-ignore
    global.opera &&
    // @ts-ignore
    Object.prototype.toString.call(opera) === '[object Opera]'
  ) {
    engine = 'presto';
  } else if ('MozAppearance' in docStyle) {
    engine = 'gecko';
  } else if ('WebkitAppearance' in docStyle) {
    engine = 'webkit';
    // @ts-ignore
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

  requestAnimationFrame(() => {
    if (helperElem.style[perspectiveProperty] !== undefined) {
      element.style[transformProperty] =
        'translate3d(' + -left + 'px,' + -top + 'px,0) scale(' + zoom + ')';
    } else if (helperElem.style[transformProperty] !== undefined) {
      element.style[transformProperty] =
        'translate(' + -left + 'px,' + -top + 'px) scale(' + zoom + ')';
    } else {
      element.style.marginLeft = left ? -left / zoom + 'px' : '';
      element.style.marginTop = top ? -top / zoom + 'px' : '';
      // @ts-ignore
      element.style.zoom = zoom || '';
    }
  });
}

export class CanvasImageState {
  canvasState: CanvasState;
  src: string = '';

  imageFit: ItemFit | undefined = undefined;
  // whether the image is the current child
  isFocused = false;

  autoNavigateEnabled = false;

  isAutoScrolling = false;

  isScrollPanning = false;
  imageZoom = 1;

  containerRef: RefObject<HTMLDivElement>;
  imageRef: RefObject<HTMLImageElement>;
  imageWidth = 0;
  imageHeight = 0;

  onEndReachedCallback: () => void | undefined = undefined;
  onStartReachedCallback: () => void | undefined = undefined;

  private _scroller: Scroller;
  private _scrollPanX = 0;
  private _scrollPanY = 0;

  private _autoSCrollTimerId: any = undefined;
  private _autoSCrollFrameId: any = undefined;
  private _lastAutoScrollSpeed: number | undefined = undefined;

  private _scrollOvershoot = {
    value: 0,
    dir: '',
  };

  private _preloadImage;

  private _disposers: Array<() => void>;

  isPanning = false;

  constructor(canvasState: CanvasState) {
    this.containerRef = React.createRef();
    this.imageRef = React.createRef();

    this.canvasState = canvasState;

    this._scroller = new Scroller(
      (left: number, top: number, zoom: number) =>
        this._onPublish(left, top, zoom),
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

    this._preloadImage = new Image();
    this._preloadImage.onload = this._onLoad;

    this._disposers = [];
    this._disposers.push(
      reaction(
        () => canvasState.fit,
        (fit) => {
          this.adjustFit();
        }
      )
    );

    this.imageZoom = 1;

    makeAutoObservable(this);
  }

  setFocused(isFocused: boolean) {
    this.isFocused = isFocused;
    // reset zoom when not current child
    if (!isFocused) {
      this.resetZoom();

      // stop auto scrolling if not focused
      if (this.isAutoScrolling) {
        console.debug('stopping auto scroll because not focused');
        this.stopAutoScroll();
      }
    }
  }

  private _onPublish(left: number, top: number, zoom: number) {
    const container = this.containerRef?.current;
    const image = this.imageRef?.current;

    if (!container) return;

    let offsetLeft = 0;
    let offsetTop = 0;
    //  make sure item is centered if containted by canvas
    if (
      this.isImageContained({
        left,
        top,
        zoom,
        checkLeft: true,
        checkTop: false,
      })
    ) {
      offsetLeft =
        (container.clientWidth - left) / 2 - (image.offsetWidth * zoom) / 2;
      // console.log([ref.current.clientWidth, refContent.current.offsetWidth]);
      // make sure item is still in view
      // offsetLeft = itemContained(
      //   { left: left - offsetLeft, top, zoom },
      //   true,
      //   false
      // )
      //   ? offsetLeft
      //   : 0;

      // lock scrolling in direction where image is fully contained
      this._scroller.options.scrollingX = false;
    } else {
      this._scroller.options.scrollingX = true;
    }

    if (
      this.isImageContained({
        left,
        top,
        zoom,
        checkLeft: false,
        checkTop: true,
      })
    ) {
      offsetTop =
        (container.clientHeight - top) / 2 - (image.offsetHeight * zoom) / 2;

      // make sure item is still in view
      // offsetTop = itemContained(
      //   { left, top: top - offsetTop, zoom },
      //   false,
      //   true
      // )
      //   ? offsetTop
      //   : 0;

      // lock scrolling in direction where image is fully contained
      this._scroller.options.scrollingX = false;
    } else {
      this._scroller.options.scrollingX = true;
    }

    // console.log('scrolling', [left, top, offsetLeft, offsetTop, zoom]);

    // console.log([left - offsetLeft, top - offsetTop, zoom]);
    scrollRender(image, left - offsetLeft, top - offsetTop, zoom);
    this.imageZoom = zoom;
  }

  canPan(e?: Event) {
    let panPossible = !this.isImageContained(this._scroller.getValues());

    if (panPossible) {
      if (e) e.preventDefault();
      return true;
    }
    return false;
  }

  setHref(href: string) {
    this.src = href;
    this._preloadImage.src = href;
  }

  update() {
    this.adjustFit();
    const { left, top, zoom } = this._scroller.getValues();
    this._onPublish(left, top, zoom);
  }

  private _onLoad = () => {
    const { naturalWidth, naturalHeight } = this._preloadImage;
    this.imageWidth = naturalWidth;
    this.imageHeight = naturalHeight;

    this.adjustFit();
  };

  /**
   * Returns true if the image is contained within the container
   */
  isImageContained({
    left,
    top,
    zoom,
    checkLeft = true,
    checkTop = true,
  }: {
    left: number;
    top: number;
    zoom: number;
    checkLeft?: boolean;
    checkTop?: boolean;
  }) {
    const container = this.containerRef.current;
    const image = this.imageRef.current;

    const leftContained =
      container.clientWidth >= image.offsetWidth * zoom + Math.abs(left);
    const topContained =
      container.clientHeight >= image.offsetHeight * zoom + Math.abs(top);

    return checkLeft && checkTop
      ? leftContained && topContained
      : checkLeft
      ? leftContained
      : topContained;
  }

  onMouseMove = (e: MouseEvent) => {
    if (!this.isPanning) {
      return;
    }

    this._scroller.doTouchMove(
      [
        {
          pageX: e.pageX,
          pageY: e.pageY,
        },
      ],
      e.timeStamp
    );
  };

  onMouseUp(e: MouseEvent) {
    if (this.isPanning) {
      this._scroller.doTouchEnd(e.timeStamp);
    }
    this.isPanning = false;
  }

  onMouseDown(e: MouseEvent) {
    console.debug('mouse down');
    if (e.defaultPrevented) {
      return;
    }
    if (this.canPan(e)) {
      this._scroller.doTouchStart(
        [
          {
            pageX: e.pageX,
            pageY: e.pageY,
          },
        ],
        e.timeStamp
      );

      this.isPanning = true;
    }
  }

  onTouchStart(e: TouchEvent) {
    console.debug('start touch');
    if (e.defaultPrevented) {
      return;
    }
    if (this.canPan(e)) {
      e.preventDefault();
      this._scroller.doTouchStart(e.touches, e.timeStamp);
      this.isPanning = true;
    }
  }

  onTouchMove(e: TouchEvent) {
    if (!this.isPanning) {
      return;
    }
    e.preventDefault();
    this._scroller.doTouchMove(e.touches, e.timeStamp);
  }

  onTouchEnd(e: TouchEvent) {
    if (this.isPanning) {
      e.preventDefault();
      this._scroller.doTouchEnd(e.timeStamp);
    }
    this.isPanning = false;
  }

  private _resetScrollOvershoot = _.debounce(function _resetScrollOvershoot(
    this: CanvasImageState
  ) {
    this._scrollOvershoot.dir = '';
    this._scrollOvershoot.value = 0;
  },
  100);

  private endReached = _.debounce(
    _.throttle(function endReached(this: CanvasImageState) {
      this.stopAutoScroll();

      if (this.isFocused) {
        this.onEndReachedCallback?.();
      }
    }, 600),
    150
  );

  private startReached = _.debounce(
    _.throttle(function startReached(this: CanvasImageState) {
      if (this.isFocused) {
        this.onStartReachedCallback?.();
      }
    }, 600),
    150
  );

  onWheel(e: WheelEvent) {
    const state = this.canvasState;
    const container = this.containerRef.current;

    if (e.defaultPrevented) {
      return;
    }

    if ((e.ctrlKey && !state.wheelZoom) || (state.wheelZoom && !e.ctrlKey)) {
      // zoom with scroll

      const { zoom, left, top } = this._scroller.getValues();
      const change = e.deltaY > 0 ? 0.88 : 1.28;

      const newZoom = zoom * change;

      const zoomingOut = e.deltaY > 0 ? true : false;

      let zoomLeft = e.pageX - container.clientWidth / 2;
      let zoomTop = e.pageY - container.clientHeight / 2;

      if (zoomingOut) {
        // if zooming out, always zoom out from same origin
        zoomLeft = 0;
        zoomTop = 0;
      }

      this._scroller.zoomTo(newZoom, true, zoomLeft, zoomTop);
    } else {
      const { left, top, zoom } = this._scroller.getValues();
      const { left: scrollMaxLeft, top: scrollMaxTop } =
        this._scroller.getScrollMax();

      if (!this.isScrollPanning) {
        this.isScrollPanning = true;
        this.canvasState.isPanning = true;
        this._scrollPanX = left;
        this._scrollPanY = top;
      }

      const force = 0.15;

      const deltaX =
        e.deltaY > 0
          ? container.clientWidth * force
          : -container.clientWidth * force;

      const deltaY =
        e.deltaY > 0
          ? container.clientHeight * force
          : -container.clientHeight * force;

      const scrollingDown = e.deltaY > 0 ? true : false;

      // check if item has reached boundary (this will always only check the boundary in y-axis since we're assuming height > width for manga)
      // can be improved to take into account reading direction, item fit and aspect ratio
      switch (state.direction) {
        case ReadingDirection.LeftToRight:
        case ReadingDirection.TopToBottom: {
          if (this._scrollPanY === top) {
            // minus 1 to account for rounding errors
            if (
              scrollingDown &&
              (this._scrollPanY >= scrollMaxTop - 1 || !this.canPan())
            ) {
              // calculate overshoot
              if (this._scrollOvershoot.dir === 'down') {
                this._scrollOvershoot.value += deltaY;
              } else {
                this._scrollOvershoot.dir = 'down';
                this._scrollOvershoot.value = 0;
              }

              console.debug(toJS(this._scrollOvershoot));

              if (
                this._scrollOvershoot.dir === 'down' &&
                this._scrollOvershoot.value >= 300
              ) {
                this.endReached();
              }

              this._resetScrollOvershoot();
              return;
            }
            if (!scrollingDown && this._scrollPanY <= 0) {
              // calculate overshoot
              if (this._scrollOvershoot.dir === 'top') {
                this._scrollOvershoot.value += Math.abs(deltaY);
              } else {
                this._scrollOvershoot.dir = 'top';
                this._scrollOvershoot.value = 0;
              }

              if (
                this._scrollOvershoot.dir === 'top' &&
                this._scrollOvershoot.value >= 300
              ) {
                this.startReached();
              }

              this._resetScrollOvershoot();
              return;
            }
          }
          break;
        }
      }
      // pan with scroll
      if (this.canPan()) {
        e.preventDefault();
        e.stopPropagation();

        // scroll in the reading direction (this will always scroll in y-axis since we're assuming height > width for manga)
        // can be improved to take into account reading direction, item fit and aspect ratio
        switch (state.direction) {
          case ReadingDirection.LeftToRight:
          case ReadingDirection.TopToBottom:
            this._scrollPanY = Math.max(
              0,
              Math.min(this._scrollPanY + deltaY, scrollMaxTop)
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

        this._scroller.scrollTo(this._scrollPanX, this._scrollPanY, true);

        this._onScrollPanEnd(e);
      }
    }
  }

  adjustFit() {
    const state = this.canvasState;
    const image = this.imageRef.current;

    if (!image) {
      return;
    }

    const { offsetHeight, offsetWidth } = image;

    if (state.fit === ItemFit.Contain) {
      if (offsetWidth >= offsetHeight) {
        this.imageFit = ItemFit.Width;
      } else {
        this.imageFit = ItemFit.Height;
      }
    } else if (state.fit === ItemFit.Auto) {
      if (offsetHeight > offsetWidth) {
        this.imageFit = ItemFit.Width;
      } else if (offsetWidth > offsetHeight) {
        this.imageFit = ItemFit.Height;
      } else {
        this.imageFit = undefined;
      }
    } else {
      this.imageFit = state.fit;
    }

    this.adjust();
  }

  adjust = _.debounce(function adjust() {
    this._scroller.setPosition(0, 0);
    const container = this.containerRef.current;
    const image = this.imageRef.current;

    if (!image) {
      return;
    }

    this._scroller.setDimensions(
      container.clientWidth,
      container.clientHeight,
      image.offsetWidth * 1.01,
      image.offsetHeight * 1.01
    );
  }, 50);

  private _onScrollPanEnd = _.debounce(function _onScrollPanEnd(
    this: CanvasImageState,
    e: WheelEvent
  ) {
    this.isScrollPanning = false;
    this.canvasState.isPanning = false;
  },
  150);

  resetZoom(e?: React.MouseEvent<HTMLElement>) {
    if (e) {
      e.preventDefault();
      e.stopPropagation();
    }
    if (!this._scroller) return false;
    this._scroller.scrollTo(0, 0, true, 1);
  }

  startAutoScroll(speed?: number) {
    if (speed === undefined) {
      speed = this._lastAutoScrollSpeed;
    }

    if (!speed) {
      return;
    }

    this.stopAutoScroll();
    this.canvasState.stopAutoNavigate();

    this.isAutoScrolling = true;

    const startAutoNavigate = _.debounce(() => {
      this.canvasState.startAutoNavigate(
        this.canvasState._lastAutoNavigateInterval,
        this.canvasState._lastAutoNavigateCallback
      );
    }, 100);

    let start: number;
    let prevtime: number;

    function scroll(this: CanvasImageState, time: number) {
      if (!this.isAutoScrolling || !this.isFocused) {
        console.debug('not focused or not enabled, skipping autoscroll');
        return;
      }

      if (!this.canvasState.isTabActive) {
        console.debug('tab not active, retrying autoscroll');
        this._autoSCrollTimerId = setTimeout(boundScroll, 5000);
        return;
      }

      if (
        this.isScrollPanning ||
        this.canvasState.isPanning ||
        this.isPanning
      ) {
        console.debug('panning, retrying autoscroll');
        this._autoSCrollTimerId = setTimeout(this.startAutoScroll, 3500);
        return;
      }

      if (!this.imageHeight || !this.imageWidth) {
        console.debug('no image height or width, retrying autoscroll');
        this._autoSCrollTimerId = setTimeout(boundScroll, 500);
        return;
      }

      if (start === undefined) {
        start = time;
      }

      const elapsed = time - start;
      let maxScroll = 0;
      let currentScroll = 0;
      let scrollDir: 'top' | 'left' = 'top';

      // scroll in the longest direction
      if (this.imageHeight > this.imageWidth) {
        maxScroll = this._scroller.getScrollMax().top;
        currentScroll = this._scroller.getValues().top;
        scrollDir = 'top';
      } else {
        maxScroll = this._scroller.getScrollMax().left;
        currentScroll = this._scroller.getValues().left;
        scrollDir = 'left';
      }

      // TODO: improve this by easing the speed

      if (prevtime !== time) {
        const nextScroll = speed / 60;
        this._scroller.scrollBy(
          scrollDir === 'left' ? nextScroll : 0,
          scrollDir === 'top' ? nextScroll : 0,
          true
        );
      }

      // if we're at the end, stop scrolling
      //  minus 1 to account for rounding errors
      if (currentScroll >= maxScroll - 1) {
        console.debug('end reached, skipping autoscroll');
        if (
          this.autoNavigateEnabled &&
          this.canvasState._lastAutoNavigateInterval
        ) {
          startAutoNavigate();
        }
        return;
      }

      prevtime = time;
      this._autoSCrollFrameId = requestAnimationFrame(boundScroll);
    }

    const boundScroll = scroll.bind(this);

    this._autoSCrollTimerId = setTimeout(() => {
      this._autoSCrollFrameId = requestAnimationFrame(boundScroll);
    }, 8000);
  }

  stopAutoScroll() {
    if (this._autoSCrollTimerId) {
      clearTimeout(this._autoSCrollTimerId);
      this._autoSCrollTimerId = undefined;
    }

    if (this._autoSCrollFrameId) {
      cancelAnimationFrame(this._autoSCrollFrameId);
      this._autoSCrollFrameId = undefined;
    }

    if (this.isAutoScrolling) {
      this.canvasState.stopAutoNavigate();
    }

    this.isAutoScrolling = false;
  }

  dispose() {
    this.stopAutoScroll();
    this._disposers.forEach((d) => d());
  }
}

const CanvasImage = observer(function CanvasImage({
  href,
  autoNavigate,
  autoScroll,
  autoScrollSpeed,
  state: canvasState,
  onError,
  onEndReached,
  onStartReached,
  focused,
  ...props
}: {
  href: string;
  state: CanvasState;
  autoNavigate?: boolean;
  autoScroll?: boolean;
  autoScrollSpeed?: number;
  onError?: (e: React.SyntheticEvent<HTMLImageElement>) => void;
  onEndReached?: () => void;
  onStartReached?: () => void;
  focused?: boolean;
}) {
  const state = useMemo(() => {
    return new CanvasImageState(canvasState);
  }, [canvasState]);

  useUnmount(() => {
    state.dispose();
  });

  useEffectAction(() => {
    if (autoScroll && focused) {
      state.startAutoScroll(autoScrollSpeed ?? 50);
    } else {
      state.stopAutoScroll();
    }
  }, [autoScroll, focused, autoScrollSpeed, state]);

  useEffectAction(() => {
    state.autoNavigateEnabled = autoNavigate;
  }, [autoNavigate]);

  useEffectAction(() => {
    state.setHref(href);
  }, [href]);

  useEffectAction(() => {
    state.setFocused(focused);
  }, [focused, state]);

  useEffectAction(() => {
    setTimeout(() => {
      state.adjust();
    }, 350);
  }, [canvasState.isFullscreen]);

  useEffectAction(() => {
    state.onEndReachedCallback = onEndReached;
  }, [onEndReached, state]);

  useEffectAction(() => {
    state.onStartReachedCallback = onStartReached;
  }, [onStartReached, state]);

  useBodyEvent('mousemove', (e) => state.onMouseMove(e), {}, [state]);

  useBodyEvent('mouseup', (e) => state.onMouseUp(e), {}, [state]);

  useRefEvent(
    state.containerRef,
    'wheel',
    (e) => state.onWheel(e),
    { passive: true },
    [state]
  );

  useRefEvent(
    state.containerRef,
    'touchstart',
    (e) => state.onTouchStart(e),
    {
      passive: true,
    },
    [state]
  );

  useRefEvent(
    state.containerRef,
    'touchmove',
    (e) => state.onTouchMove(e),
    {
      passive: true,
    },
    [state]
  );

  useRefEvent(
    state.containerRef,
    'touchend',
    (e) => state.onTouchEnd(e),
    {
      passive: true,
    },
    [state]
  );

  useTrackDimensions(
    _.debounce(
      _.throttle((entry) => {
        state.adjust();
      }, 500),
      250
    ),
    state.containerRef,
    [state]
  );

  return (
    <div
      {...props}
      ref={state.containerRef}
      draggable="false"
      onDragStart={() => false}
      className="reader-item user-select-none"
    >
      {focused && (
        <div className="actions text-center">
          {state.imageZoom !== 1 && (
            <Button
              onClick={(e) => state.resetZoom(e)}
              size="huge"
              icon="zoom"
              className="translucent-black"
            >
              <Icon name="close" />
              {t`Reset zoom`}
            </Button>
          )}
        </div>
      )}
      <img
        alt="page"
        onError={onError}
        draggable="false"
        onLoad={useCallback(() => state.update(), [state])}
        ref={state.imageRef}
        onDragStart={(e) => {
          e.preventDefault();
          e.stopPropagation();
          return false;
        }}
        onMouseDownCapture={useCallback(
          (e) => {
            state.onMouseDown(e.nativeEvent);
          },
          [state]
        )}
        src={href}
        className={classNames('', {
          'fit-width': state.imageFit === ItemFit.Width,
          'fit-height': state.imageFit === ItemFit.Height,
          stretch: canvasState.stretchFit,
        })}
      />
    </div>
  );
});

export default CanvasImage;
