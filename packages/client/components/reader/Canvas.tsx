import classNames from 'classnames';
import _ from 'lodash';
import { makeAutoObservable, reaction } from 'mobx';
import { observer } from 'mobx-react-lite';
import React, { RefObject, useCallback, useEffect } from 'react';
import { useFullscreen, useUnmount } from 'react-use';

import Scroller from '@twiddly/scroller';

import { useBreakpoints } from '../../client/hooks/ui';
import {
  useBodyEvent,
  useEffectAction,
  useRefEvent,
  useTabActive,
  useTrackDimensions,
  useUpdateEffectAction,
} from '../../client/hooks/utils';
import { ItemFit, ReadingDirection } from '../../shared/enums';
import { roundToNearest } from '../../shared/utility';
import { scrollRender } from './CanvasImage';

export class CanvasState {
  initialized = false;

  fit: ItemFit = ItemFit.Auto;
  wheelZoom = false;
  stretchFit = false;
  direction: ReadingDirection = ReadingDirection.TopToBottom;

  isPanning = false;
  isFullscreen = false;
  isTabActive = true;
  isMobile = false;
  isTablet = false;

  isAutoNavigating = false;

  focusChild: number;

  containerRef: RefObject<HTMLDivElement>;
  contentRef: RefObject<HTMLDivElement>;

  onEndReachedCallback: (() => any) | undefined = undefined;
  onFocusChildCallback: ((child: number) => any) | undefined = undefined;

  window: any[] = [];

  // semi private, used by canvas image
  _lastAutoNavigateInterval: number | undefined = undefined;
  _lastAutoNavigateCallback: (c: number) => void | undefined = undefined;

  private _scroller: Scroller;

  private _scrollPanX = 0;
  private _scrollPanY = 0;

  private _mouseDownEvent: MouseEvent | null = null;

  private _autoNavigateTimerId: any = undefined;

  private _disposers: (() => void)[] = [];

  constructor(focusChild = 0) {
    this.focusChild = focusChild;

    this.containerRef = React.createRef();
    this.contentRef = React.createRef();

    document.body.focus();
    this._scroller = new Scroller(
      (left: number, top: number, zoom: number) =>
        scrollRender(this.contentRef.current, left, top, zoom),
      {
        scrollingX: false,
        scrollingy: true,
        paging: true,
        animating: true,
        animationDuration: 250,
        speedMultiplier: 1.15,
        penetrationDeceleration: 0.1,
        penetrationAcceleration: 0.12,
        scrollingComplete: () => this.onScrollCompleted(),
      }
    );

    this._disposers = [];
    this._disposers.push(
      reaction(
        () => this.isFullscreen,
        (fit) => {
          this.adjust();
        }
      )
    );

    makeAutoObservable(this);
  }

  get currentChild() {
    let child = this.focusChild;
    if (!this._scroller) return child;

    if (!this.containerRef?.current?.clientHeight) return child;

    switch (this.direction) {
      case ReadingDirection.TopToBottom: {
        child =
          Math.abs(this._scroller.getValues().top) /
          this.containerRef.current.clientHeight;
        break;
      }
    }

    if (isNaN(child)) {
      child = 0;
    }

    // console.debug("current child", child, this._scroller.getValues(), this.containerRef.current.clientHeight)

    return roundToNearest(child);
  }

  get nextChild() {
    switch (this.direction) {
      case ReadingDirection.LeftToRight:
      case ReadingDirection.TopToBottom:
        return this.currentChild + 1;
    }
  }

  get previousChild() {
    switch (this.direction) {
      case ReadingDirection.LeftToRight:
      case ReadingDirection.TopToBottom:
        return this.currentChild - 1;
    }
  }

  private _scrollTo(child: number, animate = true) {
    if (!this._scroller) return;
    if (!this.containerRef?.current) return;

    const { left, top } = this._scroller.getValues();

    const container = this.containerRef.current;

    console.debug(
      '_scroll to',
      child,
      this._scroller.getValues(),
      child * container.clientHeight,
      this._scroller.getDimensions()
    );

    switch (this.direction) {
      case ReadingDirection.TopToBottom:
        this._scroller.scrollTo(left, child * container.clientHeight, animate);
        break;
      case ReadingDirection.LeftToRight:
        this._scroller.scrollTo(child * container.clientWidth, top, animate);
        break;
    }
  }

