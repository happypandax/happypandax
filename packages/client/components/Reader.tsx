import { useEffect, useMemo, useRef, useState } from 'react';
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

import Scroller from '@cycjimmy/scroller';
import { useEvent, useMount } from 'react-use';
import classNames from 'classnames';

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

// patches Scroller.zoomTo
function scrollerZoomTo(level, animate, originLeft, originTop, callback) {
  if (!this.options.zooming) {
    return;
  }

  // Add callback if exists
  if (callback) {
    this.__zoomComplete = callback;
  }

  // Stop deceleration
  if (this.__isDecelerating) {
    this.animate.stop(this.__isDecelerating);
    this.__isDecelerating = false;
  }

  const oldLevel = this.__zoomLevel;

  // Limit level according to configuration
  level = Math.max(Math.min(level, this.options.maxZoom), this.options.minZoom);

  // Normalize input origin to center of viewport if not defined
  if (originLeft == null) {
    originLeft = this.__clientWidth / 2;
  }

  if (originTop == null) {
    originTop = this.__clientHeight / 2;
  }

  // Recompute maximum values while temporary tweaking maximum scroll ranges
  this.__maxScrollLeft = this.__contentWidth * level - this.__clientWidth / 2;
  this.__maxScrollTop = this.__contentHeight * level - this.__clientHeight / 2;

  // Recompute left and top coordinates based on new zoom level
  let left = ((originLeft + this.__scrollLeft) * level) / oldLevel - originLeft;
  let top = ((originTop + this.__scrollTop) * level) / oldLevel - originTop;

  // Limit x-axis
  if (left > this.__maxScrollLeft) {
    left = this.__maxScrollLeft;
  } else if (left < 0 && level < 1) {
    // if zomming out, center content
    left = Math.min(left * level, 0);
  }

  // Limit y-axis
  if (top > this.__maxScrollTop) {
    top = this.__maxScrollTop;
  }

  // Push values out
  this.__publish(left, top, level, animate);
}

function CanvasImage({ href }: { href: string; number: number }) {
  const preload = useRef(new Image());
  preload.current.src = href;

  const ref = useRef<HTMLDivElement>();
  const refContent = useRef<HTMLImageElement>();

  const [scroller, setScroller] = useState<Scroller>();

  useEffect(() => {
    const s = new Scroller(scrollRender.bind(undefined, refContent.current), {
      scrollingX: false,
      scrollingy: false,
      zooming: true,
      animating: true,
      animationDuration: 250,
    });

    s.zoomTo = scrollerZoomTo.bind(s);

    ref.current.addEventListener('wheel', function (e) {
      const { zoom } = s.getValues();
      e.detail;
      const change = e.deltaY > 0 ? 0.8 : 1.33;

      const zoomingOut = e.deltaY > 0 ? true : false;

      let zoomLeft = e.clientX - ref.current.clientWidth / 2;
      let zoomTop = e.clientY - ref.current.clientHeight / 2;

      if (zoomingOut) {
        zoomTop = -ref.current.clientHeight;
      }

      s.zoomTo(zoom * change, true, zoomLeft, zoomTop);
      e.preventDefault();
      e.stopPropagation();
    });

    setScroller(s);
  }, []);

  useEffect(() => {
    if (!scroller) return;

    const rect = ref.current.getBoundingClientRect();
    const container = ref.current;
    const content = refContent.current;

    console.log(rect);
    console.log([container.clientLeft, container.clientTop]);

    scroller.setDimensions(
      container.clientWidth,
      container.clientHeight,
      content.offsetWidth,
      content.offsetHeight
    );
  }, [scroller]);

  return (
    <div
      ref={ref}
      draggable="false"
      onDragStart={() => false}
      className="reader-item user-select-none ">
      <img
        draggable="false"
        ref={refContent}
        onDragStart={() => false}
        src={href}
        className="user-select-none"
      />
    </div>
  );
}

function Canvas({
  children,
  focusPage,
}: {
  children?: any;
  focusPage: number;
}) {
  const ref = useRef<HTMLDivElement>();
  const refMouseDown = useRef(false);
  const refContent = useRef<HTMLDivElement>();

  const [scroller, setScroller] = useState<Scroller>();

  useEffect(() => {
    const s = new Scroller(scrollRender.bind(undefined, refContent.current), {
      scrollingX: false,
      scrollingy: true,
      paging: true,
      animating: true,
      animationDuration: 10,
    });

    s.zoomTo = scrollerZoomTo.bind(s);

    ref.current.addEventListener('mousedown', function (e) {
      s.doTouchStart(
        [
          {
            pageX: e.pageX,
            pageY: e.pageY,
          },
        ],
        e.timeStamp
      );

      refMouseDown.current = true;
    });

    refContent.current.addEventListener('wheel', function (e) {
      s.doMouseZoom(e.deltaY, e.timeStamp, e.pageX, e.pageY);
      e.preventDefault();
      e.stopPropagation();
    });

    setScroller(s);
  }, []);

  useEvent('mousemove', (e) => {
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
  });

  useEvent('mouseup', (e) => {
    if (!refMouseDown.current) {
      return;
    }

    scroller.doTouchEnd(e.timeStamp);
  });

  useEffect(() => {
    if (!scroller) return;

    if (window.ontouchstart) {
      ref.current.addEventListener('touchstart', function (e) {
        scroller.doTouchStart(e.touches, e.timeStamp);
        e.preventDefault();
      });

      document.addEventListener('touchmove', function (e) {
        scroller.doTouchMove(e.touches, e.timeStamp);
      });

      document.addEventListener('touchend', function (e) {
        scroller.doTouchEnd(e.timeStamp);
      });
    }
  }, [scroller]);

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
  }, [children, scroller]);

  useEffect(() => {}, []);

  return (
    <div ref={ref} className="reader-container user-select-none">
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
  const [pages, setPages] = useState([]);

  useEffect(() => {
    const windowed = windowedPages(pageNumber, 4, 15);
    setPages(
      windowed.map((p) => {
        const d = {
          number: p,
          url:
            'https://jhxnekt.ofkqjcvmzmnk.hath.network/h/b08842ef5480f5c4fe4f603bfba172ed8bb7f3d3-257916-1280-1808-jpg/keystamp=1620249900-61bce7e5e8;fileindex=75795344;xres=1280/001.jpg',
        };
        return d;
      })
    );
  }, [pageNumber]);

  return (
    <Segment inverted>
      <Canvas focusPage={pageNumber}>
        {pages.map((p) => (
          <CanvasImage key={p.number} href={p.url} number={p.number} />
        ))}
      </Canvas>
    </Segment>
  );
}
