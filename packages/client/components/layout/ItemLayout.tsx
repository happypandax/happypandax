import classNames from 'classnames';
import { useCallback, useMemo } from 'react';
import {
  Button,
  ButtonGroup,
  Dropdown,
  Icon,
  Menu,
  Popup,
} from 'semantic-ui-react';

import { QueryType, useQueryType } from '../../client/queries';
import { ItemType, ViewType } from '../../misc/enums';
import t from '../../misc/lang';
import { FieldPath, ServerFilter, ServerSortIndex } from '../../misc/types';

export function SortButtonInput({
  itemType,
  className,
  data: initialData,
  active,
  setActive,
}: {
  itemType: ItemType;
  className?: string;
  active?: number;
  data?: ServerSortIndex[];
  setActive: (f: number) => void;
}) {
  const { data } = useQueryType(
    QueryType.SORT_INDEXES,
    {
      item_type: itemType,
    },
    { initialData }
  );

  return (
    <Popup
      on="click"
      position="left center"
      hoverable
      trigger={
        <Button
          icon="sort alphabet down"
          primary
          circular
          className={classNames(className)}
        />
      }>
      <Popup.Content>
        <Menu secondary vertical>
          {!!data?.data &&
            data.data
              .sort((a, b) => a.name.localeCompare(b.name))
              .map((v) => (
                <Menu.Item
                  key={v.index}
                  index={v.index}
                  active={v.index === active}
                  icon="sort"
                  color="blue"
                  name={v.name}
                  onClick={() => {
                    setActive(v.index);
                  }}
                />
              ))}
        </Menu>
      </Popup.Content>
    </Popup>
  );
}

export function SortOrderButton(
  props: React.ComponentProps<typeof Button> & { descending?: boolean }
) {
  return (
    <Button
      icon={{
        className: props.descending
          ? 'sort amount down'
          : 'sort amount down alternate',
      }}
      primary
      circular
      basic
      color="blue"
      title={t`Sort order`}
      {...props}
    />
  );
}

export function ClearFilterButton(props: React.ComponentProps<typeof Button>) {
  return (
    <Button
      icon="close"
      primary
      circular
      basic
      color="red"
      title={t`Clear filter`}
      {...props}
    />
  );
}

export function FilterButtonInput({
  className,
  active,
  data: initialData,
  setActive,
}: {
  className?: string;
  active: number;
  setActive: (f: number) => void;
  data?: ServerFilter[];
}) {
  const { data } = useQueryType(
    QueryType.ITEMS,
    {
      item_type: ItemType.Filter,
      fields: ['name'] as FieldPath<ServerFilter>[],
      limit: 9999, // no limit
    },
    { initialData }
  );

  return (
    <Popup
      on="click"
      position="left center"
      hoverable
      trigger={
        <Button
          icon="filter"
          primary
          inverted={!!!active}
          circular
          className={classNames(className)}
        />
      }>
      <Popup.Content>
        <Menu secondary vertical>
          {!!data?.data &&
            data.data?.map?.((v) => (
              <Menu.Item
                key={v.id}
                index={v.id}
                active={active === v.id}
                icon="filter"
                color="blue"
                name={v.name}
                onClick={() => {
                  setActive(v.id);
                }}
              />
            ))}
        </Menu>
      </Popup.Content>
    </Popup>
  );
}

export function OnlyFavoritesButton({
  className,
  active,
  setActive,
}: {
  className?: string;
  active: boolean;
  setActive: (boolean) => void;
}) {
  return (
    <Button
      icon="heart"
      title={t`Show only favorites`}
      basic={!active}
      color="red"
      onClick={useCallback(() => {
        setActive(!active);
      }, [active])}
      circular
      className={classNames(className)}
    />
  );
}

export function ViewButtons({
  size = 'tiny',
  item,
  setItem,
  setView,
  view,
}: {
  size?: React.ComponentProps<typeof ButtonGroup>['size'];
  view: ViewType;
  setView: (view: ViewType) => void;
  item: ItemType;
  setItem: (item: ItemType) => void;
}) {
  const options = useMemo(
    () => [
      {
        text: (
          <>
            <Icon name="th" /> {t`All`}
          </>
        ),
        value: ViewType.All,
      },
      {
        text: (
          <>
            <Icon name="archive" /> {t`Library`}
          </>
        ),
        value: ViewType.Library,
      },
      {
        text: (
          <>
            <Icon name="inbox" /> {t`Inbox`}
          </>
        ),
        value: ViewType.Inbox,
      },
    ],
    []
  );

  return (
    <ButtonGroup toggle basic size={size}>
      <Dropdown
        selectOnBlur={false}
        disabled={view === ViewType.Favorite}
        basic
        className="active"
        value={view}
        options={options}
        button
      />
      <Button
        primary
        basic={item === ItemType.Collection}
        onClick={useCallback(() => {
          setItem(ItemType.Collection);
        }, [])}>{t`Collection`}</Button>
      <Button
        primary
        basic={item === ItemType.Gallery}
        onClick={useCallback(() => {
          setItem(ItemType.Gallery);
        }, [])}>{t`Gallery`}</Button>
    </ButtonGroup>
  );
}

export default function ItemLayout({
  children,
}: {
  children?: React.ReactNode;
}) {
  return <div></div>;
}
