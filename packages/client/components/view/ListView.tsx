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
import { PaginatedView, ViewAutoSizer, ViewBase } from './';
import styles from './ListView.module.css';

type ItemRender<T> = React.ComponentType<{
  data: T;
  horizontal?: boolean;
  size?: ItemSize;
  fluid?: boolean;
}>;

interface ListViewProps<T> {
  items: T[];
  onItemKey: (item: T) => any;
  itemRender: ItemRender<T>;
  loading?: boolean;
  itemsPerPage?: number;
  size?: ItemSize;
  dynamicRowHeight?: boolean;
}

type ListViewRenderData = {
  onSetDims: (dims: boolean) => void;
  itemRef: React.Ref<HTMLDivElement>;
  itemsPerRow: number;
} & ListViewProps<any>;

const ListViewRender = memo(function ListViewRender({
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
  data: ListViewRenderData;
}) {
  const cols = [];

  if (items?.length) {
    const fromIndex = index * itemsPerRow;
    const toIndex = fromIndex + itemsPerRow;

    for (let i = fromIndex; i < toIndex; i++) {
      if (i >= items.length) {
        if (loading) {
          cols.push(
            <div
              ref={itemRef}
              key={`loading-${i}`}
              className={styles.item}
              style={{ flexGrow: 1 }}
            >
              <PlaceholderItemCard horizontal fluid size={size} />
            </div>
          );
        }
        continue;
      }

      cols.push(
        <div
          ref={itemRef}
          key={onItemKey(items[i])}
          className={styles.item}
          style={{ flexGrow: 1 }}
        >
          <ItemRender data={items[i]} horizontal size={size} fluid />
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

const ListViewList = forwardRef(function ListViewList<T>(
  {
    outerRef,
    style,
    width: initialWidth,
    height,
    items,
    dynamicRowHeight,
    size,
    itemRender: ItemRender,
    loading,
    itemsPerPage,
    onScroll,
    scrollTop,
    onItemKey,
  }: {
    outerRef?: React.Ref<any>;
    style?: React.CSSProperties;
    width: number;
    height: number;
    onScroll?: any;
    scrollTop?: any;
    autoHeight?: any;
  } & ListViewProps<T>,
  ref
) {
  const itemRef = useRef<HTMLDivElement>();
  const [itemWidth, setItemWidth] = useState(600);
  const [rowHeight, setRowHeight] = useState(140);
  const [dims, setDims] = useState(false);
  const [width, setWidth] = useState(initialWidth);

  const itemsPerRow = Math.max(Math.floor(width / itemWidth), 1);
  const rowCount = Math.ceil(
    ((items?.length ?? 0) + (loading && itemsPerPage ? itemsPerPage : 0)) /
      itemsPerRow
  );

  const [data, setData] = useState<ListViewRenderData>({
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
      size,
      loading,
      onSetDims: setDims,
      onItemKey,
      itemRef,
    });
  }, [items, itemsPerRow, ItemRender, loading, onItemKey]);

  const resize = useCallback(() => {
    if (itemRef.current) {
      if (dynamicRowHeight) {
        const margin = size === 'small' ? 7 : 15;
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
      outerRef={outerRef}
      style={style}
      className="listview"
      overscanCount={10}
      initialScrollOffset={scrollTop}
      onScroll={onScroll}
      itemKey={(index, data) =>
        onItemKey
          ? data?.items?.length
            ? onItemKey(data.items[index])
            : index
          : index
      }
      itemData={data}
      width={width}
      height={height}
      itemCount={rowCount}
      itemSize={() => rowHeight}
      estimatedItemSize={rowHeight}
    >
      {ListViewRender}
    </List>
  );
});

export default function ListView<T>({
  itemRender,
  items,
  size = 'small',
  disableWindowScroll,
  dynamicRowHeight,
  onItemKey,
  arrayContext,
  ...props
}: {
  disableWindowScroll?: boolean;
} & ListViewProps<T> &
  Omit<
    React.ComponentProps<typeof PaginatedView> &
      React.ComponentProps<typeof ViewBase>,
    'children' | 'itemCount' | 'paddedChildren'
  >) {
  return (
    <ViewBase arrayContext={arrayContext}>
      <PaginatedView {...props} itemCount={items?.length} paddedChildren>
        <ViewAutoSizer
          items={items}
          size={size}
          itemRender={itemRender}
          loading={props.loading}
          itemsPerPage={props.itemsPerPage}
          dynamicRowHeight={dynamicRowHeight}
          disableWindowScroll={disableWindowScroll}
          onItemKey={onItemKey}
          view={ListViewList}
        />
      </PaginatedView>
    </ViewBase>
  );
}
