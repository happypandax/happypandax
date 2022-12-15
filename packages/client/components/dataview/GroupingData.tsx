import { useEffect, useState } from 'react';
import { useSetRecoilState } from 'recoil';
import { Segment } from 'semantic-ui-react';

import { DataContext } from '../../client/context';
import { QueryType, useQueryType } from '../../client/queries';
import { ItemType } from '../../shared/enums';
import { ServerGallery, ServerGrouping } from '../../shared/types';
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
  ...props
}: {
  data: PartialExcept<ServerGrouping, 'id'>;
} & React.ComponentProps<typeof DataTable>) {
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
      <DataTable showDataText={showDataText} loading={isLoading} {...props}>
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
        {data?.info && (
          <DataTableItem>
            <Segment tertiary className="fluid">
              {data.info}
            </Segment>
          </DataTableItem>
        )}
      </DataTable>
    </DataContext.Provider>
  );
}
