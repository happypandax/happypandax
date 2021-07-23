import { useCallback, useMemo } from 'react';
import { Button, Icon } from 'semantic-ui-react';

import { ItemType } from '../misc/enums';
import t from '../misc/lang';
import { ItemSize, ServerGallery, ServerItem } from '../misc/types';
import {
  GroupingNumberLabel,
  LanguageLabel,
  PageCountLabel,
  ReadCountLabel,
  StatusLabel,
} from './data/Common';
import { GalleryDataTable } from './DataTable';
import {
  HeartIconLabel,
  InboxIconLabel,
  ItemCard,
  ItemCardActionContent,
  ItemCardActionContentItem,
  ItemCardContent,
  ItemCardImage,
  ItemLabel,
  ItemMenuLabel,
  ItemMenuLabelItem,
  ProgressLabel,
  ReadingIconLabel,
  ReadLaterIconLabel,
  TranslucentLabel,
  UnreadIconLabel,
} from './Item';

function ReadButton() {
  return (
    <Button primary size="mini">
      <Icon name="envelope open outline" />
      {t`Read`}
    </Button>
  );
}

function SaveForLaterButton() {
  return (
    <Button size="mini">
      <Icon name="bookmark outline" />
      {t`Save for later`}
    </Button>
  );
}

function GalleryCardMenu() {
  return (
    <ItemMenuLabel>
      <ItemMenuLabelItem icon="envelope open outline">{t`Read`}</ItemMenuLabelItem>
      <ItemMenuLabelItem icon="play">{t`Continue reading`}</ItemMenuLabelItem>
    </ItemMenuLabel>
  );
}

export type GalleryCardData = DeepPick<
  ServerGallery,
  | 'id'
  | 'preferred_title.name'
  | 'artists.[].preferred_name.name'
  | 'page_count'
  | 'language.code'
>;

export function GalleryCard({
  size,
  data,
  fluid,
  draggable = true,
  disableModal,
  details = GalleryDataTable,
  onDetailsOpen,
  horizontal,
}: {
  size?: ItemSize;
  data: GalleryCardData;
  fluid?: boolean;
  draggable?: boolean;
  disableModal?: boolean;
  details?: React.ElementType<{ data: PartialExcept<ServerItem, 'id'> }>;
  onDetailsOpen?: () => void;
  horizontal?: boolean;
}) {
  return (
    <ItemCard
      type={ItemType.Gallery}
      dragData={data}
      draggable={draggable}
      centered
      link
      fluid={fluid}
      horizontal={horizontal}
      size={size}
      details={details}
      detailsData={data}
      disableModal={disableModal}
      onDetailsOpen={onDetailsOpen}
      labels={useMemo(
        () => [
          <ItemLabel x="left" y="top">
            <HeartIconLabel />
            {!!data?.number && data?.number > 0 && (
              <GroupingNumberLabel as={TranslucentLabel}>
                {data?.number}
              </GroupingNumberLabel>
            )}
          </ItemLabel>,
          <ItemLabel x="right" y="top">
            {!!data?.metatags?.inbox && <InboxIconLabel />}
            {!data?.metatags?.read && <UnreadIconLabel />}
            {!!data?.metatags?.readlater && <ReadLaterIconLabel />}
            {!!data?.progress && !data?.progress?.end && (
              <ReadingIconLabel percent={data?.progress?.percent} />
            )}
            <ProgressLabel />
          </ItemLabel>,
          <ItemLabel x="right" y="bottom">
            {horizontal && <StatusLabel as={TranslucentLabel} />}
            {horizontal && <ReadCountLabel as={TranslucentLabel} />}
            {horizontal && <LanguageLabel as={TranslucentLabel} />}
            {horizontal && <PageCountLabel as={TranslucentLabel} />}
            {!horizontal && !!data.language.code && (
              <TranslucentLabel>
                {data.language.code.toUpperCase()}
              </TranslucentLabel>
            )}
            {!horizontal && (
              <TranslucentLabel circular>{data.page_count}</TranslucentLabel>
            )}
            <GalleryCardMenu />
          </ItemLabel>,
        ],
        [horizontal]
      )}
      actionContent={useCallback(
        () => (
          <ItemCardActionContent>
            <ItemCardActionContentItem>
              <ReadButton />
            </ItemCardActionContentItem>
            <ItemCardActionContentItem>
              <SaveForLaterButton />
            </ItemCardActionContentItem>
          </ItemCardActionContent>
        ),
        []
      )}
      image={useCallback(
        ({ children }: { children?: React.ReactNode }) => (
          <ItemCardImage>{children}</ItemCardImage>
        ),
        []
      )}>
      <ItemCardContent
        title={data?.preferred_title?.name ?? ''}
        subtitle={data?.artists.map((a) => (
          <span>{a.preferred_name.name}</span>
        ))}>
        <ReadCountLabel />
      </ItemCardContent>
    </ItemCard>
  );
}

export default GalleryCard;
