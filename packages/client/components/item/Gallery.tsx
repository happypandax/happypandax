import Link from 'next/link';
import { useCallback, useMemo } from 'react';
import { useRecoilState, useRecoilValue } from 'recoil';
import { Button, Icon } from 'semantic-ui-react';

import { ItemType } from '../../misc/enums';
import t from '../../misc/lang';
import {
  FieldPath,
  ItemSize,
  ServerGallery,
  ServerItem,
} from '../../misc/types';
import { AppState } from '../../state';
import {
  GroupingNumberLabel,
  LanguageLabel,
  PageCountLabel,
  ReadCountLabel,
  StatusLabel,
} from '../data/Common';
import { GalleryDataTable } from '../DataTable';
import {
  FavoriteLabel,
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
  QueueIconLabel,
  ReadingIconLabel,
  ReadLaterIconLabel,
  TranslucentLabel,
  UnreadIconLabel,
} from '../Item';

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
        <Icon className="book open" />
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

function AddToQueueButton({ data }: { data: GalleryCardData }) {
  const [readingQueue, setReadingQueue] = useRecoilState(AppState.readingQueue);

  return (
    <Button
      color="red"
      size="mini"
      onClick={useCallback(() => {
        setReadingQueue([...readingQueue, data.id]);
      }, [data, readingQueue])}>
      <Icon name="plus" />
      {t`Add to queue`}
    </Button>
  );
}

function GalleryMenu({
  hasProgress,
  read,
}: {
  hasProgress: boolean;
  read: boolean;
}) {
  return (
    <ItemMenuLabel>
      {!hasProgress && (
        <ItemMenuLabelItem icon="book open">{t`Read`}</ItemMenuLabelItem>
      )}
      {hasProgress && (
        <ItemMenuLabelItem icon="play">{t`Continue reading`}</ItemMenuLabelItem>
      )}
      <ItemMenuLabelItem icon="plus">{t`Add to queue`}</ItemMenuLabelItem>
      <ItemMenuLabelItem icon="pencil">{t`Edit`}</ItemMenuLabelItem>
      {!read && (
        <ItemMenuLabelItem icon="eye">{t`Mark as read`}</ItemMenuLabelItem>
      )}
      {read && (
        <ItemMenuLabelItem icon="eye">{t`Mark as unread`}</ItemMenuLabelItem>
      )}
      <ItemMenuLabelItem icon="trash">{t`Delete`}</ItemMenuLabelItem>
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

  const readingQueue = useRecoilValue(AppState.readingQueue);

  return (
    <ItemCard
      type={ItemType.Gallery}
      href={`/item/gallery/${data.id}`}
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
            <FavoriteLabel />
          </ItemLabel>,
          <ItemLabel x="right" y="top">
            {readingQueue?.includes?.(data?.id) && <QueueIconLabel />}
            {!!data?.metatags?.inbox && <InboxIconLabel />}
            {!data?.metatags?.read && !hasProgress && <UnreadIconLabel />}
            {!!data?.metatags?.readlater && <ReadLaterIconLabel />}
            {hasProgress && (
              <ReadingIconLabel percent={data?.progress?.percent} />
            )}
            {data?.number !== undefined && data?.number > 0 && (
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
            <GalleryMenu
              hasProgress={hasProgress}
              read={data?.metatags?.read}
            />
          </ItemLabel>,
        ],
        [horizontal, hasProgress, data, readingQueue]
      )}
      actionContent={useCallback(
        () => (
          <ItemCardActionContent>
            <ItemCardActionContentItem>
              {!hasProgress && <ReadButton data={data} />}
              {hasProgress && <ContinueButton data={data} />}
            </ItemCardActionContentItem>
            {!(['tiny', 'small', 'mini'] as ItemSize[]).includes(size) && (
              <ItemCardActionContentItem>
                <AddToQueueButton data={data} />
              </ItemCardActionContentItem>
            )}
            <ItemCardActionContentItem>
              <SaveForLaterButton />
            </ItemCardActionContentItem>
          </ItemCardActionContent>
        ),
        [data, size]
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