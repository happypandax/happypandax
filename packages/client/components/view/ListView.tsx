import { List, AutoSizer, WindowScroller } from 'react-virtualized';
import { Segment, Grid } from 'semantic-ui-react';

import styles from './ListView.module.css';
import { useCallback } from 'react';
import { ItemSize } from '../../misc/types';
import { PaginatedView, ViewAutoSizer } from '.';

type ItemRender = React.ComponentType<{
  data: any;
  horizontal: boolean;
  size: ItemSize;
  fluid: boolean;
}>;

interface ListViewProps {
  items: any[];
  itemRender: ItemRender;
  size?: ItemSize;
}

function ListViewList({
  width,
  height,
  items,
  size,
  itemRender: ItemRender,
  isScrolling,
  onScroll,
  scrollTop,
  autoHeight,
}: {
  width: number;
  height: number;
  isScrolling?: any;
  onScroll?: any;
  scrollTop?: any;
  autoHeight?: any;
} & ListViewProps) {
  const itemWidth = 600;
  const rowHeight = 140;

  const itemsPerRow = Math.max(Math.floor(width / itemWidth), 1);
  console.log(itemsPerRow);
  const rowCount = Math.ceil(items.length / itemsPerRow);

  return (
    <List
      className="listview"
      autoHeight={autoHeight}
      isScrolling={isScrolling}
      scrollTop={scrollTop}
      onScroll={onScroll}
      width={width}
      height={height}
      rowCount={rowCount}
      rowHeight={rowHeight}
      overscanRowCount={2}
      rowRenderer={useCallback(
        ({ index, key, style }) => {
          const cols = [];
          const fromIndex = index * itemsPerRow;
          const toIndex = Math.min(fromIndex + itemsPerRow, items.length);

          for (let i = fromIndex; i < toIndex; i++) {
            cols.push(
              <div className={styles.item} style={{ flexGrow: 1 }}>
                <ItemRender data={items[i]} horizontal size={size} fluid />
              </div>
            );
          }

          return (
            <div className={styles.row} key={key} style={style}>
              {cols}
            </div>
          );
        },
        [items, itemsPerRow, ItemRender]
      )}
    />
  );
}

export default function ListView({
  itemRender,
  items,
  size = 'tiny',
  disableWindowScroll,
  ...props
}: {
  disableWindowScroll?: boolean;
} & ListViewProps &
  Omit<
    React.ComponentProps<typeof PaginatedView>,
    'children' | 'itemCount' | 'paddedChildren'
  >) {
  return (
    <PaginatedView {...props} itemCount={items.length} paddedChildren>
      <ViewAutoSizer
        items={items}
        itemRender={itemRender}
        disableWindowScroll={disableWindowScroll}
        view={useCallback(
          (p: any) => (
            <ListViewList {...p} size={size} />
          ),
          [size]
        )}
      />
    </PaginatedView>
  );
}
