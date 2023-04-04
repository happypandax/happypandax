import classNames from 'classnames';
import {
  forwardRef,
  memo,
  useCallback,
  useEffect,
  useRef,
  useState,
} from 'react';
import { areEqual, VariableSizeList as List } from 'react-window';

import { ItemSize } from '../../shared/types';
import { PlaceholderItemCard } from '../item/index';
import styles from './CardView.module.css';
import { PaginatedView, ViewAutoSizer, ViewBase } from './index';

type ItemRender<T> = React.ComponentType<{ data: T; size?: ItemSize }>;

interface CardViewProps<T> {
  items: T[];
  onItemKey: (item: T) => any;
  itemRender: ItemRender<T>;
  loading?: boolean;
  itemsPerPage?: number;
  size?: ItemSize;
  dynamicRowHeight?: boolean;
}

type CardViewRenderData = {
  onSetDims: (dims: boolean) => void;
  itemRef: React.Ref<HTMLDivElement>;
  itemsPerRow: number;
} & CardViewProps<any>;

const CardViewRender = memo(function CardViewRender({
  index,
  key,
  style,
  data: {
    onSetDims,
    itemRef,
    items,
    itemsPerRow,
    loading,
    itemRender: ItemRender,
    onItemKey,
    size,
  },
}: {
  index: number;
  key: any;
  style: React.CSSProperties;
  data: CardViewRenderData;
}) {
  const cols = [];
  if (items?.length) {
    const fromIndex = index * itemsPerRow;
    const toIndex = fromIndex + itemsPerRow;

    for (let i = fromIndex; i < toIndex; i++) {
      if (i >= items.length) {
        if (loading) {
          cols.push(
            <div ref={itemRef} key={`loading-${i}`} className={styles.item}>
              <PlaceholderItemCard size={size} />
            </div>
          );
        }
        continue;
      }

      cols.push(
        <div ref={itemRef} key={onItemKey(items[i])} className={styles.item}>
          <ItemRender data={items[i]} size={size} />
        </div>
      );
    }

    onSetDims(true);
  }

  return (
    <div className={styles.row} key={key} style={style}>
      {cols}
    </div>
  );
},
areEqual);

const CardViewGrid = forwardRef(function CardViewGrid<T>(
  {
    outerRef,
    style,
    width: initialWidth,
    height,
    items,
    dynamicRowHeight,
    itemRender: ItemRender,
    loading,
    itemsPerPage,
    onScroll,
    scrollTop,
    onItemKey,
    size,
  }: {
    width: number;
    height: number;
    outerRef?: React.Ref<any>;
    style?: React.CSSProperties;
    onScroll?: any;
    scrollTop?: any;
  } & CardViewProps<T>,
  ref
) {
  const itemRef = useRef<HTMLDivElement>();
  const [width, setWidth] = useState(initialWidth);
  const [itemWidth, setItemWidth] = useState(250);
  const [rowHeight, setRowHeight] = useState(420);
  const [dims, setDims] = useState(false);

  const itemsPerRow = Math.max(Math.floor(width / itemWidth), 1);
  const rowCount = Math.ceil(
    ((items?.length ?? 0) + (loading && itemsPerPage ? itemsPerPage : 0)) /
      itemsPerRow
  );

  const [data, setData] = useState<CardViewRenderData>({
    items,
    itemsPerRow,
    itemRender: ItemRender,
    loading,
    size,
    onSetDims: setDims,
    onItemKey,
    itemRef,
  });

  useEffect(() => {
    setData({
      items,
      itemsPerRow,
      itemRender: ItemRender,
      loading,
      size,
      onSetDims: setDims,
      onItemKey,
      itemRef,
    });
  }, [items, itemsPerRow, ItemRender, loading, onItemKey]);

  const resize = useCallback(() => {
    if (itemRef.current) {
      if (dynamicRowHeight) {
        const margin = size === 'small' ? 10 : 35;
        setItemWidth(itemRef.current.children[0].offsetWidth || itemWidth);
        setRowHeight(
          itemRef.current.children[0].offsetHeight + margin || rowHeight
        );
      } else {
        setItemWidth(itemRef.current.offsetWidth || itemWidth);
        setRowHeight(itemRef.current.offsetHeight || rowHeight);
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
        const f = () => setTimeout(resize, 150);
        el.addEventListener('load', resize);
        el.addEventListener('error', f);
        return () => {
          el?.removeEventListener('load', resize);
          el?.removeEventListener('error', f);
        };
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
      ref={ref}
      style={style}
      outerRef={outerRef}
      className={classNames('galleryview')}
      width={width}
      height={height}
      overscanCount={10}
      initialScrollOffset={scrollTop}
      onScroll={onScroll}
      itemCount={rowCount}
      itemData={data}
      itemKey={(index, data) =>
        onItemKey
          ? data?.items?.length
            ? onItemKey(data.items[index])
            : index
          : index
      }
      itemSize={() => rowHeight}
      estimatedItemSize={rowHeight}
    >
      {CardViewRender}
    </List>
  );
});

export default function CardView<T>({
  disableWindowScroll,
  items,
  itemRender,
  dynamicRowHeight,
  size,
  onItemKey,
  arrayContext,
  ...props
}: {
  disableWindowScroll?: boolean;
} & CardViewProps<T> &
  React.ComponentProps<typeof ViewBase> &
  Omit<React.ComponentProps<typeof PaginatedView>, 'children' | 'itemCount'>) {
  return (
    <ViewBase arrayContext={arrayContext}>
      <PaginatedView {...props} itemCount={items?.length}>
        <ViewAutoSizer
          items={items}
          size={size}
          loading={props.loading}
          itemsPerPage={props.itemsPerPage}
          itemRender={itemRender}
          dynamicRowHeight={dynamicRowHeight}
          onItemKey={onItemKey}
          disableWindowScroll={disableWindowScroll}
          view={CardViewGrid}
        />
      </PaginatedView>
    </ViewBase>
  );
}
