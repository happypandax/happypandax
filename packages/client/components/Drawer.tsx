import classNames from 'classnames';
import { useEffect, useMemo, useState } from 'react';
import { useDrop } from 'react-dnd';
import { useRecoilState } from 'recoil';
import {
  Dimmer,
  Icon,
  Label,
  Ref,
  Segment,
  Tab,
  TransitionablePortal,
} from 'semantic-ui-react';

import { Query, QueryType } from '../client/queries';
import { ImageSize, ItemType } from '../misc/enums';
import t from '../misc/lang';
import { DragItemData } from '../misc/types';
import { AppState } from '../state';
import GalleryCard, { GalleryCardData, galleryCardDataFields } from './Gallery';
import { EmptySegment } from './Misc';

export function SelectedBoard({}: {}) {
  const [items, setItems] = useState([]);

  const [{ isOver }, dropRef] = useDrop(
    () => ({
      accept: ItemType.Gallery.toString(),
      drop: (item: DragItemData, monitor) => {
        setItems([...items, item.data]);
      },
      canDrop: (item, monitor) => !items.find((v) => v.id === item.data.id),
      collect: (monitor) => ({
        isOver: !!monitor.isOver(),
        dragData: monitor.getItem() as DragItemData | null,
      }),
    }),
    [items]
  );

  return (
    <Ref innerRef={dropRef}>
      <Dimmer.Dimmable className="min-200-h" dimmed={isOver}>
        <Dimmer active={isOver}>
          <Icon size="large" name="plus" inverted />
        </Dimmer>
        {items.map((v) => (
          <GalleryCard
            draggable={false}
            key={v.id}
            data={v}
            horizontal
            size="mini"
          />
        ))}
        {!items.length && <EmptySegment />}
      </Dimmer.Dimmable>
    </Ref>
  );
}

export function SessionBoard({}: {}) {
  const [readingSession, setReadingSession] = useRecoilState(
    AppState.readingSession
  );
  const [items, setItems] = useState<GalleryCardData[]>([]);

  const [{ isOver }, dropRef] = useDrop(
    () => ({
      accept: ItemType.Gallery.toString(),
      drop: (item: DragItemData, monitor) => {
        setReadingSession([...readingSession, item.data.id]);
      },
      canDrop: (item, monitor) => !items.find((v) => v.id === item.data.id),
      collect: (monitor) => ({
        isOver: !!monitor.isOver(),
        dragData: monitor.getItem() as DragItemData | null,
      }),
    }),
    [items, readingSession]
  );

  useEffect(() => {
    const f_ids = readingSession.filter(
      (i) => !items.find((i2) => i2.id === i)
    );
    if (f_ids.length) {
      Query.get(QueryType.ITEM, {
        item_id: f_ids,
        item_type: ItemType.Gallery,
        profile_options: {
          size: ImageSize.Small,
        },
        fields: galleryCardDataFields,
      }).then((r) => {
        setItems([...items, ...(r.data as GalleryCardData[])]);
      });
    }
  }, [readingSession]);

  return (
    <Ref innerRef={dropRef}>
      <Dimmer.Dimmable className="min-200-h" dimmed={isOver}>
        <Dimmer active={isOver}>
          <Icon size="large" name="plus" inverted />
        </Dimmer>
        {items.map((v) => (
          <GalleryCard
            draggable={false}
            key={v.id}
            data={v}
            horizontal
            size="mini"
          />
        ))}
        {!items.length && <EmptySegment />}
      </Dimmer.Dimmable>
    </Ref>
  );
}

export function RecentViewed() {
  const items = [];

  return <>{!items.length && <EmptySegment />}</>;
}

export function Drawer({
  className,
  id,
  onClose,
}: {
  className?: string;
  id?: string;
  onClose?: () => void;
}) {
  return (
    <Segment
      id={id}
      className={classNames('no-padding-segment min-200-h', className)}>
      <Tab
        menu={useMemo(
          () => ({ pointing: true, secondary: true, size: 'small' }),
          []
        )}
        panes={useMemo(
          () => [
            {
              menuItem: t`Selected`,
              render: () => (
                <Tab.Pane basic className="no-padding-segment">
                  <SelectedBoard />
                </Tab.Pane>
              ),
            },
            {
              menuItem: t`Session`,
              render: () => (
                <Tab.Pane basic className="no-padding-segment">
                  <SessionBoard />
                </Tab.Pane>
              ),
            },
            {
              menuItem: t`Recently viewed`,
              render: () => (
                <Tab.Pane basic className="no-padding-segment">
                  <RecentViewed />
                </Tab.Pane>
              ),
            },
          ],
          []
        )}
      />
      <Label as="a" attached="top right" onClick={onClose}>
        <Icon name="close" fitted />
      </Label>
    </Segment>
  );
}

export default function DrawerPortal({
  open,
  onClose,
}: {
  open?: boolean;
  onClose?: () => void;
}) {
  return (
    <TransitionablePortal open={open} onClose={onClose}>
      <div id="drawer">
        <Drawer onClose={onClose} />
      </div>
    </TransitionablePortal>
  );
}
