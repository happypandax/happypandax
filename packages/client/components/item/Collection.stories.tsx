import { SelectedBoard } from '../Drawer';
import PageLayout from '../layout/Page';
import { CollectionCard } from './Collection';

export default {
  title: 'Item/Collection',
};

const data = (id: number, title = 'title_test', artist = 'testy') => ({
  id,
  preferred_title: { name: title },
  artists: [{ preferred_name: { name: artist } }],
});

export const Card = () => <CollectionCard data={data(1)} />;

export const Horizontal = () => (
  <CollectionCard data={data(1)} horizontal size="tiny" />
);

export const Draggable = () => (
  <PageLayout>
    <CollectionCard data={data(1)} horizontal size="tiny" />
    <CollectionCard data={data(2)} />
    <SelectedBoard />
  </PageLayout>
);
