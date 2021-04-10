import classNames from 'classnames';
import Link from 'next/link';
import React, { useContext } from 'react';
import { useState, useCallback } from 'react';
import { useRef } from 'react';
import { useHover, useMouseHovered } from 'react-use';
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

export function InboxIconAction() {
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

export function ReadLaterIconAction() {
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

export function ReadingIconAction() {
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

export function UnreadIconAction() {
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

export function ItemAction({
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
export function HeartIconAction({
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

export function ItemCardProgress() {
  return <div>Progress</div>;
}

function ItemCardActions({ children }: { children: React.ReactNode }) {
  return <div className="card-content">{children}</div>;
}

export function ItemCardContent() {
  return (
    <Card.Content>
      <Card.Header>Daniel</Card.Header>
      <Card.Meta>Joined in 2016</Card.Meta>
      <Card.Description>
        Daniel is a comedian living in Nashville.
      </Card.Description>
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
  const itemContext = useContext(ItemContext);

  return (
    <Dimmer active={itemContext.hover} inverted>
      <List>{children}</List>
    </Dimmer>
  );
}

export function ItemCardImage({ children }: { children?: React.ReactNode }) {
  return <Image src="/img/default.png" fluid centered dimmer={children} />;
}

export function ItemCard({
  children,
  size = 'medium',
  href,
  actions,
  loading,
  image,
  centered,
  link,
}: {
  children?: React.ReactNode;
  actions?: React.ReactNode[];
  image?: React.ElementType;
  href?: string;
  loading?: boolean;
  size?: 'medium';
  centered?: boolean;
  link?: boolean;
}) {
  const Im = image;
  const [hover, setHover] = useState(false);
  const itemContext = useContext(ItemContext);

  return (
    <ItemContext.Provider value={{ ...itemContext, hover, loading }}>
      <Card
        onMouseEnter={useCallback(() => setHover(true), [])}
        onMouseLeave={useCallback(() => setHover(false), [])}
        centered={centered}
        link={link}
        className={classNames(`${size}-size`)}>
        <Dimmer.Dimmable dimmed={loading}>
          <Dimmer active={loading} inverted>
            <Loader inverted active={loading} />
          </Dimmer>
          <ItemCardActions>
            {href && (
              <Link href={href}>
                <a>
                  <Im />
                </a>
              </Link>
            )}
            {!!!href && <Im />}
            {actions}
          </ItemCardActions>
          {children}
        </Dimmer.Dimmable>
      </Card>
    </ItemContext.Provider>
  );
}

export default {};
