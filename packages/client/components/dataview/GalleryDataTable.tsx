import { useEffect, useState } from 'react';
import { useSetRecoilState } from 'recoil';

import { DataContext } from '../../client/context';
import { QueryType, useQueryType } from '../../client/queries';
import { ItemType } from '../../misc/enums';
import t from '../../misc/lang';
import { ServerGallery } from '../../misc/types';
import { DataState } from '../../state';
import {
  ArtistLabels,
  CategoryLabel,
  CircleLabels,
  DateAddedLabel,
  DatePublishedLabel,
  GroupingLabel,
  GroupingNumberLabel,
  LanguageLabel,
  LastReadLabel,
  LastUpdatedLabel,
  NamesTable,
  PageCountLabel,
  ParodyLabels,
  ReadCountLabel,
  StatusLabel,
  TagsTable,
  UrlList,
} from './Common';
import { DataTable, DataTableItem } from './DataTable';

export default function GalleryDataTable({
  data: initialData,
}: {
  data: PartialExcept<ServerGallery, 'id'>;
}) {
  const contextKey = DataState.getKey(ItemType.Gallery, initialData);

  const setData = useSetRecoilState(DataState.data(contextKey));

  const [showDataText, setShowDataText] = useState(false);

  const { data: qData, isLoading } = useQueryType(QueryType.ITEM, {
    item_type: ItemType.Gallery,
    item_id: initialData.id,
    fields: [
      'titles.name',
      'titles.language.name',
      'preferred_title.name',
      'language.name',
      'grouping.name',
      'grouping.status.name',
      'number',
      'info',
      'artists.names.name',
      'artists.circles.name',
      'artists.preferred_name.name',
      'parodies.names.name',
      'parodies.preferred_name.name',
      'rating',
      'page_count',
      'category.name',
      'circles.name',
      'urls.name',
      'last_read',
      'last_updated',
      'timestamp',
      'pub_date',
      'tags.namespace.name',
      'tags.tag.name',
      'urls.name',
      'times_read',
    ],
  });

  const data = qData?.data ?? initialData;

  useEffect(() => {
    setData(data as PartialExcept<ServerGallery, 'id'>);
  }, [data]);

  return (
    <DataContext.Provider value={{ key: contextKey, type: ItemType.Gallery }}>
      <DataTable showDataText={showDataText} loading={isLoading}>
        <DataTableItem>
          <NamesTable dataKey="titles" dataPrimaryKey="preferred_title">
            {/* <Label
                as="a"
                onClick={useCallback(() => {
                  setShowDataText(true);
                }, [])}
                className="float-right"
                size="tiny">
                <Icon name="pencil" /> {t`Edit`}
              </Label> */}
            <GroupingNumberLabel
              className="float-left"
              circular
              size="tiny"
              color="black">
              {data?.number}
            </GroupingNumberLabel>
          </NamesTable>
        </DataTableItem>
        <DataTableItem textAlign="center">
          <CategoryLabel />
          <LanguageLabel>{data?.language?.name}</LanguageLabel>
          <ReadCountLabel>{data?.times_read}</ReadCountLabel>
          <PageCountLabel>{data?.page_count}</PageCountLabel>
          <StatusLabel>{data?.grouping?.status?.name}</StatusLabel>
        </DataTableItem>
        {data?.info && <p>{data.info}</p>}
        <DataTableItem name={t`Artist`}>
          <ArtistLabels />
        </DataTableItem>
        <DataTableItem name={t`Rating`}>test</DataTableItem>
        <DataTableItem name={t`Series`}>
          <GroupingLabel />
        </DataTableItem>
        <DataTableItem name={t`Circle`}>
          <CircleLabels />
        </DataTableItem>
        <DataTableItem name={t`Parody`}>
          <ParodyLabels />
        </DataTableItem>
        <DataTableItem name={t`Published`}>
          <DatePublishedLabel />
        </DataTableItem>
        <DataTableItem name={t`Tags`}>
          <TagsTable />
        </DataTableItem>
        <DataTableItem name={t`External links`}>
          <UrlList />
        </DataTableItem>
        <DataTableItem textAlign="center">
          <LastReadLabel timestamp={data?.last_read} />
          <LastUpdatedLabel timestamp={data?.last_updated} />
          <DateAddedLabel timestamp={data?.timestamp} />
        </DataTableItem>
      </DataTable>
    </DataContext.Provider>
  );
}
