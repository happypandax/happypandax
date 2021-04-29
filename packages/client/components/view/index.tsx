import classNames from 'classnames';
import { useCallback } from 'react';
import { WindowScroller, AutoSizer } from 'react-virtualized';
import { Segment, Grid, Sidebar, Pagination, Header } from 'semantic-ui-react';
import t from '../../misc/lang';

export function ViewPagination({
  onPageChange,
  activePage,
  totalPages,
}: {
  onPageChange?: React.ComponentProps<typeof Pagination>['onPageChange'];
  activePage?: React.ComponentProps<typeof Pagination>['activePage'];
  totalPages?: React.ComponentProps<typeof Pagination>['totalPages'];
}) {
  return (
    <Pagination
      totalPages={totalPages ?? 1}
      activePage={activePage}
      onPageChange={onPageChange}
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
}: {
  disableWindowScroll?: boolean;
  itemRender: ItemRender;
  items?: any[];
  view: React.ElementType<ViewProps>;
}) {
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
  ...props
}: {
  children: React.ReactNode | React.ReactNode[];
  paddedChildren?: boolean;
  sidebarAnimation?: React.ComponentProps<typeof Sidebar>['animation'];
  sidebarVisible?: boolean;
  sidebarContent?: React.ReactNode | React.ReactNode[];
  onPageChange?: React.ComponentProps<typeof ViewPagination>['onPageChange'];
  activePage?: React.ComponentProps<typeof ViewPagination>['activePage'];
  pagination?: boolean;
  totalItemCount?: number;
  itemCount?: number;
  itemsPerPage?: number;
  bottomPagination?: boolean;
} & React.ComponentProps<typeof Segment>) {
  const totalPages = Math.max(
    Math.floor(totalItemCount / Math.max(itemsPerPage, 1)),
    1
  );

  const getPagination = () => (
    <ViewPagination
      totalPages={totalPages}
      onPageChange={onPageChange}
      activePage={activePage}
    />
  );

  const fromCount = (+(activePage ?? 1) - 1) * itemsPerPage + 1;
  const toCount = fromCount + Math.max(itemCount - 1, 0);
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
      className={classNames('no-padding-segment', props.className)}>
      <Sidebar
        visible={sidebarVisible}
        animation={sidebarAnimation}
        direction="top">
        {sidebarContent}
      </Sidebar>
      <Sidebar.Pusher>
        <Grid verticalAlign="middle" padded="vertically">
          {pagination && getPaginatioText()}
          {pagination && (
            <Grid.Row centered className="no-bottom-padding">
              {getPagination()}
            </Grid.Row>
          )}
          <Grid.Row
            className={classNames({ 'no-padding-segment': !paddedChildren })}>
            {children}
          </Grid.Row>
          {bottomPagination && pagination && (
            <Grid.Row centered>{getPagination()}</Grid.Row>
          )}
          {bottomPagination && pagination && getPaginatioText()}
        </Grid>
      </Sidebar.Pusher>
    </Sidebar.Pushable>
  );
}
