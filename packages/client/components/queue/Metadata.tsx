import _ from 'lodash';
import { useCallback, useEffect, useMemo, useState } from 'react';
import {
  Button,
  Card,
  Checkbox,
  Dropdown,
  Form,
  Header,
  Icon,
  Label,
  Menu,
  Modal,
  Segment,
  Select,
} from 'semantic-ui-react';

import {
  MutatationType,
  QueryType,
  useMutationType,
  useQueryType,
} from '../../client/queries';
import {
  CommandState,
  ImageSize,
  ItemsKind,
  ItemType,
  LogType,
  QueueType,
} from '../../misc/enums';
import t from '../../misc/lang';
import { MetadataItem } from '../../misc/types';
import GalleryCard, { galleryCardDataFields } from '../item/Gallery';
import {
  ItemCardActionContent,
  ItemCardActionContentItem,
} from '../item/index';
import { EmptyMessage } from '../Misc';
import { ItemQueueBase } from './';

function MetadataSettings({ trigger }: { trigger: React.ReactNode }) {
  return (
    <Modal trigger={trigger} dimmer={false}>
      <Modal.Header>{t`Metadata Settings`}</Modal.Header>
      <Modal.Content>
        <Form>
          <Form.Group inline>
            <label>{t`Display`}</label>
            <Form.Radio label={t`Card`} value="card" />
            <Form.Radio label={t`List`} value="list" />
          </Form.Group>

          <Form.Group inline>
            <label>{t`Default view`}</label>
            <Form.Radio label={t`All`} />
            <Form.Radio label={t`Library`} />
            <Form.Radio label={t`Inbox`} />
          </Form.Group>

          <Form.Field
            control={Select}
            label={t`Items per page`}
            placeholder={t`Items per page`}
            onChange={useCallback((ev, { value }) => {
              ev.preventDefault();
              setLimit(parseInt(value, 10));
            }, [])}
            // width={4}
          />

          <Form.Field
            control={Select}
            label={t`Default item`}
            placeholder={t`Default item`}
            onChange={useCallback((ev, data) => {
              ev.preventDefault();
            }, [])}
            value={30}
            defaultValue={30}
            // width={4}
          />

          <Form.Field
            control={Select}
            label={t`Default sort`}
            placeholder={t`Default sort`}
            onChange={useCallback((ev, data) => {
              ev.preventDefault();
            }, [])}
            value={30}
            defaultValue={30}
            // width={4}
          />

          <Form.Field
            control={Select}
            label={t`Default sort order`}
            placeholder={t`Default sort order`}
            onChange={useCallback((ev, data) => {
              ev.preventDefault();
            }, [])}
            value={30}
            defaultValue={30}
            // width={4}
          />

          <Form.Field
            control={Select}
            label={t`Default filter`}
            placeholder={t`Default filter`}
            onChange={useCallback((ev, data) => {
              ev.preventDefault();
            }, [])}
            value={30}
            defaultValue={30}
            // width={4}
          />

          <Form.Field>
            <label>{t`Infinite scroll`}</label>
            <Checkbox
              toggle
              onChange={useCallback((ev, { checked }) => {
                ev.preventDefault();
                setInfinite(checked);
              }, [])}
            />
          </Form.Field>
        </Form>
      </Modal.Content>
    </Modal>
  );
}

function MetadataItemState({ item }: { item: MetadataItem }) {
  return (
    <Header inverted size="tiny">
      {item.active && <Icon name="asterisk" loading />}
      {item.state === CommandState.finished && (
        <Icon name="check" color="green" />
      )}
      {item.state === CommandState.stopped && (
        <Icon name="exclamation circle" color="orange" />
      )}
      {item.state === CommandState.failed && (
        <Icon name="exclamation triangle" color="red" />
      )}
      <Header.Content>
        {item.subtitle && item.text
          ? item.subtitle
          : item.title
          ? item.title
          : t`Fetching...`}
        <Header.Subheader>{item.text || item.subtitle}</Header.Subheader>
      </Header.Content>
    </Header>
  );
}

function MetadataItemActionContent({
  item,
  onUpdate,
}: {
  item: MetadataItem;
  onUpdate?: () => any;
}) {
  const [removing, setRemoving] = useState(false);

  const removeItem = useMutationType(MutatationType.REMOVE_ITEM_FROM_QUEUE, {
    onMutate: () => setRemoving(false),
    onSettled: () => {
      onUpdate?.();
    },
  });

  return (
    <ItemCardActionContent>
      <ItemCardActionContentItem>
        <Button
          size="tiny"
          loading={removing}
          color="red"
          onClick={useCallback((e) => {
            e.preventDefault();
            removeItem.mutate({
              item_id: item.item_id,
              item_type: item.item_type,
              queue_type: QueueType.Metadata,
            });
          }, [])}>{t`Remove`}</Button>
      </ItemCardActionContentItem>
    </ItemCardActionContent>
  );
}

