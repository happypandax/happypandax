import { GalleryCard } from './Gallery';

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
