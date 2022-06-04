import _ from 'lodash';
import { useCallback, useEffect, useMemo, useRef, useState } from 'react';
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
  Loader,
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
import { MetadataHandler, MetadataItem, ServerGallery } from '../../misc/types';
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

  const genItemsMap = () => ({
    ..._.keyBy(queueState?.data?.queued, 'item_id'),
    ..._.keyBy(queueState?.data?.active, 'item_id'),
    ..._.keyBy(queueState?.data?.finished, 'item_id'),
  });

  const refetchEvery =
    !active && !addLoading ? 10000 : addLoading ? 3500 : 5000;

  const { data: queueState, refetch } = useQueryType(
    QueryType.QUEUE_STATE,
    {
      queue_type: QueueType.Metadata,
      include_active: true,
      include_finished: true,
      include_queued: true,
    },
    {
      refetchInterval: refetchEvery,
      keepPreviousData: true,
      refetchOnMount: 'always',
      onSettled: () => {
        itemsMapRef.current = { ...itemsMapRef.current, ...genItemsMap() };
        console.debug('count', Object.keys(itemsMapRef.current).length);
      },
    }
  );

  const itemsMapRef = useRef(genItemsMap());

  const itemsMap = itemsMapRef.current;

  const addItems = useMutationType(MutatationType.ADD_ITEMS_TO_METADATA_QUEUE, {
    onMutate: () => {
      setAddLoading(true);
      setTimeout(() => refetch(), 300);
    },
    onSettled: () => {
      refetch().finally(() => setAddLoading(false));
    },
  });

  const hasActiveItems = !!queueState?.data?.active?.length;

  const { data: activeItems, isLoading: isLoadingActive } = useQueryType(
    QueryType.ITEM,
    {
      item_type: ItemType.Gallery,
      item_id: queueState?.data?.active?.map?.((i) => i.item_id),
      fields: galleryCardDataFields,
      profile_options: { size: ImageSize.Small },
    },
    {
      enabled: hasActiveItems,
      keepPreviousData: hasActiveItems,
    }
  );

  const hasFinishedItems = !!queueState?.data?.finished?.length;

  const { data: finishedItems, isLoading: isLoadingFinished } = useQueryType(
    QueryType.ITEM,
    {
      item_type: ItemType.Gallery,
      item_id: queueState?.data?.finished
        ?.slice?.(0, 10)
        ?.map?.((i) => i.item_id),
      fields: galleryCardDataFields,
      profile_options: { size: ImageSize.Small },
    },
    {
      enabled: hasFinishedItems,
      keepPreviousData: hasFinishedItems,
    }
  );

  const hasQueueItems = !!queueState?.data?.queued?.length;

  const { data: queuedItems, isLoading: isLoadingQueued } = useQueryType(
    QueryType.ITEM,
    {
      item_type: ItemType.Gallery,
      item_id: queueState?.data?.queued
        ?.slice?.(0, 50)
        ?.map?.((i) => i.item_id),
      fields: galleryCardDataFields,
      profile_options: { size: ImageSize.Small },
    },
    {
      enabled: hasQueueItems,
      keepPreviousData: hasQueueItems,
    }
  );

  const itemMap = (i: ServerGallery) => {
    if (!itemsMap[i.id]) return null;
    return (
      <GalleryCard
        hiddenLabel
        activity={(itemsMap[i.id] as MetadataItem).active}
        hiddenAction={false}
        actionContent={
          !(itemsMap[i.id] as MetadataItem).active
            ? () => (
                <MetadataItemActionContent
                  item={itemsMap[i.id] as MetadataItem}
                  onUpdate={refetch}
                />
              )
            : undefined
        }
        activityContent={
          <MetadataItemState item={itemsMap[i.id] as MetadataItem} />
        }
        key={i.id}
        data={i}
        horizontal
        size="mini"
      />
    );
  };

  const isEmpty = !(
    queueState?.data?.active?.length ||
    queueState?.data?.finished?.length ||
    queueState?.data?.queued?.length
  );

  console.debug('queueState', queueState?.data);

  return (
    <>
      <ItemQueueBase
        queue_type={QueueType.Metadata}
        log_type={LogType.Metadata}
        Settings={MetadataSettings}
        refetch={refetch}
        running={queueState?.data?.running}
        active_size={queueState?.data?.active_size}
        queue_size={queueState?.data?.queued_size}
        percent={queueState?.data?.percent}
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
      {isEmpty && <EmptyMessage loading={isLoadingActive} className="h-full" />}
      {!!activeItems?.data?.length && (
        <Segment tertiary>
          <Card.Group itemsPerRow={2} doubling>
            {activeItems?.data?.map?.(itemMap)}
          </Card.Group>
        </Segment>
      )}
      <Divider fitted horizontal>
        <Header as="h5" className="load">
          <Segment basic className="small-padding-segment">
            {t`Finished`}
            <Loader size="small" active={isLoadingFinished} />
          </Segment>
        </Header>
      </Divider>
      {isEmpty && (
        <EmptyMessage loading={isLoadingFinished} className="h-full" />
      )}
      {!!finishedItems?.data?.length && (
        <Segment tertiary>
          <Card.Group itemsPerRow={2} doubling>
            {finishedItems?.data?.map?.(itemMap)}
          </Card.Group>
        </Segment>
      )}
      <Divider fitted horizontal>
        <Header as="h5">
          <Segment basic className="small-padding-segment">
            {t`Queue`}
            <Loader size="small" active={isLoadingQueued || addLoading} />
          </Segment>
        </Header>
      </Divider>
      {isEmpty && (
        <EmptyMessage
          loading={isLoadingQueued || addLoading}
          className="h-full"
        />
      )}
      {!!queuedItems?.data?.length && (
        <Segment tertiary>
          <Card.Group itemsPerRow={1} doubling>
            {queuedItems?.data?.map?.(itemMap)}
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
