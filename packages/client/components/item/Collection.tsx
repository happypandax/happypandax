import { useCallback, useMemo } from 'react';

import t from '../../client/lang';
import { ItemType } from '../../shared/enums';
import { FieldPath, ItemSize, ServerCollection } from '../../shared/types';
import { FavoriteLabel, GalleryCountLabel } from '../dataview/Common';
import {
  ActivityLabel,
  InboxIconLabel,
  ItemCard,
  ItemCardImage,
  ItemLabel,
  ItemMenuLabel,
  ItemMenuLabelItem,
} from './';
import { ItemCardContent, TranslucentLabel } from './index';

export type CollectionCardData = DeepPick<
  ServerCollection,
  | 'id'
  | 'name'
  | 'profile'
  | 'gallery_count'
  | 'metatags.inbox'
  | 'metatags.favorite'
>;

export const collectionCardDataFields: FieldPath<ServerCollection>[] = [
  'name',
  'profile',
  'gallery_count',
  'metatags.*',
];

export function CollectionMenu({
  trigger,
}: {
  trigger?: React.ComponentProps<typeof ItemMenuLabel>['trigger'];
}) {
  return (
    <ItemMenuLabel trigger={trigger}>
      <ItemMenuLabelItem icon="trash">{t`Delete`}</ItemMenuLabelItem>
    </ItemMenuLabel>
  );
}

export function CollectionCard({
  size,
  data,
  fluid,
  draggable,
  disableModal,
  horizontal,
}: {
  size?: ItemSize;
  data: CollectionCardData;
  fluid?: boolean;
  draggable?: boolean;
  disableModal?: boolean;
  horizontal?: boolean;
}) {
  return (
    <ItemCard
      type={ItemType.Collection}
      dragData={data}
      href={`/item/collection/${data?.id}`}
      draggable={draggable}
      centered
      className="piled"
      link
      fluid={fluid}
      horizontal={horizontal}
      size={size}
      detailsData={data}
      disableModal={disableModal}
      labels={useMemo(
        () => [
          <ItemLabel key="fav" x="left" y="top">
            <FavoriteLabel />
          </ItemLabel>,
          <ItemLabel key="icons" x="right" y="top">
            {!!data?.metatags?.inbox && <InboxIconLabel />}
            <ActivityLabel type={ItemType.Collection} data={data} />
          </ItemLabel>,
          <ItemLabel key="menu" x="right" y="bottom">
            {horizontal && (
              <GalleryCountLabel as={TranslucentLabel}>
                {data?.gallery_count}
              </GalleryCountLabel>
            )}
            {!horizontal && (
              <TranslucentLabel circular>
                {data?.gallery_count}
              </TranslucentLabel>
            )}
            <CollectionMenu />
          </ItemLabel>,
        ],
        [horizontal, data]
      )}
      image={useCallback(
        ({ children }: { children?: React.ReactNode }) => (
          <ItemCardImage src={data?.profile}>{children}</ItemCardImage>
        ),
        [data.profile]
      )}
    >
      <ItemCardContent title={data?.name ?? ''}></ItemCardContent>
    </ItemCard>
  );
}

export default CollectionCard;
