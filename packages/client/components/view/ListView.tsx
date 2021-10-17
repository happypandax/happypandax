import { useCallback, useEffect, useRef, useState } from 'react';
import { List } from 'react-virtualized';

import { ItemSize } from '../../misc/types';
import { PaginatedView, ViewAutoSizer } from './';
import styles from './ListView.module.css';

type ItemRender<T> = React.ComponentType<{
  data: T;
  horizontal?: boolean;
  size?: ItemSize;
  fluid?: boolean;
}>;

interface ListViewProps<T> {
  items: T[];
  onItemKey: (T) => any;
  itemRender: ItemRender<T>;
  size?: ItemSize;
  dynamicRowHeight?: boolean;
}

function ListViewList<T>({
  width: initialWidth,
  height,
  items,
  dynamicRowHeight,
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

  const resize = useCallback(() => {
    if (itemRef.current) {
      if (dynamicRowHeight) {
        const margin = size === 'small' ? 7 : 15;
        setItemWidth(itemRef.current.children[0].offsetWidth);
        setRowHeight(itemRef.current.children[0].offsetHeight + margin);
      } else {
        setItemWidth(itemRef.current.offsetWidth);
        setRowHeight(itemRef.current.offsetHeight);
      }
    }
  }, [dynamicRowHeight]);

  useEffect(() => {
    resize();
  }, [dims, resize]);

  useEffect(() => {
    if (dynamicRowHeight && itemRef.current) {
      const el = itemRef.current.querySelector('img');
      if (el) {
        const f = resize;
        el.addEventListener('load', f);
        return () => el?.removeEventListener('load', f);
      }
    }
  }, [dynamicRowHeight, resize, items, dims]);

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
                ref={itemRef}
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
  size = 'small',
  disableWindowScroll,
  dynamicRowHeight,
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
        size={size}
        itemRender={itemRender}
        dynamicRowHeight={dynamicRowHeight}
        disableWindowScroll={disableWindowScroll}
        onItemKey={onItemKey}
        view={ListViewList}
      />
    </PaginatedView>
  );
}
