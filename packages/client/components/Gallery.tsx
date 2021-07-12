import { useCallback, useMemo } from 'react';
import { Button, Icon } from 'semantic-ui-react';

import { ItemType } from '../misc/enums';
import t from '../misc/lang';
import { ItemSize, ServerGallery } from '../misc/types';
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

function GalleryMenuItems() {
  return (
    <>
      <ItemMenuLabelItem icon="envelope open outline">{t`Read`}</ItemMenuLabelItem>
      <ItemMenuLabelItem icon="play">{t`Continue reading`}</ItemMenuLabelItem>
    </>
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
  'id' | 'preferred_title.name' | 'artists.[].preferred_name.name'
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
  details?: React.ElementType;
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
      disableModal={disableModal}
      onDetailsOpen={onDetailsOpen}
      labels={useMemo(
        () => [
          <ItemLabel x="left" y="top">
            <HeartIconLabel />
            <GroupingNumberLabel as={TranslucentLabel} />
          </ItemLabel>,
          <ItemLabel x="right" y="top">
            <InboxIconLabel />
            <ReadingIconLabel />
            <UnreadIconLabel />
            <ReadLaterIconLabel />
            <ProgressLabel />
          </ItemLabel>,
          <ItemLabel x="right" y="bottom">
            {horizontal && <StatusLabel as={TranslucentLabel} />}
            {horizontal && <ReadCountLabel as={TranslucentLabel} />}
            {horizontal && <LanguageLabel as={TranslucentLabel} />}
            {horizontal && <PageCountLabel as={TranslucentLabel} />}
            {!horizontal && <TranslucentLabel>{'EN'}</TranslucentLabel>}
            {!horizontal && <TranslucentLabel circular>{23}</TranslucentLabel>}
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
