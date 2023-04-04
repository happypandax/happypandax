import classNames from 'classnames';
import _ from 'lodash';
import throttle from 'lodash/throttle';
import { useRouter } from 'next/router';
import React, {
  CSSProperties,
  useCallback,
  useEffect,
  useMemo,
  useRef,
  useState,
} from 'react';
import AutoSizer from 'react-virtualized-auto-sizer';
import { useRecoilValue } from 'recoil';
import {
  Grid,
  Header,
  Pagination,
  Segment,
  Sidebar,
  Visibility,
} from 'semantic-ui-react';

import { ArrayContext, ArrayContextT } from '../../client/context';
import { useBreakpoints } from '../../client/hooks/ui';
import t from '../../client/lang';
import { getClientHeight } from '../../client/utility';
import { AppState } from '../../state';
import { PlaceholderItemCard } from '../item/index';

const windowScrollPositionKey = {
  y: 'pageYOffset',
  x: 'pageXOffset',
};

const documentScrollPositionKey = {
  y: 'scrollTop',
  x: 'scrollLeft',
};

const elementScrollPositionKey = documentScrollPositionKey;

export function ElementScroller({
  children,
  throttleTime = 10,
  isGrid = false,
  horizontal = false,
  scrollElementRef = window,
}) {
  const ref = useRef<HTMLDivElement>();
  const outerRef = useRef<HTMLDivElement>();

  const getScrollPositionWindow = useCallback(
    (axis) =>
      window[windowScrollPositionKey[axis]] ||
      document.documentElement[documentScrollPositionKey[axis]] ||
      document.body[documentScrollPositionKey[axis]] ||
      0,
    []
  );

  const getScrollPositionElement = useCallback(
    (ref, axis) => ref[elementScrollPositionKey[axis]],
    []
  );

  const getScrollPosition = useCallback((ref, axis) => {
    if (ref === window) {
      return getScrollPositionWindow(axis);
    }
    return getScrollPositionElement(ref, axis);
  }, []);

  useEffect(() => {
    const handleWindowScroll = throttle(() => {
      const { top = 0, left = 0 } =
        outerRef.current?.getBoundingClientRect?.() || {};
      const { offsetTop = 0, offsetLeft = 0 } = outerRef.current || {};

      const y = getScrollPosition(scrollElementRef, 'y');
      const x = getScrollPosition(scrollElementRef, 'x');
      const scrollTop = y - offsetTop;
      const scrollLeft = x - offsetLeft;

      if (!horizontal && y - top < 0) return;
      if (horizontal && x - left < 0) return;

      if (isGrid)
        ref.current && ref.current.scrollTo({ scrollLeft, scrollTop });
      if (!isGrid) ref.current && ref.current.scrollTo(scrollTop);
    }, throttleTime);

    scrollElementRef.addEventListener('scroll', handleWindowScroll);
    return () => {
      handleWindowScroll.cancel();
      scrollElementRef.removeEventListener('scroll', handleWindowScroll);
    };
  }, [isGrid, scrollElementRef, throttleTime, horizontal]);

  const onScroll = useCallback(
    ({
      scrollLeft = 0, // This is not provided by react-window
      scrollTop = 0, // This is not provided by react-window
      scrollOffset,
      scrollUpdateWasRequested,
    }) => {
      if (!scrollUpdateWasRequested) return;
      const top = getScrollPosition(scrollElementRef, 'y');
      const left = getScrollPosition(scrollElementRef, 'x');
      const { offsetTop = 0, offsetLeft = 0 } = outerRef.current || {};

      scrollOffset += Math.min(top, offsetTop);
      scrollTop += Math.min(top, offsetTop);
      scrollLeft += Math.min(left, offsetLeft);

      if (!isGrid && scrollOffset !== top)
        scrollElementRef.scrollTo(0, scrollOffset);
      if (isGrid && (scrollTop !== top || scrollLeft !== left)) {
        scrollElementRef.scrollTo(scrollLeft, scrollTop);
      }
    },
    [isGrid, scrollElementRef]
  );

  const style = {
    width: isGrid ? 'auto' : horizontal ? '100%' : undefined,
    height: horizontal ? undefined : '100%',
    display: 'inline-block',
  };

  return children({
    ref,
    outerRef,
    height: scrollElementRef.innerHeight,
    width: scrollElementRef.innerWidth,
    style: _.omitBy(style, _.isNil),
    onScroll,
  });
}

