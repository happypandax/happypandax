import { DragBoard } from './Drawer';
import { GalleryCard } from './Gallery';
import PageLayout from './layout/Page';

export default {
  title: 'Item/Gallery',
};

export const Card = () => (
  <GalleryCard data={{ title: 'test', artist: 'testy' }} />
);

export const Horizontal = () => (
  <GalleryCard
    data={{ title: 'test', artist: 'testy' }}
    horizontal
    size="tiny"
  />
);

export const Draggable = () => (
  <PageLayout>
    <GalleryCard
      data={{ title: 'test 1', id: 1, artist: 'testy' }}
      horizontal
      size="tiny"
    />
    <GalleryCard data={{ title: 'test 2', id: 2, artist: 'testy' }} />
    <DragBoard />
  </PageLayout>
);
