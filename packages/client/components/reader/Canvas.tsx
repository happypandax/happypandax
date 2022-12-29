import classNames from 'classnames';
import _ from 'lodash';
import { makeAutoObservable, reaction } from 'mobx';
import { observer } from 'mobx-react-lite';
import React, { RefObject, useCallback, useEffect } from 'react';
import { useFullscreen } from 'react-use';
import { useSetRecoilState } from 'recoil';

import Scroller from '@twiddly/scroller';

import {
  useBodyEvent,
  useRefEvent,
  useTabActive,
} from '../../client/hooks/utils';
import t from '../../client/lang';
import { ItemFit, ReadingDirection } from '../../shared/enums';
import { ReaderState } from '../../state';
import { scrollRender } from './CanvasImage';

export class CanvasState {
    fit: ItemFit = ItemFit.Auto;
    wheelZoom = false;
    stretchFit = false;
    direction: ReadingDirection = ReadingDirection.TopToBottom;

    isPanning = false;
    isFullscreen = false;
    isTabActive = true;

    focusChild = 0;

    containerRef: RefObject<HTMLDivElement>;
    contentRef: RefObject<HTMLDivElement>;


    onEndCallback: (() => any) | undefined = undefined;
    onFocusChildCallback: ((child: number) => any) | undefined = undefined;

    children: React.ReactNode[] = [];

    private _scroller: Scroller;

    private _scrollPanX = 0;
    private _scrollPanY = 0;

    private _mouseDownEvent: MouseEvent | null = null;

    private _autoNavigateTimerId: any = undefined;

    private _disposers: (() => void)[] = [];



    constructor() {

        this.containerRef = React.createRef();
        this.contentRef = React.createRef();

        document.body.focus();
        this._scroller = new Scroller((left: number, top: number, zoom: number) => scrollRender(this.contentRef.current, left, top, zoom), {
            scrollingX: false,
            scrollingy: true,
            paging: true,
            animating: true,
            animationDuration: 250,
            speedMultiplier: 1.15,
            penetrationDeceleration: 0.1,
            penetrationAcceleration: 0.12,
            scrollingComplete: () => this.onScrollCompleted(),
        });

        this._disposers = [];
        this._disposers.push(
            reaction(
                () => this.focusChild,
                (fit) => {
                    this.adjustFocus();
                }
            )
        );

        makeAutoObservable(this);
    }

    get currentChild() {
        let child = 0;
        if (!this._scroller) return child;
        switch (this.direction) {
            case ReadingDirection.TopToBottom: {
                child = Math.abs(this._scroller.getValues().top) / this.containerRef.current.clientHeight;
                break;
            }
        }
        return Math.floor(child);
    }

    get nextChild() {
        switch (this.direction) {
            case ReadingDirection.LeftToRight:
            case ReadingDirection.TopToBottom:
                return this.focusChild + 1;
        }
    }

    scrollToChild(childNumber: number, animate = true) {
        const { left, top } = this._scroller.getValues();

        const container = this.containerRef.current;

        switch (this.direction) {
            case ReadingDirection.TopToBottom:
                this._scroller.scrollTo(
                    left,
                    childNumber * container.clientHeight,
                    animate
                );
                break;
            case ReadingDirection.LeftToRight:
                this._scroller.scrollTo(
                    childNumber * container.clientWidth,
                    top,
                    animate
                );
                break;
        }

        if (this.children.length === childNumber) {
            this.onEndReached();
        }
    }

    onScrollCompleted() {
        if (!this._scroller) return;
        // resets scroll to current child
        const child = this.currentChild;
        if (!isNaN(child)) {
            this.onFocusChildCallback?.(child);
        }
    }

    onEndReached() {
        this.onEndCallback?.();
        this.isFullscreen = false;
    }