export function ViewPagination({
  size = 'small',
  onPageChange,
  activePage,
  totalPages,
  hrefTemplate,
}: {
  onPageChange?: (ev, n: number) => void;
  size?: React.ComponentProps<typeof Pagination>['size'];
  activePage?: React.ComponentProps<typeof Pagination>['activePage'];
  totalPages?: React.ComponentProps<typeof Pagination>['totalPages'];
  hrefTemplate?: string;
}) {
  const { isMobileMax } = useBreakpoints();

  const router = useRouter();
  const tmpl = useMemo(() => {
    return _.template(hrefTemplate ?? '');
  }, [hrefTemplate]);

  return (
    <Pagination
      boundaryRange={isMobileMax ? 0 : 1}
      totalPages={totalPages ?? 1}
      activePage={activePage}
      pageItem={useCallback(
        (Item, props, test) => {
          const pageUrl = hrefTemplate
            ? tmpl({ page: props.value })
            : undefined;
          if (pageUrl) {
            router.prefetch(pageUrl);
          }

          return (
            <Item
              {...props}
              href={pageUrl}
              onClick={(ev) => {
                onPageChange?.(ev, props.value);
                if (pageUrl) {
                  ev.preventDefault();
                  router.push(pageUrl);
                }
              }}
            />
          );
        },
        [hrefTemplate, onPageChange]
      )}
      prevItem={useMemo(() => {
        if (!hrefTemplate) return undefined;

        const prevPage = Math.max(1, parseInt(activePage as string, 10) - 1);

        const href = tmpl({
          page: prevPage,
        });

        return {
          'aria-label': t`Previous item`,
          content: '⟨',
          href,
          onClick: (ev) => {
            onPageChange?.(ev, prevPage);
            if (href) {
              ev.preventDefault();
              router.push(href);
            }
          },
        };
      }, [hrefTemplate, activePage, onPageChange])}
      firstItem={useMemo(() => {
        if (!hrefTemplate) return undefined;

        const href = tmpl({
          page: 1,
        });

        return {
          'aria-label': t`First item`,
          content: '«',
          href,
          onClick: (ev) => {
            onPageChange?.(ev, 1);
            if (href) {
              ev.preventDefault();
              router.push(href);
            }
          },
        };
      }, [hrefTemplate, activePage, onPageChange])}
      nextItem={useMemo(() => {
        if (!hrefTemplate) return undefined;

        const nextPage = Math.min(
          parseInt(totalPages as string, 10),
          parseInt(activePage as string, 10) + 1
        );

        const href = tmpl({
          page: nextPage,
        });

        return {
          'aria-label': t`Next item`,
          content: '⟩',
          href,
          onClick: (ev) => {
            onPageChange?.(ev, nextPage);
            if (href) {
              ev.preventDefault();
              router.push(href);
            }
          },
        };
      }, [hrefTemplate, activePage, totalPages, onPageChange])}
      lastItem={useMemo(() => {
        if (!hrefTemplate) return undefined;

        const href = tmpl({
          page: parseInt(totalPages as string, 10),
        });

        return {
          'aria-label': t`Last item`,
          content: '»',
          href,
          onClick: (ev) => {
            onPageChange?.(ev, parseInt(totalPages as string, 10));
            if (href) {
              ev.preventDefault();
              router.push(href);
            }
          },
        };
      }, [hrefTemplate, activePage, totalPages, onPageChange])}
      pointing
      secondary
      size={size}
    />
  );
}

