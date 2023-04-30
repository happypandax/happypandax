import classNames from 'classnames';
import NextImage from 'next/image';
import Link from 'next/link';
import React, {
  useCallback,
  useContext,
  useEffect,
  useImperativeHandle,
  useMemo,
  useRef,
  useState,
} from 'react';
import { useDrag } from 'react-dnd';
import { useRecoilValue, useSetRecoilState } from 'recoil';
import {
  Button,
  Card,
  Dimmer,
  Header,
  Icon,
  Image as ImageComponent,
  Label,
  List,
  Loader,
  Modal,
  Placeholder,
  Popup,
  Ref,
  Segment,
  SemanticCOLORS,
} from 'semantic-ui-react';

import { useItemActivity } from '../../client/activity';
import {
  DataContext,
  DataContextT,
  ItemContext,
  useSidebarDetailsContext,
} from '../../client/context';
import { useAddToQueue, useImage } from '../../client/hooks/item';
import t from '../../client/lang';
import { ItemType } from '../../shared/enums';
import {
  DragItemData,
  ItemSize,
  ServerItem,
  ServerItemWithProfile,
} from '../../shared/types';
import { maskText } from '../../shared/utility';
import { AppState, LibraryState } from '../../state';
import { ActivityList } from '../misc/ActivityList';
import { ModalWithBack } from '../misc/BackSupport';
import { GalleryCardData } from './Gallery';
import { GroupingCardData } from './Grouping';
import styles from './Item.module.css';

export function itemText(type: ItemType): string {
  let txt = undefined;
  switch (type) {
    case ItemType.Gallery: {
      txt = t`Gallery`;
      break;
    }
    case ItemType.Collection: {
      txt = t`Collection`;
      break;
    }
    case ItemType.Parody: {
      txt = t`Parody`;
      break;
    }
    case ItemType.Artist: {
      txt = t`Artist`;
      break;
    }
    case ItemType.Language: {
      txt = t`Language`;
      break;
    }
    case ItemType.Circle: {
      txt = t`Circle`;
      break;
    }
    case ItemType.Grouping: {
      txt = t`Series`;
      break;
    }
    case ItemType.Category: {
      txt = t`Category`;
      break;
    }
  }

  return txt;
}

export function itemColor(type: ItemType) {
  let color: SemanticCOLORS = undefined;
  switch (type) {
    case ItemType.Gallery: {
      break;
    }
    case ItemType.Collection: {
      color = 'violet';
      break;
    }
    case ItemType.Parody: {
      color = 'violet';
      break;
    }
    case ItemType.Artist: {
      color = 'blue';
      break;
    }
    case ItemType.Language: {
      color = 'blue';
      break;
    }
    case ItemType.Circle: {
      color = 'teal';
      break;
    }
    case ItemType.Grouping: {
      color = 'teal';
      break;
    }
    case ItemType.Category: {
      color = 'black';
      break;
    }
  }

  return color;
}

export function AddToQueueButton<T extends ItemType>({
  data,
  itemType,
}: {
  data: T extends ItemType.Gallery ? GalleryCardData : GroupingCardData;
  itemType: T;
}) {
  const { exists, toggle } = useAddToQueue<T>({ data, itemType });

  return (
    <Button color="red" size="mini" onClick={toggle}>
      <Icon name={exists ? 'bookmark' : 'bookmark outline'} />
      {t`Queue`}
    </Button>
  );
}

export function IconItemLabel(props: React.ComponentProps<typeof Icon>) {
  const itemContext = useContext(ItemContext);

  return (
    <Icon
      bordered
      inverted
      link
      size={itemContext?.size === 'mini' ? 'tiny' : 'small'}
      {...props}
    />
  );
}

export function QueueIconLabel() {
  return (
    <IconItemLabel
      className="bookmark"
      color="red"
      title={`This item is in your reading queue`}
    />
  );
}

export function InboxIconLabel() {
  return <IconItemLabel name="inbox" title={`This item is in your inbox`} />;
}

export function ReadLaterIconLabel() {
  return <IconItemLabel name="bookmark" title={`Saved for later`} />;
}

