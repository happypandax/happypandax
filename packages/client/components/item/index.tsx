import classNames from 'classnames';
import { useRouter } from 'next/dist/client/router';
import NextImage from 'next/image';
import Link from 'next/link';
import React, {
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
} from 'react';
import { useDrag } from 'react-dnd';
import { useSetRecoilState } from 'recoil';
import {
  Card,
  Dimmer,
  Header,
  Icon,
  Image,
  Label,
  List,
  Loader,
  Modal,
  Popup,
  Rating,
  Ref,
  Segment,
} from 'semantic-ui-react';

import { LibraryContext } from '../../client/context';
import { ItemType } from '../../misc/enums';
import {
  DragItemData,
  ItemSize,
  ServerItem,
  ServerItemWithProfile,
} from '../../misc/types';
import { AppState, LibraryState } from '../../state';
import styles from './Item.module.css';

const ItemContext = React.createContext({
  isDragging: false,
  openMenu: false,
  onMenuClose: undefined as () => void,
  size: 'medium' as ItemSize,
  ActionContent: undefined as React.ElementType,
  Details: undefined as React.ElementType,
  detailsData: undefined as PartialExcept<ServerItem, 'id'>,
  labels: [] as React.ReactNode[],
  href: '',
  disableModal: false,
  onDetailsOpen: undefined as () => void,
  hover: false,
  loading: false,
  horizontal: false,
});

