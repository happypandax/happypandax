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
} from '../dataview/Common';
import GalleryDataTable from '../dataview/GalleryDataTable';
import {
  ActivityLabel,
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
  QueueIconLabel,
  ReadingIconLabel,
  ReadLaterIconLabel,
  TranslucentLabel,
  UnreadIconLabel,
} from './';

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
  | 'times_read'
  | 'language.code'
  | 'language.name'
  | 'grouping.status.name'
>;

export const galleryCardDataFields: FieldPath<ServerGallery>[] = [
  'artists.preferred_name.name',
  'preferred_title.name',
  'profile',
  'number',
  'times_read',
  'page_count',
  'language.code',
  'language.name',
  'grouping.status.name',
  'progress.end',
  'progress.page.number',
  'progress.percent',
  'metatags.*',
];

function ReadButton({ data }: { data: { id: number } }) {
  const externalViewer = useRecoilValue(AppState.externalViewer);

  return (
    <Link
      href={useMemo(() => ({ pathname: `/item/gallery/${data?.id}/page/1` }), [
        data,
      ])}
      passHref>
      <Button
        as="a"
        primary
        size="mini"
        onClick={useCallback((e) => {
          if (externalViewer) {
            e.preventDefault();
          }
        }, [])}>
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
      <Button as="a" color="orange" size="mini">
        <Icon name="play" />
        {t`Continue`}
      </Button>
    </Link>
  );
}

function SaveForLaterButton() {
  return (
    <Button
      size="mini"
      onClick={useCallback((e) => {
        e.preventDefault();
      }, [])}>
      <Icon name="bookmark outline" />
      {t`Save for later`}
    </Button>
  );
}

function AddToQueueButton({ data }: { data: GalleryCardData }) {
  const [readingQueue, setReadingQueue] = useRecoilState(AppState.readingQueue);

  const exists = readingQueue.includes(data.id);

  return (
    <Button
      color="red"
      size="mini"
      onClick={useCallback(
        (e) => {
          e.preventDefault();
          if (exists) {
            setReadingQueue(readingQueue.filter((i) => i !== data.id));
          } else {
            setReadingQueue([...readingQueue, data.id]);
          }
        },
        [data, readingQueue]
      )}>
      <Icon name={exists ? 'minus' : 'plus'} />
      {t`Queue`}
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
        <>
          <ItemMenuLabelItem icon="book open">{t`Read`}</ItemMenuLabelItem>
          <ItemMenuLabelItem icon="book open">{t`Read in New Tab`}</ItemMenuLabelItem>
        </>
      )}
      {hasProgress && (
        <ItemMenuLabelItem icon="play">{t`Continue reading`}</ItemMenuLabelItem>
      )}
      <ItemMenuLabelItem icon="plus">{t`Add to queue`}</ItemMenuLabelItem>
      <ItemMenuLabelItem icon="pencil">{t`Edit`}</ItemMenuLabelItem>
      <ItemMenuLabelItem icon="exchange">{t`Show activity`}</ItemMenuLabelItem>
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
  loading,
  hiddenLabel,
  hiddenAction,
  activity,
  activityContent,
  actionContent,
  draggable = true,
  disableModal,
  details = GalleryDataTable,
  onDetailsOpen,
  horizontal,
}: {
  size?: ItemSize;
  data: GalleryCardData;
  fluid?: boolean;
  hiddenLabel?: boolean;
  hiddenAction?: boolean;
  loading?: boolean;
  activity?: boolean;
  activityContent?: React.ReactNode;
  actionContent?: React.ComponentProps<typeof ItemCard>['actionContent'];
  draggable?: boolean;
  disableModal?: boolean;
  details?: React.ElementType<{ data: PartialExcept<ServerItem, 'id'> }>;
  onDetailsOpen?: () => void;
  horizontal?: boolean;
}) {
  const hasProgress = !!data?.progress && !data?.progress?.end;

  const readingQueue = useRecoilValue(AppState.readingQueue);

  const actions = useCallback(
    () => (
      <ItemCardActionContent>
        {hasProgress && (
          <ItemCardActionContentItem>
            <ContinueButton data={data} />
          </ItemCardActionContentItem>
        )}
        {(!hasProgress || horizontal) && (
          <ItemCardActionContentItem>
            <ReadButton data={data} />
          </ItemCardActionContentItem>
        )}
        {(horizontal ||
          !(['tiny', 'small', 'mini'] as ItemSize[]).includes(size)) && (
          <ItemCardActionContentItem>
            <AddToQueueButton data={data} />
          </ItemCardActionContentItem>
        )}
        <ItemCardActionContentItem>
          <SaveForLaterButton />
        </ItemCardActionContentItem>
      </ItemCardActionContent>
    ),
    [data, size, horizontal]
  );

  return (
    <ItemCard
      type={ItemType.Gallery}
      href={`/item/gallery/${data.id}`}
      dragData={data}
      draggable={draggable}
      centered
      hiddenLabel={hiddenLabel}
      hiddenAction={hiddenAction}
      loading={loading}
      activity={activity}
      activityContent={activityContent}
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
          <ItemLabel key="fav" x="left" y="top">
            <FavoriteLabel />
          </ItemLabel>,
          <ItemLabel key="icons" x="right" y="top">
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
            <ActivityLabel />
          </ItemLabel>,
          <ItemLabel key="info" x="right" y="bottom">
            {horizontal && (
              <StatusLabel as={TranslucentLabel}>
                {data?.grouping?.status?.name}
              </StatusLabel>
            )}
            {horizontal && (
              <ReadCountLabel as={TranslucentLabel}>
                {data?.times_read}
              </ReadCountLabel>
            )}
            {horizontal && !!data?.language && (
              <LanguageLabel as={TranslucentLabel}>
                {data.language?.code
                  ? data.language.code.toUpperCase?.()
                  : data?.language?.name ?? ''}
              </LanguageLabel>
            )}
            {horizontal && (
              <PageCountLabel as={TranslucentLabel}>
                {data?.page_count}
              </PageCountLabel>
            )}
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
      actionContent={actionContent ?? actions}
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
        ))}></ItemCardContent>
    </ItemCard>
  );
}

export default GalleryCard;
