import _ from 'lodash';
import { useCallback, useEffect, useMemo, useState } from 'react';
import {
  Button,
  Card,
  Container,
  Divider,
  Dropdown,
  Form,
  Header,
  Icon,
  Label,
  List,
  Menu,
  Modal,
  Segment,
} from 'semantic-ui-react';

import { useConfig, useSetting } from '../../client/hooks/settings';
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
import { MetadataHandler, MetadataItem } from '../../misc/types';
import GalleryCard, { galleryCardDataFields } from '../item/Gallery';
import {
  ItemCardActionContent,
  ItemCardActionContentItem,
} from '../item/index';
import { EmptyMessage, SortableList } from '../Misc';
import { IsolationLabel, OptionField } from '../Settings';
import { HandlerLabelGroup, ItemQueueBase } from './';
import { HandlerSortableItem } from './index';

function MetadataSettings(props: React.ComponentProps<typeof Modal>) {
  const [cfg, setConfig] = useConfig({
    'metadata.size': undefined as number,
    'metadata.use_applied_urls': undefined as boolean,
    'metadata.continue_fetching': undefined as boolean,
    'metadata.only_if_never_fetched': undefined as boolean,
    'metadata.stop_after_first': undefined as boolean,
    'metadata.choose_first_candidate': undefined as boolean,
    'metadata.attributes': undefined as string,
    'metadata.overwrites': undefined as string,
  });

  const [priority, setPriority] = useSetting<string[]>('metadata.priority', []);

  const { data: metadataHandlers } = useQueryType(QueryType.METADATA_INFO);

  const optionChange = useCallback(
    function f<T extends typeof cfg, K extends keyof T>(key: K, value: T[K]) {
      setConfig({ [key]: value });
    },
    [setConfig]
  );

  const [handlers, setHandlers] = useState<
    { id: string; handler: MetadataHandler; type: string }[]
  >([]);

  useEffect(() => {
    if (metadataHandlers?.data) {
      setHandlers(
        metadataHandlers.data.map((h) => ({
          id: h.identifier,
          handler: h,
          type: 'metadata',
        }))
      );
    }
  }, [metadataHandlers]);

  return (
    <Modal dimmer={false} {...props}>
      <Modal.Header>{t`Metadata Settings`}</Modal.Header>
      <Modal.Content>
        <Form>
          <OptionField
            isolation="server"
            label={t`Amount of metadata tasks allowed to run concurrently`}
            cfg={cfg}
            nskey="metadata.size"
            type="number"
            optionChange={optionChange}
          />
          <OptionField
            label={t`Lookup metadata from an item's applied URLs`}
            cfg={cfg}
            isolation="user"
            nskey="metadata.use_applied_urls"
            type="boolean"
            optionChange={optionChange}
          />
          <OptionField
            label={t`Continue metadata lookup if none is found from an item's applied URLs`}
            cfg={cfg}
            isolation="user"
            nskey="metadata.continue_fetching"
            type="boolean"
            optionChange={optionChange}
          />
          <OptionField
            label={t`Only fetch metadata for items that has not been fetched before`}
            cfg={cfg}
            isolation="user"
            nskey="metadata.only_if_never_fetched"
            type="boolean"
            optionChange={optionChange}
          />
          <OptionField
            label={t`Stop metadata lookup after first found`}
            cfg={cfg}
            isolation="user"
            nskey="metadata.stop_after_first"
            type="boolean"
            optionChange={optionChange}
          />
          <OptionField
            label={t`Choose first metadata candidate when multiple are found (for each metadata handler)`}
            cfg={cfg}
            isolation="user"
            nskey="metadata.choose_first_candidate"
            type="boolean"
            optionChange={optionChange}
          />
          <OptionField
            label={t`Specify which attributes should be written to an item`}
            help={t`Set attribute:true to 'turn on' the attribute or attribute:false to 'turn off'.
              Set __all__:true to 'turn on' all attributes not specified or __all__:false to 'turn them off'`}
            cfg={cfg}
            isolation="user"
            nskey="metadata.attributes"
            type="json"
            optionChange={optionChange}
          />
          <OptionField
            label={t`Specify how attributes should be written to an item`}
            help={t`Set attribute:true to overwrite the attribute or attribute:false to only update if applicable.
              Set __all__:true to overwrite all attributes not specified or __all__:false to only update them`}
            cfg={cfg}
            isolation="user"
            nskey="metadata.overwrites"
            type="json"
            optionChange={optionChange}
          />
        </Form>
        <Divider />
        <Container textAlign="center" className="sub-text">
          <IsolationLabel isolation="user" />
          {t`Drag item to change priority`}
        </Container>
        <List relaxed="very" ordered>
          <SortableList
            element={HandlerSortableItem}
            onItemsChange={useCallback((items) => {
              setPriority(items.map((i) => i.id));
              setHandlers(items);
            }, [])}
            onlyOnDragItem
            items={handlers.sort(
              (a, b) => priority.indexOf(a.id) - priority.indexOf(b.id)
            )}
          />
        </List>
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
        <HandlerLabelGroup type="metadata" />
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
