import GalleryCard from '../Gallery';
import ListView from './ListView';

export default {
  title: 'View/List',
};

const data = (id: number, title = 'title_test', artist = 'testy') => ({
  id,
  preferred_title: { name: title },
  artists: [{ preferred_name: { name: artist } }],
});

export const List = () => (
  <ListView
    items={[
      data(1),
      data(2),
      data(3),
      data(4),
      data(5),
      data(6),
      data(7),
      data(8),
      data(9),
      data(10),
      data(11),
      data(12),
      data(13),
      data(14),
      data(15),
      data(16),
    ]}
    itemRender={GalleryCard}
    totalItemCount={16}
    pagination
    bottomPagination
  />
);
