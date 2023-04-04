import { useCallback, useState } from 'react';
import { Tab } from 'semantic-ui-react';

import { QueryType, useQueryType } from '../client/queries';
import { ItemType } from '../shared/enums';
import { ServerGallery } from '../shared/types';
import CollectionCard, { collectionCardDataFields } from './item/Collection';
import GalleryCard, { galleryCardDataFields } from './item/Gallery';
import ListView from './view/ListView';

const itemRender = {
  [ItemType.Gallery]: GalleryCard,
  [ItemType.Collection]: CollectionCard,
};

const itemFields = {
  [ItemType.Gallery]: galleryCardDataFields,
  [ItemType.Collection]: collectionCardDataFields,
};

export function TrashView({
  itemType = ItemType.Gallery,
}: {
  itemType: ItemType;
}) {
  const limit = 30;
  const [page, setPage] = useState(0);

  const { data, isLoading } = useQueryType(QueryType.LIBRARY, {
    item_type: itemType,
    fields: itemFields[itemType],
    metatags: {
      trash: true,
    },
    page: page,
    limit,
  });

  const Element = itemRender[itemType];

  //   return (
  //     <Card.Group>
  //       {data?.data?.items?.map?.((item) => (
  //         <Element key={item.id} data={item} size="mini" horizontal />
  //       ))}
  //     </Card.Group>
  //   );

  return (
    <ListView
      items={data?.data?.items as ServerGallery[]}
      onItemKey={useCallback((i) => i.id, [])}
      loading={isLoading}
      totalItemCount={data?.data?.count}
      dynamicRowHeight
      disableWindowScroll
      pagination
      paginationSize="mini"
      activePage={page + 1}
      onPageChange={useCallback((ev, p) => setPage(p - 1), [])}
      itemsPerPage={limit}
      size="mini"
      itemRender={itemRender[itemType]}
      bottomPagination
      className="max-600-h"
    />
  );
}

const panes = [
  {
    menuItem: 'Gallery',
    render: () => <TrashView itemType={ItemType.Gallery} />,
  },
  {
    menuItem: 'Collection',
    render: () => <TrashView itemType={ItemType.Collection} />,
  },
];

export function TrashTabView() {
  return <Tab panes={panes} renderActiveOnly />;
}
