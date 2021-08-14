import { useCallback, useMemo } from 'react';

import { ItemType } from '../../misc/enums';
import t from '../../misc/lang';
import { FieldPath, ItemSize, ServerPage } from '../../misc/types';
import { PageNumberLabel } from '../data/Common';
import {
  FavoriteLabel,
  InboxIconLabel,
  ItemCard,
  ItemCardImage,
  ItemLabel,
  ItemMenuLabel,
  ItemMenuLabelItem,
  ProgressLabel,
} from '../Item';

export type PageCardData = DeepPick<
  ServerPage,
  | 'id'
  | 'profile'
  | 'gallery_id'
  | 'number'
  | 'metatags.inbox'
  | 'metatags.favorite'
>;

export const pageCardDataFields: FieldPath<ServerPage>[] = [
  'profile',
  'gallery_id',
  'number',
  'metatags.*',
];

function PageMenu({}: { hasProgress: boolean; read: boolean }) {
  return (
    <ItemMenuLabel>
      <ItemMenuLabelItem icon="trash">{t`Delete`}</ItemMenuLabelItem>
    </ItemMenuLabel>
  );
}

export function PageCard({
  size,
  data,
  fluid,
  draggable,
  disableModal,
  horizontal,
}: {
  size?: ItemSize;
  data: PageCardData;
  fluid?: boolean;
  draggable?: boolean;
  disableModal?: boolean;
  horizontal?: boolean;
}) {
  return (
    <ItemCard
      type={ItemType.Page}
      dragData={data}
      href={`/item/gallery/${data?.gallery_id}/page/${data?.number}`}
      draggable={draggable}
      centered
      link
      fluid={fluid}
      horizontal={horizontal}
      size={size}
      detailsData={data}
      disableModal={disableModal}
      labels={useMemo(
        () => [
          <ItemLabel x="left" y="top">
            <FavoriteLabel />
          </ItemLabel>,
          <ItemLabel x="right" y="top">
            {!!data?.metatags?.inbox && <InboxIconLabel />}
            <ProgressLabel />
          </ItemLabel>,
          <ItemLabel x="center" y="bottom">
            {data?.number !== undefined && (
              <PageNumberLabel>{data.number}</PageNumberLabel>
            )}
          </ItemLabel>,
          <ItemLabel x="right" y="bottom">
            <PageMenu />
          </ItemLabel>,
        ],
        [horizontal, data]
      )}
      image={useCallback(
        ({ children }: { children?: React.ReactNode }) => (
          <ItemCardImage src={data?.profile}>{children}</ItemCardImage>
        ),
        [data.profile]
      )}></ItemCard>
  );
}

export default PageCard;
