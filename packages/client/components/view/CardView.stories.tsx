import CardView from './CardView';
import GalleryCard from '../Gallery';

export default {
  title: 'View/Card',
};

export const Card = () => (
  <CardView
    items={[
      { title: 'Test Title', artist: 'Testy' },
      { title: 'Test Titl2e', artist: 'Testy' },
      { title: 'Test4 Title', artist: 'Testy' },
      { title: 'Test Title', artist: 'Tes7ty' },
      { title: 'Test Title', artist: 'Tes7ty' },
      { title: 'Test Title', artist: 'Tes7ty' },
      { title: 'Test Title', artist: 'Tes7ty' },
      { title: 'Test Title', artist: 'Tes7ty' },
      { title: 'Test Title', artist: 'Tes7ty' },
      { title: 'Test Title', artist: 'Tes7ty' },
      { title: 'Test Title', artist: 'Tes7ty' },
      { title: 'Test Titl2e', artist: 'Test2y' },
      { title: 'Test Tit2le', artist: 'Test6y' },
    ]}
    itemRender={GalleryCard}
    totalItemCount={13}
    pagination
    bottomPagination
  />
);
