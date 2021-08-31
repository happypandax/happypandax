import { useCallback, useEffect, useRef, useState } from 'react';
import { List } from 'react-virtualized';

import { ItemSize } from '../../misc/types';
import { PaginatedView, ViewAutoSizer } from './';
import styles from './ListView.module.css';

type ItemRender<T> = React.ComponentType<{
  data: T;
  horizontal: boolean;
  size: ItemSize;
  fluid: boolean;
}>;

interface ListViewProps<T> {
  items: T[];
  onItemKey: (T) => any;
  itemRender: ItemRender<T>;
  size?: ItemSize;
}

function ListViewList<T>({
  width: initialWidth,
  height,
  items,
  size,
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
} & ListViewProps<T>) {
  const itemRef = useRef<HTMLDivElement>();
  const [itemWidth, setItemWidth] = useState(600);
  const [rowHeight, setRowHeight] = useState(140);
  const [dims, setDims] = useState(false);
  const [width, setWidth] = useState(initialWidth);

  const itemsPerRow = Math.max(Math.floor(width / itemWidth), 1);
  const rowCount = Math.ceil((items.length ?? 0) / itemsPerRow);

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
              <div
                key={onItemKey(items[i])}
                className={styles.item}
                style={{ flexGrow: 1 }}>
                <ItemRender data={items[i]} horizontal size={size} fluid />
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

export default function ListView<T>({
  itemRender,
  items,
  size = 'tiny',
  disableWindowScroll,
  onItemKey,
  ...props
}: {
  disableWindowScroll?: boolean;
} & ListViewProps<T> &
  Omit<
    React.ComponentProps<typeof PaginatedView>,
    'children' | 'itemCount' | 'paddedChildren'
  >) {
  return (
    <PaginatedView {...props} itemCount={items?.length} paddedChildren>
      <ViewAutoSizer
        items={items}
        itemRender={itemRender}
        disableWindowScroll={disableWindowScroll}
        onItemKey={onItemKey}
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
