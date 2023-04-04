import React, { useCallback } from 'react';
import { List } from 'semantic-ui-react';

import {
  closestCenter,
  DndContext,
  PointerSensor,
  useSensor,
  useSensors,
} from '@dnd-kit/core';
import {
  arrayMove,
  horizontalListSortingStrategy,
  SortableContext,
  useSortable,
  verticalListSortingStrategy,
} from '@dnd-kit/sortable';
import { CSS } from '@dnd-kit/utilities';

export function SortableItemItem<T extends { id: string }>({
  item,
  children,
  as: El = List.Item,
  ...props
}: {
  item: T;
  children?: React.ReactNode;
  as?: React.ElementType;
} & { [key: string]: any }) {
  const { attributes, listeners, setNodeRef, transform, transition } =
    useSortable({ id: item.id });

  delete attributes.role;

  const style = {
    transform: CSS.Transform.toString(transform),
    transition,
  };

  return (
    <El
      ref={setNodeRef}
      style={style}
      {...attributes}
      {...listeners}
      item={item}
      {...props}
    >
      {children}
    </El>
  );
}

export class DragItemPointerSensor extends PointerSensor {
  static activators = [
    {
      eventName: 'onPointerDown' as const,
      handler: (event) => {
        if (!event.nativeEvent.target?.dataset?.dragItem) {
          return false;
        }

        return true;
      },
    },
  ];
}

export function SortableList<T extends { id: string }, P extends { item: T }>({
  element: Element,
  direction = 'vertical',
  items,
  onlyOnDragItem,
  onItemsChange,
}: {
  element: React.ComponentType<P>;
  items: T[];
  direction?: 'vertical' | 'horizontal';
  onlyOnDragItem?: boolean;
  onItemsChange: (items: T[]) => void;
}) {
  const sensors = useSensors(
    useSensor(onlyOnDragItem ? DragItemPointerSensor : PointerSensor)
  );

  const handleDragEnd = useCallback(
    (event) => {
      const { active, over } = event;

      if (active.id !== over.id) {
        const oldIndex = items.findIndex((item) => item.id === active.id);
        const newIndex = items.findIndex((item) => item.id === over.id);
        const r = arrayMove(items, oldIndex, newIndex);
        onItemsChange?.(r);
      }
    },
    [onItemsChange]
  );

  return (
    <DndContext
      sensors={sensors}
      collisionDetection={closestCenter}
      onDragEnd={handleDragEnd}
    >
      <SortableContext
        items={items}
        strategy={
          direction === 'vertical'
            ? verticalListSortingStrategy
            : horizontalListSortingStrategy
        }
      >
        {items.map((i) => (
          <Element key={i.id} item={i} />
        ))}
      </SortableContext>
    </DndContext>
  );
}
