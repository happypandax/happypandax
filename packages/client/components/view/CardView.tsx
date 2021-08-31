import classNames from 'classnames';
import { useCallback, useEffect, useRef, useState } from 'react';
import { List } from 'react-virtualized';

import styles from './CardView.module.css';
import { PaginatedView, ViewAutoSizer } from './index';

type ItemRender<T> = React.ComponentType<{ data: T }>;

interface CardViewProps<T> {
  items: T[];
  onItemKey: (T) => any;
  itemRender: ItemRender<T>;
}

function CardViewGrid<T>({
  width: initialWidth,
  height,
  items,
  itemRender: ItemRender,
  isScrolling,
  onScroll,
  scrollTop,
  autoHeight,
  onItemKey,
}: {
  width: number;
  height: number;
  isScrolling?: any;
  onScroll?: any;
  scrollTop?: any;
  autoHeight?: any;
} & CardViewProps<T>) {
  const itemRef = useRef<HTMLDivElement>();
  const [width, setWidth] = useState(initialWidth);
  const [itemWidth, setItemWidth] = useState(250);
  const [rowHeight, setRowHeight] = useState(420);
  const [dims, setDims] = useState(false);

  const itemsPerRow = Math.max(Math.floor(width / itemWidth), 1);
  const rowCount = Math.ceil((items?.length ?? 0) / itemsPerRow);

  useEffect(() => {
    if (itemRef.current) {
      setItemWidth(itemRef.current.offsetWidth);
      setRowHeight(itemRef.current.offsetHeight + 10);
    }
  }, [dims]);

  useEffect(() => {
    if (initialWidth) {
      setWidth(initialWidth);
    }
  }, [initialWidth]);

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
              <div
                ref={itemRef}
                key={onItemKey(items[i])}
                className={styles.item}>
                <ItemRender data={items[i]} />
              </div>
            );
          }

          setDims(true);

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

export default function CardView<T>({
  disableWindowScroll,
  items,
  itemRender,
  onItemKey,
  ...props
}: {
  disableWindowScroll?: boolean;
} & CardViewProps<T> &
  Omit<React.ComponentProps<typeof PaginatedView>, 'children' | 'itemCount'>) {
  return (
    <PaginatedView {...props} itemCount={items?.length}>
      <ViewAutoSizer
        items={items}
        itemRender={itemRender}
        onItemKey={onItemKey}
        disableWindowScroll={disableWindowScroll}
        view={CardViewGrid}
      />
    </PaginatedView>
  );
}
