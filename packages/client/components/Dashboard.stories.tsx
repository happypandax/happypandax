import {
  FavoriteCollections,
  FavoriteGalleries,
  FavoritePages,
  Favorites as FavoritesComponent,
} from './Dashboard';

export default {
  title: 'Components/Dashboard',
};

export const Dashboard = () => (
  <>
    <FavoritesComponent />
    <FavoriteGalleries />
    <FavoriteCollections />
    <FavoritePages />
  </>
);
