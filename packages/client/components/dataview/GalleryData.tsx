import { useState } from 'react';
import { Label } from 'semantic-ui-react';

import { DataContext } from '../../client/context';
import { useSetupDataState } from '../../client/hooks/item';
import t from '../../client/lang';
import { QueryType, useQueryType } from '../../client/queries';
import { ItemType } from '../../shared/enums';
import { ServerGallery } from '../../shared/types';
import {
  ArtistLabels,
  CategoryLabel,
  CircleLabels,
  DateAddedLabel,
  DatePublishedLabel,
  GroupingLabel,
  GroupingNumberLabel,
  InfoSegment,
  LanguageLabel,
  LastReadLabel,
  LastUpdatedLabel,
  NamesTable,
  PageCountLabel,
  ParodyLabels,
  RatingLabel,
  ReadCountLabel,
  StatusLabel,
  TagsTable,
  UrlList,
} from './Common';
import { DataTable, DataTableItem } from './DataTable';

export default function GalleryDataTable({
  data: initialData,
  ...props
}: {
  data: PartialExcept<ServerGallery, 'id'>;
} & React.ComponentProps<typeof DataTable>) {
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
      'tags.metatags.favorite',
      'tags.tag.name',
      'urls.name',
      'times_read',
    ],
  });

  const { data, dataContext } = useSetupDataState({
    initialData:
      (qData?.data as PartialExcept<ServerGallery, 'id'>) ?? initialData,
    itemType: ItemType.Gallery,
  });

  return (
    <DataContext.Provider value={dataContext}>
      <DataTable showDataText={showDataText} loading={isLoading} {...props}>
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
              color="black"
            >
              {data?.number}
            </GroupingNumberLabel>
          </NamesTable>
        </DataTableItem>
        <DataTableItem textAlign="center">
          <CategoryLabel />
          <LanguageLabel>{data?.language?.name}</LanguageLabel>
          <StatusLabel>{data?.grouping?.status?.name}</StatusLabel>
          <ReadCountLabel>{data?.times_read}</ReadCountLabel>
          <PageCountLabel>{data?.page_count}</PageCountLabel>
        </DataTableItem>
        {data?.info && (
          <DataTableItem>
            <InfoSegment fluid />
          </DataTableItem>
        )}

        <DataTableItem name={t`Artist`}>
          <ArtistLabels />
        </DataTableItem>
        <DataTableItem name={t`Rating`}>
          <RatingLabel defaultRating={data?.rating} />
        </DataTableItem>
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
          <Label.Group>
            <LastReadLabel timestamp={data?.last_read} />
            <LastUpdatedLabel timestamp={data?.last_updated} />
            <DateAddedLabel timestamp={data?.timestamp} />
          </Label.Group>
        </DataTableItem>
      </DataTable>
    </DataContext.Provider>
  );
}
