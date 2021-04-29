import { Button, Icon } from 'semantic-ui-react';
import { useCallback, useMemo } from 'react';
import {
  ReadingIconLabel,
  UnreadIconLabel,
  ReadLaterIconLabel,
  ItemCardActionContent,
  ItemCardActionContentItem,
  InboxIconLabel,
  ItemLabel,
  ItemCard,
  ItemCardContent,
  ItemCardImage,
  HeartIconLabel,
  TranslucentLabel,
  ItemMenuLabelItem,
  ItemMenuLabel,
  ProgressLabel,
} from './Item';
import t from '../misc/lang';
import { ItemSize } from '../misc/types';
import { GalleryDataTable } from './DataTable';

function ReadButton() {
  return (
    <Button primary size="tiny">
      <Icon name="envelope open outline" />
      {t`Read`}
    </Button>
  );
}

function SaveForLaterButton() {
  return (
    <Button size="tiny">
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

export function GalleryCard({
  size,
  data,
  fluid,
  disableModal,
  details = GalleryDataTable,
  onDetailsOpen,
  horizontal,
}: {
  size?: ItemSize;
  data: any;
  fluid?: boolean;
  disableModal?: boolean;
  details?: React.ElementType;
  onDetailsOpen?: () => void;
  horizontal?: boolean;
}) {
  return (
    <ItemCard
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
          </ItemLabel>,
          <ItemLabel x="right" y="top">
            <InboxIconLabel />
            <ReadingIconLabel />
            <UnreadIconLabel />
            <ReadLaterIconLabel />
            <ProgressLabel />
          </ItemLabel>,
          <ItemLabel x="right" y="bottom">
            <TranslucentLabel>{'EN'}</TranslucentLabel>
            <TranslucentLabel circular>{23}</TranslucentLabel>
            <GalleryCardMenu />
          </ItemLabel>,
        ],
        []
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
        title={data?.title ?? ''}
        subtitle={[data?.artist].map((a) => (
          <span>{a}</span>
        ))}
      />
    </ItemCard>
  );
}

export default GalleryCard;
