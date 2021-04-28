import { List, AutoSizer, WindowScroller } from 'react-virtualized';
import { Segment, Grid } from 'semantic-ui-react';

import styles from './ListView.module.css';
import { useCallback } from 'react';
import { ItemSize } from '../../misc/types';

type ItemRender = React.ComponentType<{
  data: any;
  horizontal: boolean;
  size: ItemSize;
  fluid: boolean;
}>;

function ListViewList({
  width,
  height,
  items,
  size,
  itemRender: ItemRender,
  ...props
}: {
  width: number;
  height: number;
  items: any[];
  size: ItemSize;
  itemRender: ItemRender;
} & Record<string, any>) {
  const itemWidth = 600;
  const rowHeight = 140;

  const itemsPerRow = Math.max(Math.floor(width / itemWidth), 1);
  console.log(itemsPerRow);
  const rowCount = Math.ceil(items.length / itemsPerRow);

  return (
    <List
      {...props}
      className="listview"
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
  windowScroll,
}: {
  size: ItemSize;
  itemRender: ItemRender;
  items: any[];
  windowScroll?: boolean;
}) {
  const elFunc = windowScroll
    ? useCallback(
        ({ width }) => {
          return (
            <WindowScroller>
              {({ height, isScrolling, onChildScroll, scrollTop }) => (
                <ListViewList
                  itemRender={itemRender}
                  items={items}
                  height={height}
                  width={width}
                  size={size}
                  isScrolling={isScrolling}
                  onScroll={onChildScroll}
                  scrollTop={scrollTop}
                  autoHeight
                />
              )}
            </WindowScroller>
          );
        },
        [itemRender, items]
      )
    : useCallback(
        ({ height, width }) => {
          return (
            <ListViewList
              itemRender={itemRender}
              items={items}
              height={height}
              width={width}
              size={size}
            />
          );
        },
        [itemRender, items]
      );

  return <AutoSizer>{elFunc}</AutoSizer>;
}
