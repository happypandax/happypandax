import React, { useCallback, useContext } from 'react';
import { useRecoilState, useRecoilValue } from 'recoil';
import {
  Button,
  Container,
  Divider,
  Icon,
  Label,
  Popup,
  Segment,
  Table,
  TransitionablePortal,
} from 'semantic-ui-react';

import { DataContext, ReaderContext } from '../../client/context';
import { useSetupDataState } from '../../client/hooks/item';
import t from '../../client/lang';
import { QueryType, useQueryType } from '../../client/queries';
import { ItemType } from '../../shared/enums';
import { ReaderData, ServerGallery } from '../../shared/types';
import { ReaderState } from '../../state';
import { FavoriteLabel, TagsTable } from '../dataview/Common';
import GalleryCard, { GalleryCardData } from '../item/Gallery';

export function ReaderAutoNavigateButton({
  ...props
}: React.ComponentProps<typeof Button>) {
  const { stateKey } = useContext(ReaderContext);

  const [autoNavigate, setAutoNavigate] = useRecoilState(
    ReaderState.autoNavigate(stateKey)
  );

  const pageNumber = useRecoilValue(ReaderState.pageNumber(stateKey));
  const pageCount = useRecoilValue(ReaderState.pageCount(stateKey));
  const autoNavigateCounter = useRecoilValue(
    ReaderState.autoNavigateCounter(stateKey)
  );

  return (
    <Popup
      content={t`Auto navigate`}
      inverted
      position="top center"
      trigger={
        <Button
          icon={
            autoNavigate
              ? pageNumber >= pageCount
                ? 'pause'
                : 'play'
              : 'pause'
          }
          content={
            autoNavigate && autoNavigateCounter && autoNavigateCounter <= 10
              ? autoNavigateCounter
              : undefined
          }
          secondary
          color={
            autoNavigate
              ? pageNumber >= pageCount
                ? 'orange'
                : 'green'
              : undefined
          }
          basic
          circular
          {...props}
          onClick={useCallback(() => {
            setAutoNavigate(!autoNavigate);
          }, [autoNavigate])}
        />
      }
    />
  );
}

export function ReaderAutoScrollButton({
  ...props
}: React.ComponentProps<typeof Button>) {
  const { stateKey } = useContext(ReaderContext);

  const endReached = useRecoilValue(ReaderState.endReached(stateKey));
  const [autoScroll, setAutoScroll] = useRecoilState(
    ReaderState.autoScroll(stateKey)
  );

  return (
    <Popup
      content={t`Auto scroll`}
      inverted
      position="top center"
      trigger={
        <Button
          icon="lightning"
          secondary
          color={autoScroll ? (endReached ? 'orange' : 'green') : undefined}
          basic
          circular
          {...props}
          onClick={useCallback(() => {
            setAutoScroll(!autoScroll);
          }, [autoScroll])}
        />
      }
    />
  );
}

type PageInfoData = ReaderData & {};

export function PageInfo({
  onClose,
  item,
  container,
}: {
  item: GalleryCardData;
  container?: boolean;
  onClose?: () => void;
}) {
  const { stateKey } = useContext(ReaderContext);
  const page = useRecoilValue(ReaderState.page(stateKey));
  const { data: initialData } = useQueryType(
    QueryType.ITEM,
    {
      item_type: ItemType.Page,
      item_id: page?.id,
      fields: [
        'tags',
        'path',
        'name',
        'number',
        'metatags.favorite',
        'metatags.inbox',
        'metatags.trash',
      ],
    },
    { placeholderData: page, enabled: !!page }
  );

  const { data: initalGalleryData } = useQueryType(
    QueryType.ITEM,
    {
      item_type: ItemType.Gallery,
      item_id: item?.id,
      fields: ['tags.tag.name', 'tags.namespace.name'],
    },
    {
      placeholderData: undefined as DeepPick<ServerGallery, 'id' | 'tags'>,
      enabled: !!item?.id,
    }
  );

  const { data, dataContext } = useSetupDataState<PageInfoData>({
    initialData: initialData?.data,
    itemType: ItemType.Page,
  });

  const { dataContext: galleryDataContext } = useSetupDataState({
    initialData: initalGalleryData?.data,
    itemType: ItemType.Gallery,
    key: 'pageinfo',
  });

  return (
    <DataContext.Provider value={dataContext}>
      <Segment as={container ? Container : undefined}>
        <Label as="a" attached="top right" onClick={onClose}>
          <Icon name="close" fitted />
        </Label>
        <Divider horizontal>
          <Label className="left" circular>
            {page?.number}
          </Label>
        </Divider>
        <GalleryCard fluid data={item} size="tiny" horizontal />
        <Table basic="very">
          <Table.Body>
            <Table.Row>
              <Table.Cell singleLine textAlign="center" colSpan={2}>
                {t`Like this page?`}
                <FavoriteLabel />
              </Table.Cell>
            </Table.Row>
            <Table.Row>
              <Table.Cell collapsing>{t`Page tags`}:</Table.Cell>
              <Table.Cell>
                <TagsTable />
              </Table.Cell>
            </Table.Row>
            <Table.Row>
              <Table.Cell collapsing>{t`Parent tags`}:</Table.Cell>
              <Table.Cell>
                <DataContext.Provider value={galleryDataContext}>
                  <TagsTable />
                </DataContext.Provider>
              </Table.Cell>
            </Table.Row>
            <Table.Row>
              <Table.Cell collapsing>{t`Path`}:</Table.Cell>
              <Table.Cell>
                <Label basic>{data?.path}</Label>
              </Table.Cell>
            </Table.Row>
          </Table.Body>
        </Table>
      </Segment>
    </DataContext.Provider>
  );
}

export function PageInfoPortal({
  open,
  onClose,
  ...props
}: {
  open?: boolean;
} & React.ComponentProps<typeof PageInfo>) {
  return (
    <TransitionablePortal open={open} onClose={onClose}>
      <div id="drawer">
        <PageInfo {...props} onClose={onClose} />
      </div>
    </TransitionablePortal>
  );
}