  scrollToChild(childNumber: number, animate = true) {
    const child = Math.max(0, Math.min(childNumber, this.window.length - 1));

    if (this.window.length === childNumber) {
      this.onEndReached();
    }

    if (child === this.currentChild) return;

    console.debug(
      'scrolling to child',
      child,
      'current child',
      this.currentChild,
      'animate',
      animate
    );

    if (this.isAutoNavigating) {
      this.startAutoNavigate(
        this._lastAutoNavigateInterval,
        this._lastAutoNavigateCallback
      );
    }

    this._scrollTo(child, animate);
  }

  onScrollCompleted = _.debounce(function onScrollCompleted() {
    if (!this._scroller) return;
    // resets scroll to current child
    const child = this.currentChild;

    console.debug('onScrollCompleted', this._scroller.getValues(), child);

    if (!isNaN(child)) {
      this.onFocusChildCallback?.(child);
    }
  }, 100);

  onEndReached() {
    this.onEndReachedCallback?.();
    this.isFullscreen = false;
  }

  checkIfEnd() {
    const { top } = this._scroller.getValues();
    // check if item has reached the end (this will always only check the boundary in y-axis since we're assuming height > width for manga)
    // can be improved to take into account reading direction, item fit and aspect ratio

    if (this.currentChild === this.window.length - 1) {
      // if last page
      const { top: scrollMaxTop } = this._scroller.getScrollMax();
      switch (this.direction) {
        case ReadingDirection.LeftToRight:
        case ReadingDirection.TopToBottom: {
          if (this._scrollPanY >= scrollMaxTop) {
            this.onEndReached();
          }
          break;
        }
      }
    }
  }

