import { useEffect, useState } from 'react';
import { useSetRecoilState } from 'recoil';

import { DataContext } from '../../client/context';
import { QueryType, useQueryType } from '../../client/queries';
import { ItemType } from '../../misc/enums';
import { ServerGallery, ServerGrouping } from '../../misc/types';
import { DataState } from '../../state';
import {
  DateAddedLabel,
  GalleryCountLabel,
  NameTable,
  StatusLabel,
} from './Common';
import { DataTable, DataTableItem } from './DataTable';

export default function GroupingDataTable({
  data: initialData,
}: {
  data: PartialExcept<ServerGrouping, 'id'>;
}) {
  const contextKey = DataState.getKey(ItemType.Grouping, initialData);

  const setData = useSetRecoilState(DataState.data(contextKey));

  const [showDataText, setShowDataText] = useState(false);

  const { data: qData, isLoading } = useQueryType(QueryType.ITEM, {
    item_type: ItemType.Grouping,
    item_id: initialData.id,
    fields: ['name', 'info', 'timestamp', 'status.name', 'gallery_count'],
  });

  const data = qData?.data ?? initialData;

  useEffect(() => {
    setData(data as PartialExcept<ServerGallery, 'id'>);
  }, [data]);

  return (
    <DataContext.Provider value={{ key: contextKey, type: ItemType.Grouping }}>
      <DataTable showDataText={showDataText} loading={isLoading}>
        <DataTableItem>
          <NameTable>
            {/* <Label
                as="a"
                onClick={useCallback(() => {
                  setShowDataText(true);
                }, [])}
                className="float-right"
                size="tiny">
                <Icon name="pencil" /> {t`Edit`}
              </Label> */}
          </NameTable>
        </DataTableItem>
        <DataTableItem textAlign="center">
          <StatusLabel>{data?.status?.name}</StatusLabel>
          <GalleryCountLabel>{data?.gallery_count}</GalleryCountLabel>
          <DateAddedLabel timestamp={data?.timestamp} />
        </DataTableItem>
        {data?.info && <p>{data.info}</p>}
      </DataTable>
    </DataContext.Provider>
  );
}
