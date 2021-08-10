import Link from 'next/link';
import { useCallback, useMemo } from 'react';
import { Button, Icon } from 'semantic-ui-react';

import { ItemType } from '../misc/enums';
import t from '../misc/lang';
import { FieldPath, ItemSize, ServerGallery, ServerItem } from '../misc/types';
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

export type GalleryCardData = DeepPick<
  ServerGallery,
  | 'id'
  | 'preferred_title.name'
  | 'artists.[].id'
  | 'artists.[].preferred_name.name'
  | 'profile'
  | 'number'
  | 'metatags.favorite'
  | 'metatags.read'
  | 'metatags.readlater'
  | 'metatags.inbox'
  | 'progress.end'
  | 'progress.page.number'
  | 'progress.percent'
  | 'page_count'
  | 'language.code'
>;

export const galleryCardDataFields: FieldPath<ServerGallery>[] = [
  'artists.preferred_name.name',
  'preferred_title.name',
  'profile',
  'number',
  'page_count',
  'language.code',
  'progress.end',
  'progress.page.number',
  'progress.percent',
  'metatags.*',
];

function ReadButton({ data }: { data: { id: number } }) {
  return (
    <Link
      href={useMemo(() => ({ pathname: `/item/gallery/${data?.id}/page/1` }), [
        data,
      ])}
      passHref>
      <Button as="a" primary size="mini">
        <Icon name="envelope open outline" />
        {t`Read`}
      </Button>
    </Link>
  );
}

function ContinueButton({
  data,
}: {
  data: DeepPick<GalleryCardData, 'id' | 'progress.page.number'>;
}) {
  return (
    <Link
      href={useMemo(
        () => ({
          pathname: `/item/gallery/${data?.id}/page/${data.progress.page.number}`,
        }),
        [data]
      )}
      passHref>
      <Button color="orange" size="mini">
        <Icon name="play" />
        {t`Continue`}
      </Button>
    </Link>
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

function GalleryCardMenu({
  hasProgress,
  read,
}: {
  hasProgress: boolean;
  read: boolean;
}) {
  return (
    <ItemMenuLabel>
      {!hasProgress && (
        <ItemMenuLabelItem icon="envelope open outline">{t`Read`}</ItemMenuLabelItem>
      )}
      {hasProgress && (
        <ItemMenuLabelItem icon="play">{t`Continue reading`}</ItemMenuLabelItem>
      )}
      <ItemMenuLabelItem icon="plus">{t`Add to session`}</ItemMenuLabelItem>
      <ItemMenuLabelItem icon="pencil">{t`Edit`}</ItemMenuLabelItem>
      {!read && (
        <ItemMenuLabelItem icon="envelope open outline">{t`Mark as read`}</ItemMenuLabelItem>
      )}
    </ItemMenuLabel>
  );
}
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
  const hasProgress = !!data?.progress && !data?.progress?.end;

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
          </ItemLabel>,
          <ItemLabel x="right" y="top">
            {!!data?.metatags?.inbox && <InboxIconLabel />}
            {!data?.metatags?.read && !hasProgress && <UnreadIconLabel />}
            {!!data?.metatags?.readlater && <ReadLaterIconLabel />}
            {hasProgress && (
              <ReadingIconLabel percent={data?.progress?.percent} />
            )}
            {!!data?.number && data?.number > 0 && (
              <GroupingNumberLabel as={TranslucentLabel}>
                {data?.number}
              </GroupingNumberLabel>
            )}
            <ProgressLabel />
          </ItemLabel>,
          <ItemLabel x="right" y="bottom">
            {horizontal && <StatusLabel as={TranslucentLabel} />}
            {horizontal && <ReadCountLabel as={TranslucentLabel} />}
            {horizontal && <LanguageLabel as={TranslucentLabel} />}
            {horizontal && <PageCountLabel as={TranslucentLabel} />}
            {!horizontal && !!data?.language?.code && (
              <TranslucentLabel>
                {data.language.code.toUpperCase()}
              </TranslucentLabel>
            )}
            {!horizontal && (
              <TranslucentLabel circular>{data?.page_count}</TranslucentLabel>
            )}
            <GalleryCardMenu
              hasProgress={hasProgress}
              read={data?.metatags?.read}
            />
          </ItemLabel>,
        ],
        [horizontal, hasProgress, data]
      )}
      actionContent={useCallback(
        () => (
          <ItemCardActionContent>
            <ItemCardActionContentItem>
              {!hasProgress && <ReadButton data={data} />}
              {hasProgress && <ContinueButton data={data} />}
            </ItemCardActionContentItem>
            <ItemCardActionContentItem>
              <SaveForLaterButton />
            </ItemCardActionContentItem>
          </ItemCardActionContent>
        ),
        [data]
      )}
      image={useCallback(
        ({ children }: { children?: React.ReactNode }) => (
          <ItemCardImage src={data?.profile}>{children}</ItemCardImage>
        ),
        [data.profile]
      )}>
      <ItemCardContent
        title={data?.preferred_title?.name ?? ''}
        subtitle={data?.artists.map((a) => (
          <span key={a.id}>{a.preferred_name.name}</span>
        ))}>
        <ReadCountLabel />
      </ItemCardContent>
    </ItemCard>
  );
}

export default GalleryCard;
