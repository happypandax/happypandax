import { List, AutoSizer, WindowScroller } from 'react-virtualized';
import { Segment, Grid } from 'semantic-ui-react';

import styles from './GalleryView.module.css';
import { useCallback } from 'react';

type ItemRender = React.ComponentType<{ data: any }>;

function GalleryViewGrid({
  width,
  height,
  items,
  itemRender: ItemRender,
  ...props
}: {
  width: number;
  height: number;
  items: any[];
  itemRender: ItemRender;
} & Record<string, any>) {
  const itemWidth = 200;
  const rowHeight = 380;

  const itemsPerRow = Math.floor(width / itemWidth);
  const rowCount = Math.ceil(items.length / itemsPerRow);

  return (
    <List
      {...props}
      className="galleryview"
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
              <div className={styles.item}>
                <ItemRender data={items[i]} />
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

export default function GalleryView({
  itemRender,
  items,
  windowScroll,
}: {
  itemRender: React.ComponentType<{ data: any }>;
  items: any[];
  windowScroll?: boolean;
}) {
  const elFunc = windowScroll
    ? useCallback(
        ({ width }) => {
          return (
            <WindowScroller>
              {({ height, isScrolling, onChildScroll, scrollTop }) => (
                <GalleryViewGrid
                  itemRender={itemRender}
                  items={items}
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
        [itemRender, items]
      )
    : useCallback(
        ({ height, width }) => {
          return (
            <GalleryViewGrid
              itemRender={itemRender}
              items={items}
              height={height}
              width={width}
            />
          );
        },
        [itemRender, items]
      );

  return <AutoSizer>{elFunc}</AutoSizer>;
}