    checkIfEnd() {
        const { top } = this._scroller.getValues();
        // check if item has reached the end (this will always only check the boundary in y-axis since we're assuming height > width for manga)
        // can be improved to take into account reading direction, item fit and aspect ratio

        if (this.currentChild === this.children.length - 1) {
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


    updateChildren(children: React.ReactNode) {
        this.children = React.Children.toArray(children);
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


    // Makes sure focused child is in viewport
    adjustFocus() {
        if (!this._scroller) return;
        if (this.currentChild === this.focusChild) return;

        const childNumber = Math.max(
            0,
            Math.min(this.focusChild, this.children.length - 1)
        );

        this.scrollToChild(childNumber, false);
    }

    adjust() {
        if (!this._scroller) return;

        const container = this.containerRef.current;
        const content = this.contentRef.current;

        const rect = container.getBoundingClientRect();
        this._scroller.setPosition(
            rect.left + container.clientLeft,
            rect.top + container.clientTop
        );
        this._scroller.setDimensions(
            container.clientWidth,
            container.clientHeight,
            content.offsetWidth,
            content.offsetHeight
        );
    }

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

    private _onScrollPanEnd =
        _.debounce(function onScrollPanEnd(this: CanvasState) {
            this.isPanning = false;
        }, 150)

    onWheel(e: WheelEvent) {
        // scrolls with wheel when zoom is disabled

        if (e.defaultPrevented || this.wheelZoom) {
            return;
        }

        const container = this.containerRef.current;
        const content = this.contentRef.current;

        e.preventDefault();
        e.stopPropagation();

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
                    Math.min(
                        this._scrollPanX + deltaX,
                        content.offsetWidth * (1 - force)
                    )
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
        if (
            this.isTabActive &&
            this.focusChild < this.children.length - 1
        ) {
            this.stopAutoNavigate();
            let c = interval;
            const t = setInterval(() => {
                if (this.isPanning) return;
                c--;
                counterCallback?.(c);
                if (!c) {
                    this.scrollToChild(this.nextChild, true);
                    c = interval;
                }
            }, 1000);

            return () => clearInterval(t);
        }
    }

    stopAutoNavigate() {
        if (this._autoNavigateTimerId) {
            clearInterval(this._autoNavigateTimerId);
            this._autoNavigateTimerId = undefined;
        }
    }

    onDoubleClick(e: MouseEvent) {
        if (e.defaultPrevented) {
            return;
        }

        this.isFullscreen = !this.isFullscreen;
    }

    onClick(e: MouseEvent) {
        const container = this.containerRef.current;

        // ref.current.focus();
        // distinguish drag from click
        const delta = 5; // allow a small drag
        const diffX = Math.abs(e.pageX - this._mouseDownEvent.pageX);
        const diffY = Math.abs(e.pageY - this._mouseDownEvent.pageY);

        console.debug('diffX', diffX, 'diffY', diffY, 'delta', delta, diffX < delta && diffY < delta)

        if (diffX < delta && diffY < delta) {
            const childNumber = Math.max(
                0,
                Math.min(this.focusChild, this.children.length - 1)
            );

            const deadSpaceX = container.clientWidth * 0.1;
            const deadSpaceY = container.clientHeight * 0.1;
            let nextChildNumber = null as number;

            switch (this.direction) {
                case ReadingDirection.TopToBottom: {
                    if (e.pageY > container.clientHeight / 2 + deadSpaceY) {
                        nextChildNumber = childNumber + 1;
                    } else if (
                        e.pageY <
                        container.clientHeight / 2 - deadSpaceY
                    ) {
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
        this._disposers.forEach((d) => d());
        this.stopAutoNavigate();
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
    onEnd,
    stateKey,
}: {
    children?: any;
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
    onEnd?: () => void;
}) {

    const tabActive = useTabActive();
    const isFullscreen = useFullscreen(state.containerRef, state.isFullscreen, {
        onClose: () => { state.isFullscreen = false; },
    });

    const setAutoNavigateCounter = useSetRecoilState(
        ReaderState.autoNavigateCounter(stateKey)
    );

    useEffect(() => {
        state.updateChildren(children);
    }, [children, state]);

    useEffect(() => {
        state.focusChild = focusChild;
    }, [focusChild, state]);

    useEffect(() => {
        state.direction = direction;
    }, [direction, state]);

    useEffect(() => {
        state.wheelZoom = wheelZoom;
    }, [wheelZoom, state]);

    useEffect(() => {
        state.fit = fit;
    }, [fit, state]);

    useEffect(() => {
        state.stretchFit = stretchFit;
    }, [stretchFit, state]);

    useEffect(() => {
        state.isTabActive = tabActive;
    }, [tabActive, state]);

    useEffect(() => {
        state.onFocusChildCallback = onFocusChild;
    }, [onFocusChild, state]);

    useEffect(() => {
        state.onEndCallback = onEnd;
    }, [onEnd, state]);

    useBodyEvent(
        'mousemove',
        e => state.onMouseMove(e),
        {},
        [state]
    );

    useBodyEvent(
        'mouseup',
        e => state.onMouseUp(e),
        {},
        [state]
    );

    useRefEvent(
        state.containerRef,
        'touchstart',
        e => state.onTouchStart(e),
        { passive: true },
        [state],
        () => !!window.ontouchstart
    );

    useBodyEvent(
        'touchmove',
        e => state.onTouchMove(e),
        {},
        [state],
        () => !!window.ontouchstart
    );

    useBodyEvent(
        'touchend',
        e => state.onTouchEnd(e),
        {},
        [state],
        () => !!window.ontouchstart
    );

    // auto navigate
    useEffect(() => {
        if (autoNavigate) {
            state.startAutoNavigate(autoNavigateInterval, setAutoNavigateCounter);
        } else {
            state.stopAutoNavigate();
        }
    }, [autoNavigate, autoNavigateInterval, setAutoNavigateCounter, state]);



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
