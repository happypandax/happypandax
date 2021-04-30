import { List } from 'react-virtualized';

import styles from './CardView.module.css';
import { useCallback } from 'react';
import classNames from 'classnames';
import { ViewAutoSizer, PaginatedView } from './index';

type ItemRender = React.ComponentType<{ data: any }>;

interface CardViewProps {
  items: any[];
  itemRender: ItemRender;
}

function CardViewGrid({
  width,
  height,
  items,
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
} & CardViewProps) {
  const itemWidth = 200;
  const rowHeight = 380;

  const itemsPerRow = Math.max(Math.floor(width / itemWidth), 1);
  const rowCount = Math.ceil(items.length / itemsPerRow);

  return (
    <List
      className={classNames('galleryview')}
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

export default function CardView({
  disableWindowScroll,
  items,
  itemRender,
  ...props
}: {
  disableWindowScroll?: boolean;
} & CardViewProps &
  Omit<React.ComponentProps<typeof PaginatedView>, 'children' | 'itemCount'>) {
  return (
    <PaginatedView {...props} itemCount={items.length}>
      <ViewAutoSizer
        items={items}
        itemRender={itemRender}
        disableWindowScroll={disableWindowScroll}
        view={CardViewGrid}
      />
    </PaginatedView>
  );
}