export function MetadataQueue() {
  const [addLoading, setAddLoading] = useState(false);
  const [active, setActive] = useState(true);

  const { data: metadataHandlers } = useQueryType(QueryType.METADATA_INFO);

  const refetchEvery = 5000;

  const { data: queueState } = useQueryType(
    QueryType.QUEUE_STATE,
    {
      queue_type: QueueType.Metadata,
    },
    {
      refetchInterval: active ? refetchEvery : false,
      keepPreviousData: true,
      refetchOnMount: 'always',
    }
  );

  const { data: queueItems, refetch: refetchQueueItems } = useQueryType(
    QueryType.QUEUE_ITEMS,
    {
      queue_type: QueueType.Metadata,
    },
    {
      refetchInterval: active ? refetchEvery : false,
      keepPreviousData: true,
      refetchOnMount: 'always',
    }
  );

  const addItems = useMutationType(MutatationType.ADD_ITEMS_TO_METADATA_QUEUE, {
    onMutate: () => setAddLoading(true),
    onSettled: () => {
      refetchQueueItems().finally(() => setAddLoading(false));
    },
  });

  const { data: items, isLoading } = useQueryType(
    QueryType.ITEM,
    {
      item_type: ItemType.Gallery,
      item_id: queueItems?.data?.map((i) => i.item_id),
      fields: galleryCardDataFields,
      profile_options: { size: ImageSize.Small },
    },
    { enabled: !!queueItems?.data?.length, refetchOnMount: 'always' }
  );

  const queueItemsMap = _.keyBy(queueItems?.data, 'item_id');

  return (
    <>
      <ItemQueueBase
        queue_type={QueueType.Metadata}
        log_type={LogType.Metadata}
        Settings={MetadataSettings}
        refetch={refetchQueueItems}
        running={queueState?.data?.running}
        onActive={setActive}
        menuItems={useMemo(
          () => (
            <Dropdown
              item
              icon="plus"
              loading={addLoading}
              compact
              text={t`Add`}
              upward={false}>
              <Dropdown.Menu>
                <Dropdown.Item
                  onClick={() =>
                    addItems.mutate({ items_kind: ItemsKind.all_items })
                  }
                  text={t`All galleries`}
                />
                <Dropdown.Item
                  onClick={() =>
                    addItems.mutate({
                      items_kind: ItemsKind.tags_missing_items,
                    })
                  }
                  text={t`Galleries with missing tags`}
                />
                <Dropdown.Item
                  onClick={() =>
                    addItems.mutate({ items_kind: ItemsKind.library_items })
                  }
                  text={t`Library: Galleries`}
                />
                <Dropdown.Item
                  onClick={() =>
                    addItems.mutate({
                      items_kind: ItemsKind.tags_missing_library_items,
                    })
                  }
                  text={t`Library: Galleries with missing tags`}
                />
                <Dropdown.Item
                  onClick={() =>
                    addItems.mutate({ items_kind: ItemsKind.inbox_items })
                  }
                  text={t`Inbox: Galleries`}
                />
                <Dropdown.Item
                  onClick={() =>
                    addItems.mutate({
                      items_kind: ItemsKind.tags_missing_inbox_items,
                    })
                  }
                  text={t`Inbox: Galleries with missing tags`}
                />
              </Dropdown.Menu>
            </Dropdown>
          ),
          []
        )}
      />
      <Header size="tiny" textAlign="center" className="no-margins sub-text">
        {!metadataHandlers?.data?.length && t`No handlers activated`}
        {!!metadataHandlers?.data?.length && (
          <Label.Group>
            {metadataHandlers?.data?.map?.((h, i) => (
              <Label size="small" key={h.identifier}>
                {i + 1}
                <Label.Detail>{h.identifier}</Label.Detail>
              </Label>
            ))}
          </Label.Group>
        )}
      </Header>
      {!items?.data?.length && <EmptyMessage className="h-full" />}
      {!!items?.data?.length && (
        <Segment tertiary loading={isLoading || addLoading}>
          <Card.Group itemsPerRow={2} doubling>
            {items?.data?.map?.((i) => (
              <GalleryCard
                hiddenLabel
                activity={(queueItemsMap[i.id] as MetadataItem).active}
                hiddenAction={false}
                actionContent={() => (
                  <MetadataItemActionContent
                    item={queueItemsMap[i.id] as MetadataItem}
                    onUpdate={refetchQueueItems}
                  />
                )}
                activityContent={
                  <MetadataItemState
                    item={queueItemsMap[i.id] as MetadataItem}
                  />
                }
                key={i.id}
                data={i}
                horizontal
                size="mini"
              />
            ))}
          </Card.Group>
        </Segment>
      )}
    </>
  );
}

export function MetadataLabel() {
  const [interval, setInterval] = useState(5000);

  // TODO: use QueryObserver?

  const { data } = useQueryType(
    QueryType.QUEUE_STATE,
    {
      queue_type: QueueType.Metadata,
      include_finished: false,
    },
    {
      refetchInterval: interval,
      refetchOnMount: 'always',
    }
  );

  useEffect(() => {
    setInterval(data?.data?.running && data?.data?.size ? 5000 : 25000);
  }, [data]);

  const size = data?.data?.size;

  return (
    <Label
      color={data?.data?.running ? 'green' : 'red'}
      circular
      content={size}
    />
  );
}
