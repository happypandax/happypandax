import classNames from 'classnames';
import _ from 'lodash';
import { useCallback, useMemo } from 'react';
import { Divider, Popup, Segment } from 'semantic-ui-react';

import { ItemType } from '../../misc/enums';
import t from '../../misc/lang';
import {
  FieldPath,
  ItemSize,
  ServerGallery,
  ServerGrouping,
} from '../../misc/types';
import { GalleryCountLabel } from '../dataview/Common';
import GroupingDataTable from '../dataview/GroupingData';
import CardView from '../view/CardView';
import ListView from '../view/ListView';
import {
  ActivityLabel,
  FavoriteLabel,
  ItemCard,
  ItemCardImage,
  ItemLabel,
  ItemMenuLabel,
  ItemMenuLabelItem,
} from './';
import GalleryCard, { galleryCardDataFields } from './Gallery';
import { ItemCardContent, TranslucentLabel } from './index';

export type GroupingCardData = DeepPick<
  ServerGrouping,
  'id' | 'name' | 'profile' | 'gallery_count' | 'galleries'
>;

export const groupingCardDataFields: FieldPath<ServerGrouping>[] = [
  'name',
  'profile',
  'gallery_count',
  ...(galleryCardDataFields.map((f) => 'galleries.' + f) as any),
];

function GroupingMenu({}: { hasProgress: boolean; read: boolean }) {
  return (
    <ItemMenuLabel>
      <ItemMenuLabelItem icon="trash">{t`Delete`}</ItemMenuLabelItem>
    </ItemMenuLabel>
  );
}

function GroupingContent({
  data,
  horizontal,
}: {
  data: GroupingCardData;
  horizontal?: boolean;
}) {
  const onItemKey = useCallback((item: ServerGallery) => item.id, []);

  const View = horizontal ? ListView : CardView;

  return (
    <Segment basic>
      <GroupingDataTable data={data} className="no-margins" />
      <Divider />
      <View
        dynamicRowHeight
        className="no-padding-segment"
        items={data?.galleries}
        size={horizontal ? 'tiny' : 'small'}
        onItemKey={onItemKey}
        itemRender={GalleryCard}
      />
    </Segment>
  );
}

export function GroupingCard({
  size,
  data,
  fluid,
  draggable,
  disableModal,
  horizontal,
}: {
  size?: ItemSize;
  data: GroupingCardData;
  fluid?: boolean;
  draggable?: boolean;
  disableModal?: boolean;
  horizontal?: boolean;
}) {
  const is_series = (data?.gallery_count ?? 0) > 1;

  if (!is_series && data?.galleries?.[0]) {
    return (
      <GalleryCard
        size={size}
        data={data.galleries[0]}
        fluid={fluid}
        draggable={draggable}
        disableModal={disableModal}
        horizontal={horizontal}
      />
    );
  }

  const artists = _.sortedUniqBy(
    data?.galleries?.flatMap?.((g) => g?.artists ?? []) ?? [],
    (a) => a?.preferred_name?.name?.toLowerCase()
  );

  return (
    <Popup
      on="click"
      flowing
      as={Segment}
      color="teal"
      wide="very"
      position="bottom left"
      className="no-padding-segment modal"
      trigger={
        <ItemCard
          type={ItemType.Grouping}
          dragData={data}
          draggable={false}
          centered
          className={classNames({
            stacked: is_series,
            teal: is_series,
          })}
          link
          fluid={fluid}
          horizontal={horizontal}
          size={size}
          disableModal={true}
          labels={useMemo(
            () => [
              <ItemLabel key="fav" x="left" y="top">
                <FavoriteLabel />
              </ItemLabel>,
              <ItemLabel key="icons" x="right" y="top">
                {/* {!!data?.metatags?.inbox && <InboxIconLabel />} */}
                <ActivityLabel />
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
                <GroupingMenu />
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
          <ItemCardContent
            title={data?.name ?? ''}
            subtitle={artists.map((a) => (
              <span key={a.id}>{a.preferred_name.name}</span>
            ))}></ItemCardContent>
        </ItemCard>
      }>
      <GroupingContent horizontal={horizontal} data={data} />
    </Popup>
  );
}

export default GroupingCard;