type ItemRender = React.ComponentType<{ data: any }>;

export interface ViewProps {
  ref?: any;
  outerRef?: any;
  height: number;
  width: number;
  itemRender: ItemRender;
  items?: any;
  onScroll?: any;
  style?: CSSProperties;
}

// TODO: Does not show anything when having a parent component and disableWindowScroll=true
export function ViewAutoSizer({
  disableWindowScroll,
  view: View,
  items,
  itemRender,
  ...viewProps
}: {
  disableWindowScroll?: boolean;
  itemRender: ItemRender;
  items?: any[];
  view: React.ElementType<ViewProps>;
} & Record<string, any>) {
  const sidebarWidth = useRecoilValue(AppState.sidebarWidth);
  const [disableWidth, setDisableWidth] = useState(false);
  const tid = useRef<NodeJS.Timeout>();

  useEffect(() => {
    const t = sidebarWidth === 'thin';
    if (tid.current) {
      clearTimeout(tid.current);
    }
    if (t) {
      setDisableWidth(true);
    } else {
      tid.current = setTimeout(() => setDisableWidth(false), 500);
    }
  }, [sidebarWidth]);

  const winFunc = useCallback(
    ({ width }) => {
      return (
        <ElementScroller>
          {({ ref, outerRef, style, height, onScroll }) => (
            <View
              ref={ref}
              outerRef={outerRef}
              style={style}
              items={items}
              itemRender={itemRender}
              height={height}
              width={width}
              onScroll={onScroll}
              {...viewProps}
            />
          )}
        </ElementScroller>
      );
    },
    [items, itemRender, ...Object.values(viewProps)]
  );

  const func = useCallback(
    ({ height, width }) => {
      return (
        <View
          items={items}
          itemRender={itemRender}
          height={height}
          width={width}
          {...viewProps}
        />
      );
    },
    [items, itemRender, ...Object.values(viewProps)]
  );

  const elFunc = !disableWindowScroll ? winFunc : func;
  return (
    <AutoSizer disableWidth={disableWidth} disableHeight={!disableWindowScroll}>
      {elFunc}
    </AutoSizer>
  );
}

// TODO: Consider switching infinite scrolling to https://github.com/bvaughn/react-window-infinite-loader

