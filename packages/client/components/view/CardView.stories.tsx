import GalleryCard from '../item/Gallery';
import CardView from './CardView';

export default {
  title: 'View/Card',
};

const data = (id: number, title = 'title_test', artist = 'testy') => ({
  id,
  preferred_title: { name: title },
  artists: [{ preferred_name: { name: artist } }],
});

export const Card = () => (
  <CardView
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