export function ReadingIconLabel({ percent }: { percent?: number }) {
  return (
    <>
      {!!percent && (
        <TranslucentLabel
          className={classNames(styles.reading_icon_label)}
          size="mini"
          basic
          title={`This item is being read`}>
          <Icon name="eye" title={`This item is being read`} />
          <span>{Math.round(percent)}%</span>
        </TranslucentLabel>
      )}
      {!percent && (
        <IconItemLabel
          name="eye"
          color="orange"
          title={`This item is being read`}
        />
      )}
    </>
  );
}

export function UnreadIconLabel() {
  return (
    <IconItemLabel
      name="eye slash outline"
      title={`This item has not been read yet`}
    />
  );
}

export function TranslucentLabel({
  children,
  size = 'tiny',
  basic = true,
  circular,
  className,
  ...props
}: {
  children: React.ReactNode;
  circular?: boolean;
} & React.ComponentProps<typeof Label>) {
  const itemContext = useContext(ItemContext);

  return (
    <Label
      {...props}
      basic={basic}
      size={itemContext?.size === 'mini' ? 'mini' : size}
      circular={circular}
      className={classNames('translucent-black', className)}>
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
  trigger,
  onClose,
  onOpen,
  open,
}: {
  children: React.ReactNode | React.ReactNode[];
  trigger?: React.ComponentProps<typeof Popup>['trigger'];
  open?: React.ComponentProps<typeof Popup>['open'];
  onClose?: React.ComponentProps<typeof Popup>['onClose'];
  onOpen?: React.ComponentProps<typeof Popup>['onOpen'];
}) {
  const { size } = useContext(ItemContext);

  return (
    <Popup
      hoverable
      onOpen={useCallback(
        (e, d) => {
          e?.preventDefault?.();
          e?.stopPropagation?.();
          onOpen?.(e, d);
        },
        [onOpen]
      )}
      on="click"
      open={open}
      hideOnScroll
      onClose={useCallback(
        (e, d) => {
          e?.preventDefault?.();
          e?.stopPropagation?.();
          onClose?.(e, d);
        },
        [onClose]
      )}
      position="right center"
      trigger={useMemo(
        () =>
          trigger ? (
            trigger
          ) : (
            <IconItemLabel
              name="ellipsis vertical"
              size={
                (['mini', 'tiny'] as ItemSize[]).includes(size)
                  ? 'small'
                  : undefined
              }
              onClick={(e) => {
                e.preventDefault();
                onOpen?.(e, { open: false });
              }}
            />
          ),
        [trigger]
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
  x?: 'left' | 'right' | 'center';
  y?: 'top' | 'bottom';
  children?: React.ReactNode;
}) {
  return (
    <div className={classNames('card-item above-dimmer', x, y)}>{children}</div>
  );
}

export function ActivityLabel({
  type,
  data,
  parentRef,
}: {
  type: ItemType;
  data: DeepPick<ServerItem, 'id'>;
  parentRef?: React.RefObject<HTMLElement>;
}) {
  const [open, setOpen] = useState(false);
  const activities = useItemActivity(
    { type, id: data?.id },
    { ref: parentRef, interval: open ? 1000 : undefined }
  );

  return activities.length ? (
    <Popup
      size="tiny"
      onOpen={() => setOpen(true)}
      onClose={() => setOpen(false)}
      trigger={
        <TranslucentLabel floating size="mini" circular basic={false}>
          <Loader inline active indeterminate className="double" size="mini" />
        </TranslucentLabel>
      }>
      <ActivityList data={activities} />
    </Popup>
  ) : null;
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
    <ModalWithBack {...props}>
      <Modal.Content>{props.children}</Modal.Content>
    </ModalWithBack>
  );
}

function AlternativeContent(): any {
  const itemContext = useContext(ItemContext);

  return itemContext.AlternativeContent ? (
    <itemContext.AlternativeContent />
  ) : null;
}

function AlternativeDimmer() {
  const itemContext = useContext(ItemContext);

  return (
    <Dimmer active={itemContext.alternative} className="no-padding-segment">
      <AlternativeContent />
    </Dimmer>
  );
}

export function ItemCardContent({
  title,
  subtitle,
  description,
  children,
}: {
  title: React.ReactNode;
  subtitle?: React.ReactNode;
  description?: React.ReactNode;
  children?: React.ReactNode;
}) {
  const itemContext = useContext(ItemContext);
  const [detailsOpen, setDetailsOpen] = useState(false);
  const blur = useRecoilValue(AppState.blur);

  const setLibrarySidebarVisible = useSetRecoilState(
    LibraryState.sidebarVisible
  );
  const setLibrarySidebarData = useSetRecoilState(LibraryState.sidebarData);

  const Details = itemContext.Details;

  const onDetailsClose = useCallback(() => setDetailsOpen(false), []);

  const sidebarDetailsContext = useSidebarDetailsContext();

  const El = itemContext.horizontal && itemContext.href ? Link : React.Fragment;

  return (
    <El
      href={itemContext.horizontal ? itemContext.href : undefined}
      passHref
      legacyBehavior>
      <Dimmer.Dimmable
        as={itemContext.horizontal && itemContext.href ? 'a' : Card.Content}
        onClick={useCallback(
          (ev) => {
            if (!itemContext.horizontal) {
              ev.preventDefault();
              if (sidebarDetailsContext && itemContext.detailsData) {
                ev.stopPropagation();
                setLibrarySidebarData(itemContext.detailsData);
                setLibrarySidebarVisible(true);
              } else {
                setDetailsOpen(true);
                itemContext.onDetailsOpen?.();
              }
            }
          },
          [
            itemContext.horizontal,
            itemContext.detailsData,
            sidebarDetailsContext,
          ]
        )}
        className="content">
        {!!itemContext.Details &&
          !itemContext.horizontal &&
          !itemContext.disableModal && (
            <ItemDetailsModal
              open={detailsOpen}
              closeIcon
              dimmer="inverted"
              onClose={onDetailsClose}>
              <Details data={itemContext.detailsData} />
            </ItemDetailsModal>
          )}
        {itemContext.horizontal && <AlternativeDimmer />}
        <Dimmer
          active={itemContext.horizontal && itemContext.hover}
          inverted
          className="no-padding-segment">
          {!!itemContext.ActionContent && <itemContext.ActionContent />}
        </Dimmer>
        {itemContext.horizontal && (
          <ItemCardLabels>{itemContext.labels}</ItemCardLabels>
        )}
        <Card.Header className="text-ellipsis text-center card-header">
          {blur && typeof title === 'string' ? maskText(title) : title}
        </Card.Header>
        {subtitle && (
          <Card.Meta className="text-ellipsis text-center card-meta">
            {blur && typeof subtitle === 'string'
              ? maskText(subtitle)
              : subtitle}
          </Card.Meta>
        )}
        {description && (
          <Card.Description>
            {blur && typeof description === 'string'
              ? maskText(description)
              : description}
          </Card.Description>
        )}
        {!!children && <Card.Meta>{children}</Card.Meta>}
      </Dimmer.Dimmable>
    </El>
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

  return (
    <List horizontal={itemContext.horizontal}>
      {itemContext?.size === 'mini' && !itemContext.showMiniActionContent
        ? null
        : children}
    </List>
  );
}

export function ItemCardHorizontalDetailContent({
  children,
  tertiary = true,
  middle = true,
  ...props
}: {
  middle?: boolean;
  children: React.ReactNode;
} & React.ComponentProps<typeof Segment>) {
  return (
    <Segment
      {...props}
      className={classNames(
        'small-padding-segment no-margins',
        props.className
      )}>
      {middle ? <div className="centered-container">{children}</div> : children}
    </Segment>
  );
}

// TODO: any way to add this? any benefits?
function SemanticNextImage({
  children,
  width,
  height,
  ...props
}: {
  children: React.ReactNode;
  width: number;
  height: number;
}) {
  let imgProps: any = {};
  const children2 = React.Children.toArray(children).filter((c: any) => {
    if (c?.type === 'img') {
      imgProps = c.props;
    } else {
      return c;
    }
  });

  return (
    <div {...props}>
      {children2}
      <NextImage {...imgProps} src={imgProps?.src} />
    </div>
  );
}

export function ItemCardImage({
  children,
  src: initialSrc,
}: {
  children?: React.ReactNode;
  src?: string | ServerItemWithProfile['profile'];
}) {
  const itemContext = useContext(ItemContext);
  const [detailsOpen, setDetailsOpen] = useState(false);
  const blur = useRecoilValue(AppState.blur);
  const { src } = useImage(initialSrc);

  const Details = itemContext.Details;

  const onDetailsClose = useCallback(() => setDetailsOpen(false), []);

  const setLibrarySidebarVisible = useSetRecoilState(
    LibraryState.sidebarVisible
  );

  const setLibrarySidebarData = useSetRecoilState(LibraryState.sidebarData);

  const sidebarDetailsContext = useSidebarDetailsContext();

  // const size = src && typeof src !== 'string' ? src.size : undefined;

  return (
    <ImageComponent
      // as={!src || typeof src === 'string' ? 'img' : SemanticNextImage}
      src={src}
      // width={size?.[0]}
      // height={size?.[1]}
      alt="item cover"
      fluid={!itemContext.horizontal}
      centered={!itemContext.horizontal}
      className={classNames({
        [`${itemContext.size}-size`]: itemContext.horizontal,
        blur: blur,
      })}
      onClick={useCallback(
        (ev) => {
          if (itemContext.horizontal) {
            ev.preventDefault();
            if (sidebarDetailsContext && itemContext.detailsData) {
              ev.stopPropagation();
              setLibrarySidebarData(itemContext.detailsData);
              setLibrarySidebarVisible(true);
            } else {
              setDetailsOpen(true);
              itemContext.onDetailsOpen?.();
            }
          }
        },
        [itemContext.horizontal, itemContext.detailsData, sidebarDetailsContext]
      )}
      dimmer={{
        active:
          (itemContext.hover || itemContext.alternative) &&
          !itemContext.horizontal,
        inverted: itemContext.alternative ? false : true,
        children: itemContext.alternative ? (
          <AlternativeContent />
        ) : (
          <>
            {!!itemContext.Details &&
              itemContext.horizontal &&
              !itemContext.disableModal && (
                <ItemDetailsModal
                  open={detailsOpen}
                  closeIcon
                  dimmer="inverted"
                  onClose={onDetailsClose}>
                  <Details data={itemContext.detailsData} />
                </ItemDetailsModal>
              )}
            {children}
          </>
        ),
      }}></ImageComponent>
  );
}

export const ItemCard = React.forwardRef(
  (
    {
      children,
      size = 'medium',
      href,
      className,
      disableModal,
      draggable,
      details: Details,
      detailsData,
      onDetailsOpen,
      labels,
      actionContent: ActionContent,
      horizontalDetailContent: HorizontalDetailContent,
      horizontalDetailPosition = 'right',
      loading,
      alternative,
      hideLabel,
      showMiniActionContent,
      alternativeContent: AlternativeContentComponent,
      fluid,
      horizontal,
      image: Image,
      centered,
      dragData,
      link,
      type,
      dataContext,
      ...props
    }: {
      children?: React.ReactNode;
      className?: string;
      type: ItemType;
      labels?: React.ReactNode;
      actionContent?: React.ElementType;
      horizontalDetailContent?: React.ElementType;
      details?: React.ElementType<{ data: PartialExcept<ServerItem, 'id'> }>;
      detailsData?: PartialExcept<ServerItem, 'id'>;
      image?: React.ElementType;
      href?: string;
      disableModal?: boolean;
      onDetailsOpen?: () => void;
      hideLabel?: boolean;
      showMiniActionContent?: boolean;
      horizontalDetailPosition?: 'left' | 'right';
      loading?: boolean;
      alternative?: boolean;
      alternativeContent?: React.ElementType;
      fluid?: boolean;
      draggable?: boolean;
      horizontal?: boolean;
      dragData?: DragItemData['data'];
      size?: ItemSize;
      centered?: boolean;
      link?: boolean;
      dataContext?: DataContextT;
    } & React.ComponentProps<typeof Card>,
    forwardRef
  ) => {
    const [hover, setHover] = useState(false);
    const itemContext = useContext(ItemContext);
    const setDrawerOpen = useSetRecoilState(AppState.drawerOpen);
    const ref = useRef();

    const [{ isDragging }, dragRef] = useDrag(
      () => ({
        type: type.toString(),
        item: {
          data: dragData,
        } as DragItemData,
        canDrag: (monitor) => !!draggable,
        collect: (monitor) => ({
          isDragging: !!monitor.isDragging(),
        }),
      }),
      [dragData, draggable]
    );

    useImperativeHandle(forwardRef, () => ref.current);
    useImperativeHandle(dragRef, () => ref.current);

    useEffect(() => {
      if (isDragging) {
        setDrawerOpen(true);
      }
    }, [isDragging]);

    let itemSize = size ?? 'medium';

    const labelContent = hideLabel ? null : labels;

    const imageElement = Image ? (
      horizontal ? (
        <Image />
      ) : (
        <Image>{!!ActionContent && <ActionContent />}</Image>
      )
    ) : undefined;

    const el = (
      <ItemContext.Provider
        value={{
          ...itemContext,
          isDragging,
          hover,
          href,
          disableModal,
          showMiniActionContent,
          alternative,
          onDetailsOpen,
          Details,
          detailsData,
          AlternativeContent: AlternativeContentComponent,
          ActionContent,
          labels: labelContent,
          loading,
          horizontal,
          size: itemSize,
        }}>
        <Ref innerRef={ref}>
          <Card
            {...props}
            fluid={fluid}
            as={Segment}
            // stacked
            onMouseEnter={useCallback(() => setHover(true), [])}
            onMouseLeave={useCallback(() => setHover(false), [])}
            centered={centered}
            link={link ?? !!href}
            style={
              isDragging
                ? {
                    opacity: 0.5,
                  }
                : {}
            }
            className={classNames(
              className,
              {
                dragging: isDragging,
                horizontal: horizontal,
                [`${itemSize}-size`]: !horizontal,
              },
              {
                [`${itemSize}-size`]:
                  horizontal &&
                  (['mini', 'tiny', 'small'] as ItemSize[]).includes(itemSize),
              }
            )}
            onContextMenu={(e) => {
              e.preventDefault();
              setOpenMenu(true);
            }}>
            <Dimmer active={loading} inverted>
              <Loader inverted active={loading} />
            </Dimmer>
            {!horizontal && (
              <ItemCardLabels>
                {href && <Link href={href}>{imageElement}</Link>}
                {!!!href && !!imageElement && imageElement}
                {labelContent}
              </ItemCardLabels>
            )}
            {horizontal &&
              HorizontalDetailContent &&
              horizontalDetailPosition == 'left' && <HorizontalDetailContent />}
            {horizontal && !!imageElement && imageElement}
            {children}
            {horizontal &&
              HorizontalDetailContent &&
              horizontalDetailPosition == 'right' && (
                <HorizontalDetailContent />
              )}
          </Card>
        </Ref>
      </ItemContext.Provider>
    );

    if (dataContext) {
      return (
        <DataContext.Provider value={dataContext}>{el}</DataContext.Provider>
      );
    }

    return el;
  }
);

export function PlaceholderItemCard({
  size,
  fluid,
  horizontal,
  centered = true,
  type = ItemType.Gallery,
  ...props
}: {
  size?: ItemSize;
  fluid?: boolean;
  centered?: boolean;
  type?: ItemType;
  horizontal?: boolean;
} & Omit<React.ComponentProps<typeof ItemCard>, 'type'>) {
  return (
    <ItemCard
      {...props}
      type={type}
      draggable={false}
      centered={centered}
      fluid={fluid}
      horizontal={horizontal}
      size={size}
      disableModal={true}
      image={useCallback(
        ({ children }: { children?: React.ReactNode }) => (
          <ItemCardImage src="/img/default.png">{children}</ItemCardImage>
        ),
        []
      )}>
      <Placeholder>
        <Placeholder.Header>
          <Placeholder.Line />
        </Placeholder.Header>
        <Placeholder.Line />
      </Placeholder>
    </ItemCard>
  );
}

export default {};
