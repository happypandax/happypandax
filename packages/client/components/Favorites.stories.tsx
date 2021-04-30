import {
  Favorites as FavoritesComponent,
  FavoriteGalleries,
  FavoritePages,
  FavoriteCollections,
} from './Favorites';

export default {
  title: 'Components/Favorites',
};

export const Favorites = () => (
  <>
    <FavoritesComponent />
    <FavoriteGalleries />
    <FavoriteCollections />
    <FavoritePages />
  </>
);