export function QueueIconLabel() {
  return (
    <Icon
      className="book open"
      color="red"
      bordered
      inverted
      size="small"
      link
      title={`This item is in your reading queue`}
    />
  );
}

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
      title={`Saved for later`}
    />
  );
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
          <Icon name="eye" size="large" title={`This item is being read`} />
          <span>{Math.round(percent)}%</span>
        </TranslucentLabel>
      )}
      {!percent && (
        <Icon
          name="eye"
          bordered
          inverted
          size="small"
          color="orange"
          link
          title={`This item is being read`}
        />
      )}
    </>
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
  className,
  ...props
}: {
  children: React.ReactNode;
  circular?: boolean;
} & React.ComponentProps<typeof Label>) {
  return (
    <Label
      {...props}
      basic={basic}
      size={size}
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
}: {
  children: React.ReactNode | React.ReactNode[];
}) {
  const { openMenu, onMenuClose } = useContext(ItemContext);

  return (
    <Popup
      hoverable
      on="click"
      open={openMenu ? openMenu : undefined}
      hideOnScroll
      onClose={onMenuClose}
      position="right center"
      trigger={useMemo(
        () => (
          <Icon
            name="ellipsis vertical"
            bordered
            link
            inverted
            onClick={(e) => e.preventDefault()}
          />
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
  x?: 'left' | 'right' | 'center';
  y?: 'top' | 'bottom';
  children?: React.ReactNode;
}) {
  return (
    <div className={classNames('card-item above-dimmer', x, y)}>{children}</div>
  );
}

// https://github.com/Semantic-Org/Semantic-UI-React/issues/3950
export function FavoriteLabel({
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

export function ActivityLabel() {
  return (
    <TranslucentLabel floating size="mini" circular basic={false}>
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
  children,
}: {
  title: React.ReactNode;
  subtitle?: React.ReactNode;
  description?: React.ReactNode;
  children?: React.ReactNode;
}) {
  const itemContext = useContext(ItemContext);
  const [detailsOpen, setDetailsOpen] = useState(false);

  const setLibrarySidebarVisible = useSetRecoilState(
    LibraryState.sidebarVisible
  );
  const setLibrarySidebarData = useSetRecoilState(LibraryState.sidebarData);

  const Details = itemContext.Details;

  const onDetailsClose = useCallback(() => setDetailsOpen(false), []);

  const libraryContext = useContext(LibraryContext);

  const El = itemContext.horizontal && itemContext.href ? Link : React.Fragment;

  return (
    <>
      <El href={itemContext.horizontal ? itemContext.href : undefined} passHref>
        <Dimmer.Dimmable
          as={itemContext.horizontal && itemContext.href ? 'a' : Card.Content}
          onClick={useCallback(
            (ev) => {
              if (!itemContext.horizontal) {
                ev.preventDefault();
                if (libraryContext) {
                  ev.stopPropagation();
                  setLibrarySidebarData(itemContext.detailsData);
                  setLibrarySidebarVisible(true);
                } else {
                  setDetailsOpen(true);
                  itemContext.onDetailsOpen?.();
                }
              }
            },
            [itemContext.horizontal, itemContext.detailsData, libraryContext]
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
          <Dimmer active={itemContext.horizontal && itemContext.hover} inverted>
            {!!itemContext.ActionContent && <itemContext.ActionContent />}
          </Dimmer>
          {itemContext.horizontal && (
            <ItemCardLabels>{itemContext.labels}</ItemCardLabels>
          )}
          <Card.Header className="text-ellipsis card-header">
            {title}
          </Card.Header>
          {subtitle && (
            <Card.Meta className="text-ellipsis">{subtitle}</Card.Meta>
          )}
          {description && <Card.Description>{description}</Card.Description>}
          {!!children && <Card.Meta>{children}</Card.Meta>}
        </Dimmer.Dimmable>
      </El>
    </>
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

const defaultImage = '/img/default.png';

export function ItemCardImage({
  children,
  src,
}: {
  children?: React.ReactNode;
  src?: string | ServerItemWithProfile['profile'];
}) {
  const router = useRouter();
  const itemContext = useContext(ItemContext);
  const [detailsOpen, setDetailsOpen] = useState(false);

  const imgSrc = !src
    ? defaultImage
    : typeof src === 'string'
    ? src
    : src.data
    ? src.data
    : defaultImage;

  const [imageErr, setImageErr] = useState(false);

  const Details = itemContext.Details;

  const onDetailsClose = useCallback(() => setDetailsOpen(false), []);

  const setLibrarySidebarVisible = useSetRecoilState(
    LibraryState.sidebarVisible
  );

  const setLibrarySidebarData = useSetRecoilState(LibraryState.sidebarData);

  const libraryContext = useContext(LibraryContext);

  // const size = src && typeof src !== 'string' ? src.size : undefined;

  return (
    <Image
      // as={!src || typeof src === 'string' ? 'img' : SemanticNextImage}
      src={imageErr ? defaultImage : imgSrc}
      // width={size?.[0]}
      // height={size?.[1]}
      fluid={!itemContext.horizontal}
      centered={!itemContext.horizontal}
      className={classNames({
        [`${itemContext.size}-size`]: itemContext.horizontal,
      })}
      onClick={useCallback(
        (ev) => {
          if (itemContext.horizontal) {
            ev.preventDefault();
            if (libraryContext) {
              ev.stopPropagation();
              setLibrarySidebarData(itemContext.detailsData);
              setLibrarySidebarVisible(true);
            } else {
              setDetailsOpen(true);
              itemContext.onDetailsOpen?.();
            }
          }
        },
        [itemContext.horizontal, itemContext.detailsData, libraryContext]
      )}
      onError={useCallback(() => {
        setImageErr(true);
      }, [imgSrc])}
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
                  <Details data={itemContext.detailsData} />
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
  draggable,
  details: Details,
  detailsData,
  onDetailsOpen,
  labels,
  actionContent: ActionContent,
  loading,
  fluid,
  horizontal,
  image: Image,
  centered,
  dragData,
  link,
  type,
}: {
  children?: React.ReactNode;
  className?: string;
  type: ItemType;
  labels?: React.ReactNode[];
  actionContent?: React.ElementType;
  details?: React.ElementType<{ data: PartialExcept<ServerItem, 'id'> }>;
  detailsData?: PartialExcept<ServerItem, 'id'>;
  image?: React.ElementType;
  href?: string;
  disableModal?: boolean;
  onDetailsOpen?: () => void;
  loading?: boolean;
  fluid?: boolean;
  draggable?: boolean;
  horizontal?: boolean;
  dragData?: DragItemData['data'];
  size?: ItemSize;
  centered?: boolean;
  link?: boolean;
}) {
  const [hover, setHover] = useState(false);
  const [openMenu, setOpenMenu] = useState(false);
  const itemContext = useContext(ItemContext);
  const setDrawerOpen = useSetRecoilState(AppState.drawerOpen);

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

  useEffect(() => {
    if (isDragging) {
      setDrawerOpen(true);
    }
  }, [isDragging]);

  let itemSize = size ?? 'medium';

  const imageElement = Image ? (
    horizontal ? (
      <Image />
    ) : (
      <Image>{!!ActionContent && <ActionContent />}</Image>
    )
  ) : undefined;

  const onMenuClose = useCallback(() => {
    setOpenMenu(false);
  }, []);

  return (
    <ItemContext.Provider
      value={{
        ...itemContext,
        isDragging,
        onMenuClose,
        hover,
        href,
        disableModal,
        openMenu,
        onDetailsOpen,
        Details,
        detailsData,
        ActionContent,
        labels,
        loading,
        horizontal,
        size: itemSize,
      }}>
      <Ref innerRef={dragRef}>
        <Card
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
          className={classNames({
            dragging: isDragging,
            horizontal: horizontal,
            [`${itemSize}-size`]: !horizontal,
          })}
          onContextMenu={(e) => {
            e.preventDefault();
            setOpenMenu(true);
          }}>
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
              {!!!href && !!imageElement && imageElement}
              {labels}
            </ItemCardLabels>
          )}
          {horizontal && !!imageElement && imageElement}
          {children}
        </Card>
      </Ref>
    </ItemContext.Provider>
  );
}

export default {};
