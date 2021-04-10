import { Button } from 'semantic-ui-react';
import { useCallback } from 'react';
import {
  ReadingIconAction,
  UnreadIconAction,
  ReadLaterIconAction,
  ItemCardImageContent,
  ItemCardImageContentItem,
  InboxIconAction,
  ItemAction,
  ItemCard,
  ItemCardContent,
  ItemCardImage,
  ItemCardProgress,
  HeartIconAction,
} from './Item';

export function GalleryCard() {
  return (
    <ItemCard
      centered
      link
      actions={[
        <ItemAction x="left" y="top">
          <HeartIconAction />
        </ItemAction>,
        <ItemAction x="right" y="top">
          <InboxIconAction />
          <ReadingIconAction />
          <UnreadIconAction />
          <ReadLaterIconAction />
        </ItemAction>,
      ]}
      image={useCallback(
        () => (
          <ItemCardImage>
            <ItemCardImageContent>
              <ItemCardImageContentItem>
                <Button>Test</Button>
              </ItemCardImageContentItem>{' '}
            </ItemCardImageContent>{' '}
          </ItemCardImage>
        ),
        []
      )}>
      <ItemCardContent />
      <ItemCardProgress />
    </ItemCard>
  );
}

export default GalleryCard;
