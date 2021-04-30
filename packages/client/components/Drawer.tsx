import { useContext, useState, useCallback } from 'react';
import { createContext, useMemo } from 'react';
import { useDrop } from 'react-dnd';
import {
  TransitionablePortal,
  Segment,
  Menu,
  Label,
  Icon,
  Dimmer,
  Tab,
  Ref,
} from 'semantic-ui-react';
import { DragItemData } from '../misc/types';
import { ItemType } from '../misc/enums';
import t from '../misc/lang';
import GalleryCard from './Gallery';
import { EmptyMessage } from './Misc';

export function DragBoard({}) {
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
      <div className="min-200-h">
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
        {!items.length && <EmptyMessage />}
      </div>
    </Ref>
  );
}

export function RecentViewed() {
  const items = [];

  return <>{!items.length && <EmptyMessage />}</>;
}

export function Drawer() {
  return (
    <Segment className="no-padding-segment min-200-h">
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
                  <DragBoard />
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
      <Label
        as="a"
        attached="top right"
        onClick={useCallback(() => undefined, [])}>
        <Icon name="close" fitted />
      </Label>
    </Segment>
  );
}

export default function DrawerPortal() {
  return (
    <TransitionablePortal open={true}>
      <Drawer />
    </TransitionablePortal>
  );
}
