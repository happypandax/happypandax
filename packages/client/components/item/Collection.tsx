import { useCallback, useMemo } from 'react';

import { ItemType } from '../../misc/enums';
import t from '../../misc/lang';
import { FieldPath, ItemSize, ServerCollection } from '../../misc/types';
import {
  ActivityLabel,
  FavoriteLabel,
  InboxIconLabel,
  ItemCard,
  ItemCardImage,
  ItemLabel,
  ItemMenuLabel,
  ItemMenuLabelItem,
} from './';
import { ItemCardContent } from './index';

export type CollectionCardData = DeepPick<
  ServerCollection,
  'id' | 'name' | 'profile' | 'metatags.inbox' | 'metatags.favorite'
>;

export const collectionCardDataFields: FieldPath<ServerCollection>[] = [
  'name',
  'profile',
  'metatags.*',
];

function CollectionMenu({}: { hasProgress: boolean; read: boolean }) {
  return (
    <ItemMenuLabel>
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
      type={ItemType.Page}
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
            <ActivityLabel />
          </ItemLabel>,
          <ItemLabel key="menu" x="right" y="bottom">
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
      )}>
      <ItemCardContent title={data?.name ?? ''}></ItemCardContent>
    </ItemCard>
  );
}

export default CollectionCard;