  updateWindow(children: any[]) {
    if (children.length === this.window.length) {
      return;
    }

    console.debug('updating window', children.length);

    this.window = [...children];
    this.adjust();
    this.adjustFocus();
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

  onMouseUp = (e: MouseEvent) => {
    if (!this.isPanning) {
      return;
    }

    this._scroller.doTouchEnd(e.timeStamp);
    this.isPanning = false;
  };

  onTouchStart(e: TouchEvent) {
    if (e.touches.length !== 1) {
      return;
    }

    this._scroller.doTouchStart(e.touches, e.timeStamp);
    e.preventDefault();
  }

  onTouchMove(e: TouchEvent) {
    if (e.touches.length !== 1) {
      return;
    }

    this._scroller.doTouchMove(e.touches, e.timeStamp);
  }

  onTouchEnd(e: TouchEvent) {
    if (e.touches.length !== 1) {
      return;
    }

    this._scroller.doTouchEnd(e.timeStamp);
  }

  initializeValues() {
    const { position, dimensions } = this.adjustments;

    console.debug(
      'initializing values',
      position,
      dimensions,
      this.currentChild,
      this._scroller.getValues()
    );

    this._scroller.setDimensions(
      dimensions.width,
      dimensions.height,
      dimensions.contentWidth,
      dimensions.contentHeight
    );
    this._scroller.setPosition(position.left, position.top);

    const childNumber = Math.max(
      0,
      Math.min(this.focusChild, this.window.length - 1)
    );

    console.debug(
      'initializing values',
      childNumber,
      this.focusChild,
      this.window.length,
      position,
      dimensions,
      this._scroller.getValues()
    );

    this._scrollTo(childNumber, false);

    this.initialized = true;
  }

  // Makes sure focused child is in viewport
  adjustFocus = _.debounce(function adjustFocus(this: CanvasState) {
    if (!this._scroller) return;
    if (this.currentChild === this.focusChild) return;
    console.debug('adjustFocus', this.focusChild, this.currentChild);

    this._scrollTo(this.focusChild, false);
  }, 105);

  needsAdjust() {
    if (!this._scroller) return false;

    const { dimensions } = this.adjustments;

    const {
      width,
      height,
      contentWidth,
      contentHeight,
    } = this._scroller.getDimensions();

    return (
      width !== dimensions.width ||
      height !== dimensions.height ||
      contentWidth !== dimensions.contentWidth ||
      contentHeight !== dimensions.contentHeight
    );
  }

  get adjustments() {
    const container = this.containerRef.current;
    const content = this.contentRef.current;

    const rect = container.getBoundingClientRect();

    const position = {
      left: rect.left + container.clientLeft,
      top: rect.top + container.clientTop,
    };

    const dimensions = {
      width: container.clientWidth,
      height: container.clientHeight,
      contentWidth: content.offsetWidth,
      contentHeight: content.offsetHeight,
    };

    return { position, dimensions };
  }

  adjust = _.debounce(function adjust(this: CanvasState) {
    if (!this._scroller) return;

    const { position, dimensions } = this.adjustments;

    this._scroller.setDimensions(
      dimensions.width,
      dimensions.height,
      dimensions.contentWidth,
      dimensions.contentHeight
    );

    const { left, top } = this._scroller.getValues();
    if (isNaN(left) || isNaN(top)) {
      this._scrollTo(this.currentChild, false);
    }

    console.debug(
      'adjust dimensions',
      'position',
      position,
      'dimensions',
      dimensions
    );
    console.debug(
      'scroller dimensions',
      this._scroller.getValues(),
      this._scroller.getDimensions()
    );
  }, 100);

  // private _onCanvasKeyDown = (e: KeyboardEvent) => {
  //     if (e.ctrlKey) {
  //         if (e.key === '0') {
  //             this._scroller.zoomTo(1);
  //         } else if (e.key === '+') {
  //             this._scroller.zoomBy(1 + this._zoomStep);
  //         }

  //         if (e.key === '-') {
  //             this._scroller.zoomBy(1 - this._zoomStep);
  //         }

  //         if (e.key === 'ArrowUp') {
  //             this._scroller.scrollBy(0, -10);
  //         }

  //         if (e.key === 'ArrowDown') {
  //             this._scroller.scrollBy(0, 10);
  //         }

  //         if (e.key === 'ArrowLeft') {
  //             this._scroller.scrollBy(-10, 0);
  //         }

  //         if (e.key === 'ArrowRight') {
  //             this._scroller.scrollBy(10, 0);
  //         }

  //         if (e.key === 'PageUp') {
  //             this._scroller.scrollBy(0, -this._canvasHeight);
  //         }

  //         if (e.key === 'PageDown') {
  //             this._scroller.scrollBy(0, this._canvasHeight);
  //         }

  //         if (e.key === 'Home') {
  //             this._scroller.scrollTo(0, 0);
  //         }

  //         if (e.key === 'End') {
  //             this._scroller.scrollTo(0, this._scroller.scrollHeight);
  //         }

  //         if (e.key === 'Enter') {
  //             this._scroller.scrollTo(0, 0);
  //         }
  //     }
  // };

  private _onScrollPanEnd = _.debounce(function onScrollPanEnd(
    this: CanvasState
  ) {
    this.isPanning = false;
  },
  150);

  onWheel(e: WheelEvent) {
    if (e.defaultPrevented) {
      return;
    }

    e.preventDefault();
    e.stopPropagation();
    e.stopImmediatePropagation();

    if (this.wheelZoom) {
      return;
    }

    return;

    // scrolls with wheel when zoom is disabled

    const container = this.containerRef.current;
    const content = this.contentRef.current;

    if (!this.isPanning) {
      const { left, top } = this._scroller.getValues();
      this.isPanning = true;
      this._scrollPanX = left;
      this._scrollPanY = top;
    }

    const force = 0.33;

    const deltaX =
      e.deltaY > 0
        ? container.clientWidth * force
        : -container.clientWidth * force;

    const deltaY =
      e.deltaY > 0
        ? container.clientHeight * force
        : -container.clientHeight * force;

    switch (this.direction) {
      case ReadingDirection.TopToBottom:
        this._scrollPanY = Math.max(
          container.clientHeight * force,
          Math.min(
            this._scrollPanY + deltaY,
            content.offsetHeight * (1 - force)
          )
        );
        break;
      case ReadingDirection.LeftToRight:
        this._scrollPanX = Math.max(
          container.clientWidth * force,
          Math.min(this._scrollPanX + deltaX, content.offsetWidth * (1 - force))
        );
        break;
    }

    this._scroller.scrollTo(this._scrollPanX, this._scrollPanY, true);

    const scrollingDown = e.deltaY > 0 ? true : false;
    if (scrollingDown) {
      // TODO: doesn't work
      this.checkIfEnd();
    }

    this._onScrollPanEnd();
  }

  startAutoNavigate(interval: number, counterCallback?: (c: number) => void) {
    this.stopAutoNavigate();

    this._lastAutoNavigateCallback = counterCallback;
    this._lastAutoNavigateInterval = interval;

    let c = interval;
    this.isAutoNavigating = true;
    this._autoNavigateTimerId = setInterval(() => {
      if (!this.isTabActive || !(this.currentChild < this.window.length - 1))
        return;

      if (this.isPanning || !this.isAutoNavigating) return;

      c--;
      counterCallback?.(c);
      if (!c) {
        this.scrollToChild(this.nextChild, true);
        c = interval;
      }
    }, 1000);
  }

  stopAutoNavigate() {
    if (this._autoNavigateTimerId) {
      clearInterval(this._autoNavigateTimerId);
      this._autoNavigateTimerId = undefined;
    }
    this.isAutoNavigating = false;
  }

  onDoubleClick(e: MouseEvent) {
    if (e.defaultPrevented) {
      return;
    }

    this.isFullscreen = !this.isFullscreen;
  }

  onClick(e: MouseEvent) {
    const container = this.containerRef.current;
    console.debug('onClick current child', this.currentChild);

    // ref.current.focus();
    // distinguish drag from click
    const delta = 5; // allow a small drag
    const diffX = Math.abs(e.pageX - (this._mouseDownEvent?.pageX ?? 0));
    const diffY = Math.abs(e.pageY - (this._mouseDownEvent?.pageY ?? 0));

    console.debug(
      'diffX',
      diffX,
      'diffY',
      diffY,
      'delta',
      delta,
      diffX < delta && diffY < delta
    );

    if (diffX < delta && diffY < delta) {
      const childNumber = this.currentChild;

      const deadFactor = this.isMobile ? 0.01 : 0.1;
      const deadSpaceX = container.clientWidth * deadFactor;
      const deadSpaceY = container.clientHeight * deadFactor;

      console.debug({
        deadSpaceX,
        deadSpaceY,
      });

      let nextChildNumber = null as number;

      switch (this.direction) {
        case ReadingDirection.TopToBottom: {
          if (e.pageY > container.clientHeight / 2 + deadSpaceY) {
            nextChildNumber = childNumber + 1;
          } else if (e.pageY < container.clientHeight / 2 - deadSpaceY) {
            nextChildNumber = childNumber - 1;
          }
          break;
        }
        case ReadingDirection.LeftToRight: {
          if (e.pageX > container.clientWidth / 2 + deadSpaceX) {
            nextChildNumber = childNumber + 1;
          } else if (e.pageX > container.clientWidth / 2 - deadSpaceX) {
            nextChildNumber = childNumber - 1;
          }
          break;
        }
      }

      if (nextChildNumber !== null) {
        this.scrollToChild(nextChildNumber, true);
      }
    }
  }

  onMouseDown(e: MouseEvent) {
    this._mouseDownEvent = e;
    console.debug('onMouseDown current child', this.currentChild);
    if (e.defaultPrevented) {
      return;
    }
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

  dispose() {
    this.stopAutoNavigate();
    this._disposers.forEach((d) => d());
  }
}

const Canvas = observer(function Canvas({
  children,
  direction = ReadingDirection.TopToBottom,
  focusChild = 0,
  autoNavigateInterval = 5,
  autoNavigate,
  wheelZoom,
  state,
  fit,
  stretchFit,
  label,
  onFocusChild,
  onEndReached,
  onAutoNavigateCounter,
  stateKey,
}: {
  children?: React.ReactNode;
  direction?: ReadingDirection;
  fit?: ItemFit;
  stretchFit?: boolean;
  label?: React.ReactNode;
  autoNavigateInterval?: number;
  focusChild?: number;
  wheelZoom?: boolean;
  stateKey?: string;
  state: CanvasState;
  autoNavigate?: boolean;
  onFocusChild?: (number) => void;
  onEndReached?: () => void;
  onAutoNavigateCounter?: (number) => void;
}) {
  const tabActive = useTabActive();
  const isFullscreen = useFullscreen(state.containerRef, state.isFullscreen, {
    onClose: () => {
      state.isFullscreen = false;
    },
  });

  useUnmount(() => {
    state.dispose();
  });

  useUpdateEffectAction(() => {
    state.updateWindow(React.Children.toArray(children));
  }, [children, state]);

  useEffectAction(() => {
    state.focusChild = focusChild;
    state.adjustFocus();
  }, [focusChild, state]);

  useEffectAction(() => {
    state.direction = direction;
  }, [direction, state]);

  useEffectAction(() => {
    state.wheelZoom = wheelZoom;
  }, [wheelZoom, state]);

  useEffectAction(() => {
    state.fit = fit;
  }, [fit, state]);

  useEffectAction(() => {
    state.stretchFit = stretchFit;
  }, [stretchFit, state]);

  useEffectAction(() => {
    state.isTabActive = tabActive;
  }, [tabActive, state]);

  useEffectAction(() => {
    state.onFocusChildCallback = onFocusChild;
  }, [onFocusChild, state]);

  useEffectAction(() => {
    state.onEndReachedCallback = onEndReached;
  }, [onEndReached, state]);

  const { isMobileMax, isTablet } = useBreakpoints();

  useEffectAction(() => {
    state.isMobile = isMobileMax;
    state.isTablet = isTablet;
  }, [isMobileMax, isTablet]);

  useRefEvent(
    state.containerRef,
    'wheel',
    (e) => state.onWheel(e),
    { passive: false },
    [state]
  );

  useBodyEvent('mousemove', (e) => state.onMouseMove(e), {}, [state]);

  useBodyEvent('mouseup', (e) => state.onMouseUp(e), {}, [state]);

  useRefEvent(
    state.containerRef,
    'touchstart',
    (e) => state.onTouchStart(e),
    { passive: true },
    [state],
    () => !!window.ontouchstart
  );

  useBodyEvent(
    'touchmove',
    (e) => state.onTouchMove(e),
    {},
    [state],
    () => !!window.ontouchstart
  );

  useBodyEvent(
    'touchend',
    (e) => state.onTouchEnd(e),
    {},
    [state],
    () => !!window.ontouchstart
  );

  // auto navigate
  useEffectAction(() => {
    if (autoNavigate) {
      state.startAutoNavigate(autoNavigateInterval, onAutoNavigateCounter);
    } else {
      state.stopAutoNavigate();
    }
  }, [autoNavigate, autoNavigateInterval, onAutoNavigateCounter]);

  // initialize values

  useEffect(() => {
    state.initializeValues();
  }, [state]);

  useTrackDimensions(
    _.debounce(
      _.throttle((entry) => {
        if (state.initialized && state.needsAdjust()) {
          state.adjust();
        }
      }, 500),
      250
    ),
    state.containerRef,
    [state]
  );

  return (
    <div
      ref={state.containerRef}
      className="reader-container"
      tabIndex={-1}
      onDoubleClick={useCallback(
        (e) => {
          state.onDoubleClick(e.nativeEvent);
        },
        [state]
      )}
      onClick={useCallback(
        (e) => {
          state.onClick(e.nativeEvent);
        },
        [state]
      )}
      onMouseDown={useCallback(
        (e) => {
          state.onMouseDown(e.nativeEvent);
        },
        [state]
      )}>
      <div className="top-content text-center">{!!label && label}</div>

      <div
        ref={state.contentRef}
        className={classNames(
          'user-select-none reader-content no-scrollbar',
          'column'
        )}>
        {children}
      </div>
    </div>
  );
});

export default Canvas;
