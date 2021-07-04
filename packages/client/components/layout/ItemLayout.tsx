import classNames from 'classnames';
import {
  Button,
  ButtonGroup,
  Dropdown,
  Icon,
  Menu,
  Popup,
} from 'semantic-ui-react';
import { useState, useCallback } from 'react';
import t from '../../misc/lang';
import { ItemType, ViewType } from '../../misc/enums';
import { useMemo } from 'react';

export function SortButtonInput({
  className,
  active,
  setActive,
}: {
  className?: string;
  active: null | string;
  setActive: (f: null | string) => void;
}) {
  return (
    <Popup
      on="click"
      position="left center"
      hoverable
      trigger={
        <Button
          icon="sort content ascending"
          primary
          circular
          className={classNames(className)}
        />
      }>
      <Popup.Content>
        <Menu secondary vertical>
          <Menu.Item
            active={active === 'sort 1'}
            icon="sort"
            color="blue"
            name="sort 1"
            onClick={() => {
              setActive('sort 1');
            }}
          />
          <Menu.Item
            active={active === 'sort 2'}
            icon="sort"
            color="blue"
            name="sort 2"
            onClick={() => {
              setActive('sort 2');
            }}
          />
          <Menu.Item
            active={active === 'sort 3'}
            icon="sort"
            color="blue"
            name="sort 3"
            onClick={() => {
              setActive('sort 3');
            }}
          />
        </Menu>
      </Popup.Content>
    </Popup>
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
  setActive,
}: {
  className?: string;
  active: null | string;
  setActive: (f: null | string) => void;
}) {
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
          <Menu.Item
            active={active === 'filter 1'}
            icon="filter"
            color="blue"
            name="filter 1"
            onClick={() => {
              setActive('filter 1');
            }}
          />
          <Menu.Item
            active={active === 'filter 2'}
            icon="filter"
            color="blue"
            name="filter 2"
            onClick={() => {
              setActive('filter 2');
            }}
          />
          <Menu.Item
            active={active === 'filter 3'}
            icon="filter"
            color="blue"
            name="filter 3"
            onClick={() => {
              setActive('filter 3');
            }}
          />
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
