import classNames from 'classnames';
import { Button, Menu, Popup } from 'semantic-ui-react';
import { useState, useCallback } from 'react';
import t from '../../misc/lang';

export function SortButtonInput({ className }: { className?: string }) {
  const [active, setActive] = useState('sort 1');

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

export function FilterButtonInput({ className }: { className?: string }) {
  const [active, setActive] = useState('filter 1');

  return (
    <Popup
      on="click"
      position="left center"
      hoverable
      trigger={
        <Button
          icon="filter"
          primary
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

export function OnlyFavoritesButton({ className }: { className?: string }) {
  const [active, setActive] = useState(false);

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

export default function ItemLayout({
  children,
}: {
  children?: React.ReactNode;
}) {
  return <div></div>;
}
