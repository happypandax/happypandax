import classNames from 'classnames';
import Link from 'next/link';
import React, { useContext, useMemo } from 'react';
import { useState, useCallback } from 'react';
import { useRef } from 'react';
import { useHover, useMouseHovered } from 'react-use';
import { Label, Modal, Popup } from 'semantic-ui-react';
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

const ItemContext = React.createContext({
  size: 'medium' as ItemSize,
  ActionContent: undefined as React.ElementType,
  Details: undefined as React.ElementType,
  labels: [] as React.ReactNode[],
  href: '',
  disableModal: false,
  onDetailsOpen: undefined as () => void,
  hover: false,
  loading: false,
  horizontal: false,
});

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
  size = 'tiny',
  basic = true,
  circular,
}: {
  children: React.ReactNode;
  size?: React.ComponentProps<typeof Label>['size'];
  basic?: React.ComponentProps<typeof Label>['basic'];
  circular?: boolean;
}) {
  return (
    <Label
      basic={basic}
      size={size}
      circular={circular}
      className="translucent-black">
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
    <TranslucentLabel size="mini" circular basic={false}>
      <Loader inline active size="mini" />
    </TranslucentLabel>
  );
}

function ItemCardLabels({ children }: { children: React.ReactNode }) {
  const itemContext = useContext(ItemContext);

  return (
    <>
      {!itemContext.horizontal && (
        <div className="card-content">{children}</div>
      )}
      {itemContext.horizontal && children}
    </>
  );
}

function ItemDetailsModal(props: React.ComponentProps<typeof Modal>) {
  return (
    <Modal {...props}>
      <Modal.Content>{props.children}</Modal.Content>
    </Modal>
  );
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
  const itemContext = useContext(ItemContext);
  const [detailsOpen, setDetailsOpen] = useState(false);

  const Details = itemContext.Details;

  const onDetailsClose = useCallback(() => setDetailsOpen(false), []);

  return (
    <Dimmer.Dimmable
      as={itemContext.horizontal && itemContext.href ? 'a' : Card.Content}
      onClick={useCallback(() => {
        if (!itemContext.horizontal) {
          setDetailsOpen(true);
          itemContext.onDetailsOpen?.();
        }
      }, [itemContext.horizontal])}
      className="content">
      {!!itemContext.Details &&
        !itemContext.horizontal &&
        !itemContext.disableModal && (
          <ItemDetailsModal
            open={detailsOpen}
            closeIcon
            dimmer="inverted"
            onClose={onDetailsClose}>
            <Details />
          </ItemDetailsModal>
        )}
      <Dimmer active={itemContext.horizontal && itemContext.hover} inverted>
        <itemContext.ActionContent />
      </Dimmer>
      {itemContext.horizontal && (
        <ItemCardLabels>{itemContext.labels}</ItemCardLabels>
      )}
      <Card.Header className="text-ellipsis card-header">{title}</Card.Header>
      {subtitle && <Card.Meta className="text-ellipsis">{subtitle}</Card.Meta>}
      {description && <Card.Description>{description}</Card.Description>}
    </Dimmer.Dimmable>
  );
}

export function ItemCardActionContentItem({
  children,
}: {
  children?: React.ReactNode;
}) {
  return <List.Item>{children}</List.Item>;
}

export function ItemCardActionContent({
  children,
}: {
  children?: React.ReactNode;
}) {
  const itemContext = useContext(ItemContext);

  return <List horizontal={itemContext.horizontal}>{children}</List>;
}

export function ItemCardImage({ children }: { children?: React.ReactNode }) {
  const itemContext = useContext(ItemContext);
  const [detailsOpen, setDetailsOpen] = useState(false);

  const Details = itemContext.Details;

  const onDetailsClose = useCallback(() => setDetailsOpen(false), []);

  return (
    <Image
      src="/img/default.png"
      fluid={!itemContext.horizontal}
      centered={!itemContext.horizontal}
      className={classNames({
        [`${itemContext.size}-size`]: itemContext.horizontal,
      })}
      onClick={useCallback(() => {
        if (itemContext.horizontal) {
          setDetailsOpen(true);
          itemContext.onDetailsOpen?.();
        }
      }, [itemContext.horizontal])}
      dimmer={{
        active: itemContext.hover && !itemContext.horizontal,
        inverted: true,
        children: (
          <>
            {!!itemContext.Details &&
              itemContext.horizontal &&
              !itemContext.disableModal && (
                <ItemDetailsModal
                  open={detailsOpen}
                  closeIcon
                  dimmer="inverted"
                  onClose={onDetailsClose}>
                  <Details />
                </ItemDetailsModal>
              )}
            {children}
          </>
        ),
      }}></Image>
  );
}

export function ItemCard({
  children,
  size,
  href,
  className,
  disableModal,
  details: Details,
  onDetailsOpen,
  labels,
  actionContent: ActionContent,
  loading,
  fluid,
  horizontal,
  image: Image,
  centered,
  link,
}: {
  children?: React.ReactNode;
  className?: string;
  labels?: React.ReactNode[];
  actionContent?: React.ElementType;
  details?: React.ElementType;
  image?: React.ElementType;
  href?: string;
  disableModal?: boolean;
  onDetailsOpen?: () => void;
  loading?: boolean;
  fluid?: boolean;
  horizontal?: boolean;
  size?: ItemSize;
  centered?: boolean;
  link?: boolean;
}) {
  const [hover, setHover] = useState(false);
  const itemContext = useContext(ItemContext);

  let itemSize = size ?? 'medium';

  const imageElement = horizontal ? (
    <Image />
  ) : (
    <Image>
      <ActionContent />
    </Image>
  );

  return (
    <ItemContext.Provider
      value={{
        ...itemContext,
        hover,
        href,
        disableModal,
        onDetailsOpen,
        Details,
        ActionContent,
        labels,
        loading,
        horizontal,
        size: itemSize,
      }}>
      <Card
        fluid={fluid}
        onMouseEnter={useCallback(() => setHover(true), [])}
        onMouseLeave={useCallback(() => setHover(false), [])}
        centered={centered}
        link={link}
        className={classNames({
          horizontal: horizontal,
          [`${itemSize}-size`]: !horizontal,
        })}>
        {}
        <Dimmer active={loading} inverted>
          <Loader inverted active={loading} />
        </Dimmer>
        {!horizontal && (
          <ItemCardLabels>
            {href && (
              <Link href={href}>
                <a>{imageElement}</a>
              </Link>
            )}
            {!!!href && imageElement}
            {labels}
          </ItemCardLabels>
        )}
        {horizontal && imageElement}
        {children}
      </Card>
    </ItemContext.Provider>
  );
}

export default {};
