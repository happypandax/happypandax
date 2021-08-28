import classNames from 'classnames';
import _ from 'lodash';
import { useRouter } from 'next/router';
import { useCallback, useMemo } from 'react';
import { AutoSizer, WindowScroller } from 'react-virtualized';
import {
  Grid,
  Header,
  Pagination,
  Segment,
  Sidebar,
  Visibility,
} from 'semantic-ui-react';

import t from '../../misc/lang';
import { getClientHeight } from '../../misc/utility';

export function ViewPagination({
  onPageChange,
  activePage,
  totalPages,
  hrefTemplate,
}: {
  onPageChange?: React.ComponentProps<typeof Pagination>['onPageChange'];
  activePage?: React.ComponentProps<typeof Pagination>['activePage'];
  totalPages?: React.ComponentProps<typeof Pagination>['totalPages'];
  hrefTemplate?: string;
}) {
  const router = useRouter();
  const tmpl = useMemo(() => {
    return _.template(hrefTemplate ?? '');
  }, [hrefTemplate]);

  return (
    <Pagination
      totalPages={totalPages ?? 1}
      activePage={activePage}
      onPageChange={onPageChange}
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
                onPageChange?.(ev, props);
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

        const href = tmpl({
          page: Math.max(1, parseInt(activePage as string, 10) - 1),
        });

        return {
          'aria-label': t`Previous item`,
          content: '⟨',
          href,
          onClick: (ev) => {
            onPageChange?.(ev, undefined);
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
          'aria-label': t`First  item`,
          content: '«',
          href,
          onClick: (ev) => {
            onPageChange?.(ev, undefined);
            if (href) {
              ev.preventDefault();
              router.push(href);
            }
          },
        };
      }, [hrefTemplate, activePage, onPageChange])}
      nextItem={useMemo(() => {
        if (!hrefTemplate) return undefined;

        const href = tmpl({
          page: Math.min(
            parseInt(totalPages as string, 10),
            parseInt(activePage as string, 10) + 1
          ),
        });

        return {
          'aria-label': t`Next item`,
          content: '⟩',
          href,
          onClick: (ev) => {
            onPageChange?.(ev, undefined);
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
            onPageChange?.(ev, undefined);
            if (href) {
              ev.preventDefault();
              router.push(href);
            }
          },
        };
      }, [hrefTemplate, activePage, totalPages, onPageChange])}
      pointing
      secondary
      size="small"
    />
  );
}

type ItemRender = React.ComponentType<{ data: any }>;

export interface ViewProps {
  width: number;
  height: number;
  isScrolling?: any;
  itemRender: ItemRender;
  items?: any;
  onScroll?: any;
  scrollTop?: any;
  autoHeight?: any;
}

// TODO: Does not show anything when having a parent component when disableWindowScroll=true
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
  const elFunc = !disableWindowScroll
    ? useCallback(
        ({ width }) => {
          return (
            <WindowScroller>
              {({ height, isScrolling, onChildScroll, scrollTop }) => (
                <View
                  items={items}
                  itemRender={itemRender}
                  height={height}
                  width={width}
                  isScrolling={isScrolling}
                  onScroll={onChildScroll}
                  scrollTop={scrollTop}
                  autoHeight
                  {...viewProps}
                />
              )}
            </WindowScroller>
          );
        },
        [items, itemRender]
      )
    : useCallback(
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
        [items, itemRender]
      );

  return <AutoSizer disableHeight={!disableWindowScroll}>{elFunc}</AutoSizer>;
}

export function PaginatedView({
  children,
  sidebarVisible,
  sidebarAnimation = 'push',
  sidebarContent,
  pagination,
  paddedChildren,
  bottomPagination,
  itemsPerPage = 20,
  totalItemCount = 0,
  itemCount = 0,
  activePage,
  onPageChange,
  fluid,
  hrefTemplate,
  infinite,
  onLoadMore,
  ...props
}: {
  children: React.ReactNode | React.ReactNode[];
  paddedChildren?: boolean;
  sidebarAnimation?: React.ComponentProps<typeof Sidebar>['animation'];
  sidebarVisible?: boolean;
  sidebarContent?: React.ReactNode | React.ReactNode[];
  pagination?: boolean;
  fluid?: boolean;
  infinite?: boolean;
  onLoadMore?: () => void;
  totalItemCount?: number;
  itemCount?: number;
  itemsPerPage?: number;
  bottomPagination?: boolean;
} & Omit<React.ComponentProps<typeof ViewPagination>, 'totalPages'> &
  React.ComponentProps<typeof Segment>) {
  const totalPages = Math.max(
    Math.floor(totalItemCount / Math.max(itemsPerPage, 1)),
    1
  );

  const getPagination = () => (
    <ViewPagination
      totalPages={totalPages}
      onPageChange={onPageChange}
      activePage={activePage}
      hrefTemplate={hrefTemplate}
    />
  );

  let fromCount = (+(activePage ?? 1) - 1) * itemsPerPage + 1;
  const toCount = fromCount + itemsPerPage - 1;
  fromCount = toCount + 1 - itemCount;
  const count = totalItemCount;

  const getPaginatioText = () => (
    <Grid.Row centered>
      <Header>
        <Header.Subheader as="h6">
          {t`Showing ${fromCount}-${toCount} of ${count}`}
        </Header.Subheader>
      </Header>
    </Grid.Row>
  );

  return (
    <Sidebar.Pushable
      as={Segment}
      basic
      {...props}
      className={classNames('no-padding-segment', { fluid }, props.className)}>
      <Sidebar
        visible={sidebarVisible}
        animation={sidebarAnimation}
        direction="top">
        {sidebarContent}
      </Sidebar>
      <Sidebar.Pusher>
        <Grid
          as={Segment}
          basic
          className="no-margins"
          verticalAlign="middle"
          padded="vertically">
          {pagination && getPaginatioText()}
          {pagination && (
            <Grid.Row centered className="no-bottom-padding">
              {getPagination()}
            </Grid.Row>
          )}
          <Visibility
            as={Grid.Row}
            className={classNames({ 'no-padding-segment': !paddedChildren })}
            onUpdate={useCallback(
              (e, { calculations: { pixelsPassed, height } }) => {
                const pixelsLeft = height - pixelsPassed - getClientHeight();
                if (infinite && onLoadMore && pixelsLeft < 500) {
                  onLoadMore();
                }
              },
              [infinite, onLoadMore]
            )}>
            {children}
          </Visibility>
          {bottomPagination && pagination && (
            <Grid.Row centered>{getPagination()}</Grid.Row>
          )}
          {bottomPagination && pagination && getPaginatioText()}
        </Grid>
      </Sidebar.Pusher>
    </Sidebar.Pushable>
  );
}
