import classNames from 'classnames';
import Link from 'next/link';
import React, { useContext, useMemo } from 'react';
import { useState, useCallback } from 'react';
import { useRef } from 'react';
import { useHover, useMouseHovered } from 'react-use';
import { Label, Popup } from 'semantic-ui-react';
import { ItemSize } from '../misc/types';
import {
  Card,
  Image,
  Dimmer,
  Rating,
  Icon,
  List,
  Loader,
} from 'semantic-ui-react';

const ItemContext = React.createContext({ hover: false, loading: false });

export function InboxIconLabel() {
  return (
    <Icon
      name="inbox"
      bordered
      inverted
      size="small"
      link
      title={`This item is in your inbox`}
    />
  );
}

export function ReadLaterIconLabel() {
  return (
    <Icon
      name="bookmark"
      bordered
      inverted
      size="small"
      link
      title={`Save for later`}
    />
  );
}

export function ReadingIconLabel() {
  return (
    <Icon
      name="eye"
      bordered
      inverted
      size="small"
      color="orange"
      link
      title={`This item is being read`}
    />
  );
}

export function UnreadIconLabel() {
  return (
    <Icon
      name="eye slash outline"
      bordered
      inverted
      size="small"
      link
      title={`This item has not been read yet`}
    />
  );
}

export function TranslucentLabel({
  children,
  circular,
}: {
  children: React.ReactNode;
  circular?: boolean;
}) {
  return (
    <Label circular={circular} className="translucent-black">
      {children}
    </Label>
  );
}

export function ItemMenuLabelItem({
  ...props
}: React.ComponentProps<typeof List.Item>) {
  return <List.Item {...props} />;
}

export function ItemMenuLabel({
  children,
}: {
  children: React.ReactNode | React.ReactNode[];
}) {
  return (
    <Popup
      hoverable
      on="click"
      hideOnScroll
      position="right center"
      trigger={useMemo(
        () => (
          <Icon name="ellipsis vertical" bordered link inverted />
        ),
        []
      )}>
      <List selection relaxed>
        {children}
      </List>
    </Popup>
  );
}

export function ItemLabel({
  x = 'left',
  y = 'top',
  children,
}: {
  x?: 'left' | 'right';
  y?: 'top' | 'bottom';
  children?: React.ReactNode;
}) {
  return (
    <div className={classNames('card-item above-dimmer', x, y)}>{children}</div>
  );
}

// https://github.com/Semantic-Org/Semantic-UI-React/issues/3950
export function HeartIconLabel({
  onRate,
  defaultRating,
}: {
  onRate?: React.ComponentProps<typeof Rating>['onRate'];
  defaultRating?: React.ComponentProps<typeof Rating>['defaultRating'];
}) {
  return (
    <Rating
      icon="heart"
      onRate={onRate}
      size="massive"
      defaultRating={defaultRating}
    />
  );
}

export function ProgressLabel() {
  return (
    <TranslucentLabel circular>
      <Loader inline active size="mini" />
    </TranslucentLabel>
  );
}

function ItemCardLabels({ children }: { children: React.ReactNode }) {
  return <div className="card-content">{children}</div>;
}

export function ItemCardContent({
  title,
  subtitle,
  description,
}: {
  title: React.ReactNode;
  subtitle?: React.ReactNode;
  description?: React.ReactNode;
}) {
  return (
    <Card.Content>
      <Card.Header className="text-ellipsis card-header">{title}</Card.Header>
      {subtitle && <Card.Meta className="text-ellipsis">{subtitle}</Card.Meta>}
      {description && <Card.Description>{description}</Card.Description>}
    </Card.Content>
  );
}

export function ItemCardImageContentItem({
  children,
}: {
  children?: React.ReactNode;
}) {
  return <List.Item>{children}</List.Item>;
}

export function ItemCardImageContent({
  children,
}: {
  children?: React.ReactNode;
}) {
  return <List>{children}</List>;
}

export function ItemCardImage({ children }: { children?: React.ReactNode }) {
  const itemContext = useContext(ItemContext);

  return (
    <Image
      src="/img/default.png"
      fluid
      centered
      dimmer={{ active: itemContext.hover, inverted: true, children }}
    />
  );
}

export function ItemCard({
  children,
  size,
  href,
  className,
  labels,
  loading,
  image,
  centered,
  link,
}: {
  children?: React.ReactNode;
  className?: string;
  labels?: React.ReactNode[];
  image?: React.ElementType;
  href?: string;
  loading?: boolean;
  size?: ItemSize;
  centered?: boolean;
  link?: boolean;
}) {
  const Im = image;
  const [hover, setHover] = useState(false);
  const itemContext = useContext(ItemContext);

  let itemSize = size ?? 'medium';
  if (!size) {
  }

  return (
    <ItemContext.Provider value={{ ...itemContext, hover, loading }}>
      <Card
        onMouseEnter={useCallback(() => setHover(true), [])}
        onMouseLeave={useCallback(() => setHover(false), [])}
        centered={centered}
        link={link}
        className={classNames(`${itemSize}-size`)}>
        <Dimmer active={loading} inverted>
          <Loader inverted active={loading} />
        </Dimmer>
        <ItemCardLabels>
          {href && (
            <Link href={href}>
              <a>
                <Im />
              </a>
            </Link>
          )}
          {!!!href && <Im />}
          {labels}
        </ItemCardLabels>
        {children}
      </Card>
    </ItemContext.Provider>
  );
}

export default {};
