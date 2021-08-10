import { useCallback, useEffect, useState } from 'react';
import { useSetRecoilState } from 'recoil';
import { Header, Icon, Label, Table } from 'semantic-ui-react';

import { QueryType, useQueryType } from '../client/queries';
import { ItemType } from '../misc/enums';
import t from '../misc/lang';
import { ServerGallery } from '../misc/types';
import { DataState } from '../state';
import {
  ArtistLabels,
  CategoryLabel,
  CircleLabels,
  DataContext,
  DateAddedLabel,
  DatePublishedLabel,
  GroupingLabel,
  GroupingNumberLabel,
  LanguageLabel,
  LastReadLabel,
  LastUpdatedLabel,
  NameTable,
  PageCountLabel,
  ReadCountLabel,
  StatusLabel,
  TagsTable,
  UrlList,
} from './data/Common';
import { TextEditor } from './Misc';

export function GalleryDataTable({
  data: initialData,
}: {
  data: PartialExcept<ServerGallery, 'id'>;
}) {
  const contextKey = DataState.getKey(ItemType.Gallery, initialData);

  const setData = useSetRecoilState(DataState.data(contextKey));

  const [showDataText, setShowDataText] = useState(false);

  const { data: qData } = useQueryType(QueryType.ITEM, {
    item_type: ItemType.Gallery,
    item_id: initialData.id,
    fields: [
      'titles.language.name',
      'preferred_title.name',
      'language.name',
      'grouping.name',
      'grouping.status.name',
      'number',
      'artists.names.name',
      'artists.circles.name',
      'artists.preferred_name.name',
      'rating',
      'page_count',
      'category.name',
      'circles.name',
      'category.name',
      'urls.name',
      'last_read',
      'last_updated',
      'tags.namespace.name',
      'tags.tag.name',
      'pub_date',
      'timestamp',
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
      <DataTable showDataText={showDataText}>
        <DataTableItem>
          <NameTable dataKey="titles" dataPrimaryKey="preferred_title">
            <Label
              as="a"
              onClick={useCallback(() => {
                setShowDataText(true);
              }, [])}
              className="float-right"
              size="tiny">
              <Icon name="pencil" /> {t`Edit`}
            </Label>
            <GroupingNumberLabel
              className="float-left"
              circular
              size="tiny"
              color="black">
              {data?.number}
            </GroupingNumberLabel>
          </NameTable>
        </DataTableItem>
        <DataTableItem textAlign="center">
          <CategoryLabel />
          <LanguageLabel>{data?.language?.name}</LanguageLabel>
          <ReadCountLabel>{data?.times_read}</ReadCountLabel>
          <PageCountLabel>{data?.page_count}</PageCountLabel>
          <StatusLabel>{data?.grouping?.status?.name}</StatusLabel>
        </DataTableItem>
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
        <DataTableItem name={t`Tags`}>
          <TagsTable />
        </DataTableItem>
        <DataTableItem name={t`External links`}>
          <UrlList />
        </DataTableItem>
        <DataTableItem textAlign="center">
          <LastReadLabel timestamp={data?.last_read} />
          <DatePublishedLabel timestamp={data?.pub_date} />
          <LastUpdatedLabel timestamp={data?.last_updated} />
          <DateAddedLabel timestamp={data?.timestamp} />
        </DataTableItem>
      </DataTable>
    </DataContext.Provider>
  );
}

export function DataTableItem({
  children,
  colSpan = true,
  verticalAlign,
  textAlign,
  name,
}: {
  children?: React.ReactNode;
  name?: string;
  verticalAlign?: React.ComponentProps<typeof Table.Cell>['verticalAlign'];
  textAlign?: React.ComponentProps<typeof Table.Cell>['textAlign'];
  colSpan?: boolean;
}) {
  return (
    <Table.Row>
      {!!name && (
        <Table.Cell collapsing>
          <Header size="tiny" className="sub-text">
            {name}
          </Header>
        </Table.Cell>
      )}
      <Table.Cell
        colSpan={colSpan && !name ? '2' : undefined}
        verticalAlign={verticalAlign}
        textAlign={textAlign}>
        {children}
      </Table.Cell>
    </Table.Row>
  );
}

export function DataTable({
  children,
  size,
  compact,
  showDataText,
}: {
  size?: React.ComponentProps<typeof Table>['size'];
  children?: React.ReactNode;
  showDataText?: boolean;
  compact?: boolean;
}) {
  return (
    <Table basic="very" size={size} coamp={compact ? 'very' : false}>
      {showDataText && <TextEditor />}
      <Table.Body>{children}</Table.Body>
    </Table>
  );
}
