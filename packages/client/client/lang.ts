import { msgid as tmsgid, ngettext, t as tt } from 'ttag';

import { ItemSort } from '../shared/enums';

export const t = tt;
export default t;

export const pluralize = ngettext;
export const msgid = tmsgid;

// Example
// pluralize(msgid`${i} tick passed`, `${i} ticks passed`, i)

export const sortIndexName = {
  [ItemSort.GalleryRandom]: t`Random`,
  [ItemSort.GalleryTitle]: t`Title`,
  [ItemSort.GalleryArtist]: t`Artist`,
  [ItemSort.GalleryDate]: t`Date Added`,
  [ItemSort.GalleryPublished]: t`Date Published`,
  [ItemSort.GalleryRead]: t`Last Read`,
  [ItemSort.GalleryUpdated]: t`Last Updated`,
  [ItemSort.GalleryRating]: t`Rating`,
  [ItemSort.GalleryReadCount]: t`Read Count`,
  [ItemSort.GalleryPageCount]: t`Page Count`,
  [ItemSort.GalleryCircle]: t`Circle`,
  [ItemSort.GroupingRandom]: t`Random`,
  [ItemSort.GroupingName]: t`Series Name`,
  [ItemSort.GroupingDate]: t`Date Added`,
  [ItemSort.GroupingGalleryCount]: t`Gallery Count`,
  [ItemSort.ArtistName]: t`Name`,
  [ItemSort.NamespaceTagNamespace]: t`Namespace`,
  [ItemSort.NamespaceTagTag]: t`Tag`,
  [ItemSort.FilterName]: t`Name`,
  [ItemSort.CircleName]: t`Name`,
  [ItemSort.ParodyName]: t`Name`,
  [ItemSort.CollectionRandom]: t`Random`,
  [ItemSort.CollectionName]: t`Name`,
  [ItemSort.CollectionDate]: t`Date Added`,
  [ItemSort.CollectionPublished]: t`Date Published`,
  [ItemSort.CollectionGalleryCount]: t`Gallery Count`,
};