export function PaginatedView({
  children,
  pagination,
  paddedChildren,
  bottomPagination,
  itemsPerPage = 20,
  totalItemCount = 0,
  itemCount = 0,
  activePage = 1,
  onPageChange,
  paginationSize,
  fluid,
  loading,
  hrefTemplate,
  infinite,
  placeholderElement: Placeholder = PlaceholderItemCard,
  onLoadMore: loadMore,
  ...props
}: {
  children: React.ReactNode | React.ReactNode[];
  paddedChildren?: boolean;
  pagination?: boolean;
  paginationSize?: React.ComponentProps<typeof Pagination>['size'];
  fluid?: boolean;
  infinite?: boolean;
  onLoadMore?: () => void;
  loading?: boolean;
  placeholderElement?: React.ComponentType;
  totalItemCount?: number;
  itemCount?: number;
  itemsPerPage?: number;
  bottomPagination?: boolean;
} & Omit<React.ComponentProps<typeof ViewPagination>, 'totalPages'> &
  React.ComponentProps<typeof Segment>) {
  const [hasScrolled, setHasScrolled] = useState(false);
  const [canLoadMore, setCanLoadMore] = useState(false);

  const onLoadMore = useCallback(
    loadMore
      ? _.throttle(() => {
          loadMore();
          setCanLoadMore(false);
          setHasScrolled(false);
        }, 1000)
      : undefined,
    [loadMore]
  );

  const totalPages = Math.max(
    Math.ceil(totalItemCount / Math.max(itemsPerPage, 1)),
    1
  );

  const getPagination = () => (
    <ViewPagination
      size={paginationSize}
      totalPages={totalPages}
      onPageChange={onPageChange}
      activePage={activePage}
      hrefTemplate={hrefTemplate}
    />
  );

  let fromCount = (+(activePage ?? 1) - 1) * itemsPerPage + 1;
  let toCount = fromCount + Math.min(itemsPerPage - 1, itemCount - 1);
  toCount = Math.min(toCount, totalItemCount);

  fromCount = itemCount ? toCount + 1 - itemCount : 0;
  toCount = itemCount ? toCount : 0;
  if (toCount) {
    fromCount = Math.max(1, fromCount);
  }

  const count = totalItemCount;

  const getPaginationText = () => (
    <Grid.Row centered>
      <Header>
        <Header.Subheader as="h6">
          {t`Showing ${fromCount}-${toCount} of ${count}`}
        </Header.Subheader>
      </Header>
    </Grid.Row>
  );

  useEffect(() => {
    if (!loading && itemsPerPage * +(activePage ?? 1) < totalItemCount) {
      setTimeout(() => {
        setCanLoadMore(true);
      }, 500);
    }
  }, [itemCount, activePage, loading]);

  return (
    <Segment
      basic
      {...props}
      className={classNames('no-padding-segment', { fluid }, props.className)}
    >
      <Grid className="no-margins" verticalAlign="middle" padded="vertically">
        {pagination && getPaginationText()}
        {pagination && (
          <Grid.Row centered className="no-bottom-padding">
            {getPagination()}
          </Grid.Row>
        )}

        <Visibility
          as={Grid.Row}
          fireOnMount={false}
          className={classNames({ 'no-padding-segment': !paddedChildren })}
          onUpdate={useCallback(
            (e, { calculations: { pixelsPassed, height, direction } }) => {
              const pixelsLeft = height - pixelsPassed - getClientHeight();
              if (direction === 'down') {
                setHasScrolled(true);
              }

              if (
                infinite &&
                hasScrolled &&
                canLoadMore &&
                !loading &&
                itemCount &&
                +activePage <= Math.ceil(totalItemCount / itemsPerPage) &&
                onLoadMore &&
                pixelsLeft < 500
              ) {
                onLoadMore();
              }
            },
            [
              infinite,
              onLoadMore,
              canLoadMore,
              loading,
              hasScrolled,
              totalItemCount,
              itemCount,
              itemsPerPage,
              activePage,
            ]
          )}
        >
          {children}
        </Visibility>
        {/* {loading && (
          <Grid.Row>
            <Loader active={loading} />
          </Grid.Row>
        )} */}
        {bottomPagination && pagination && (
          <Grid.Row centered>{getPagination()}</Grid.Row>
        )}
        {bottomPagination && pagination && getPaginationText()}
      </Grid>
    </Segment>
  );
}

export function SidebarPaginatedView({
  children,
  sidebarVisible,
  sidebarAnimation = 'push',
  sidebarContent,
  ...props
}: {
  sidebarAnimation?: React.ComponentProps<typeof Sidebar>['animation'];
  sidebarVisible?: boolean;
  sidebarContent?: React.ReactNode | React.ReactNode[];
} & React.ComponentProps<typeof PaginatedView>) {
  return (
    <PaginatedView as={Sidebar.Pushable} {...props}>
      <Sidebar
        visible={sidebarVisible}
        animation={sidebarAnimation}
        direction="top"
      >
        {sidebarContent}
      </Sidebar>
      <Sidebar.Pusher>{children}</Sidebar.Pusher>
    </PaginatedView>
  );
}

export function ViewBase<T>({
  children,
  arrayContext,
}: {
  arrayContext?: ArrayContextT;
  children: React.ReactNode;
}) {
  const el = <>{children}</>;

  if (arrayContext) {
    return (
      <ArrayContext.Provider value={arrayContext}>
        {children}
      </ArrayContext.Provider>
    );
  }
  return el;
}
