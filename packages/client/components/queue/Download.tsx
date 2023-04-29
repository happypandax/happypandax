import { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import { useHoverDirty } from 'react-use';
import { useRecoilValue } from 'recoil';
import {
  Card,
  Container,
  Divider,
  Form,
  Header,
  Icon,
  Image,
  Label,
  List,
  Modal,
  Ref,
  Segment,
} from 'semantic-ui-react';

import { useConfig, useSetting } from '../../client/hooks/settings';
import t from '../../client/lang';
import {
  MutatationType,
  QueryType,
  useMutationType,
  useQueryType,
} from '../../client/queries';
import {
  CommandState,
  DrawerTab,
  LogType,
  QueueType,
} from '../../shared/enums';
import { DownloadHandler, DownloadItem } from '../../shared/types';
import { AppState } from '../../state';
import { EmptyMessage } from '../misc';
import { ModalWithBack } from '../misc/BackSupport';
import { Progress } from '../misc/Progress';
import { SortableList } from '../misc/SortableList';
import { IsolationLabel, OptionField } from '../Settings';
import { HandlerLabelGroup, HandlerSortableItem, ItemQueueBase } from './index';

function DownloadItemCard({
  item,
  onUpdate,
}: {
  item: DownloadItem;
  onUpdate?: () => any;
}) {
  const ref = useRef<HTMLDivElement>();
  const [removing, setRemoving] = useState(false);

  const removeItem = useMutationType(MutatationType.REMOVE_ITEM_FROM_QUEUE, {
    onMutate: () => setRemoving(false),
    onSettled: () => {
      onUpdate?.();
    },
  });

  let lbl: React.ReactNode = item.subtitle
    ? item.subtitle
    : item.text
    ? item.text
    : '';

  const color = item.success ? 'green' : 'red';

  if ([CommandState.Finished, CommandState.Failed].includes(item.state)) {
    lbl = <Icon name={item.success ? 'check' : 'remove'} color={color} />;
  } else if (item.state === CommandState.Stopped) {
    lbl = <Icon name="remove" />;
  }

  const hovered = useHoverDirty(ref);

  return (
    <Ref innerRef={ref}>
      <Card className="horizontal" link>
        <Image
          src={item.thumbnail_url ?? '/img/default.png'}
          className="tiny-size"
          alt=""
        />
        <Card.Content>
          <Card.Header className="text-ellipsis">
            {item.title ? item.title : item.url}
          </Card.Header>
          <Card.Meta className="text-ellipsis">
            {item?.title ? item.url : item.thumbnail_url}
          </Card.Meta>
          <Card.Description>
            {item.state !== CommandState.InQueue && (
              <Progress
                error={item.state === CommandState.Failed}
                success={item.state === CommandState.Finished && item.success}
                warning={item.state === CommandState.Finished && !item.success}
                indicating={item.active}
                percent={item.active ? item.percent : 100}
                active={item.active}>
                {lbl}
              </Progress>
            )}
            {item.state === CommandState.InQueue && (
              <div className="ui placeholder fluid">
                <div className="very long line" />
              </div>
            )}
          </Card.Description>
        </Card.Content>
      </Card>
    </Ref>
  );
}

function DownloadSettings(props: React.ComponentProps<typeof Modal>) {
  const [cfg, setConfig] = useConfig({
    'download.size': undefined as number,
    'download.skip_if_downloaded_before': undefined as boolean,
    'download.skip_if_item_exists': undefined as boolean,
    'download.delete_failed_downloads': undefined as boolean,
    'download.import': undefined as boolean,
    'download.download_cache_dir': undefined as string,
    'download.download_dir': undefined as string,
    'download.options': undefined as object,
  });

  const [priority, setPriority] = useSetting<string[]>('download.priority', []);

  const { data: downloadHandlers } = useQueryType(QueryType.DOWNLOAD_INFO);

  const optionChange = useCallback(
    function f<T extends typeof cfg, K extends keyof T>(key: K, value: T[K]) {
      setConfig({ [key]: value });
    },
    [setConfig]
  );

  const [handlers, setHandlers] = useState<
    { id: string; handler: DownloadHandler; type: string }[]
  >([]);

  useEffect(() => {
    if (downloadHandlers?.data) {
      setHandlers(
        downloadHandlers.data.map((h) => ({
          id: h.identifier,
          handler: h,
          type: 'download',
        }))
      );
    }
  }, [downloadHandlers]);

  return (
    <ModalWithBack dimmer={false} {...props}>
      <Modal.Header>{t`Download Settings`}</Modal.Header>
      <Modal.Content>
        <Form>
          <OptionField
            isolation="server"
            label={t`Amount of download tasks allowed to run concurrently`}
            cfg={cfg}
            nskey="download.size"
            type="number"
            optionChange={optionChange}
          />
          <OptionField
            label={t`Import item after download`}
            cfg={cfg}
            isolation="user"
            nskey="download.import"
            type="boolean"
            optionChange={optionChange}
          />
          <OptionField
            label={t`Skip import if item already exists in the database`}
            cfg={cfg}
            isolation="user"
            nskey="download.skip_if_item_exists"
            type="boolean"
            optionChange={optionChange}
          />
          <OptionField
            label={t`Skip a download URL if it has been successfully downloaded before`}
            cfg={cfg}
            isolation="user"
            nskey="download.skip_if_downloaded_before"
            type="boolean"
            optionChange={optionChange}
          />
          <OptionField
            label={t`Clean left-over files if downloading fails`}
            cfg={cfg}
            isolation="user"
            nskey="download.delete_failed_downloads"
            type="boolean"
            optionChange={optionChange}
          />
          <OptionField
            label={t`Download folder`}
            cfg={cfg}
            isolation="user"
            nskey="download.download_dir"
            type="string"
            optionChange={optionChange}
          />
          <OptionField
            label={t`Download cache folder`}
            cfg={cfg}
            isolation="user"
            nskey="download.download_cache_dir"
            type="string"
            optionChange={optionChange}
          />
          <OptionField
            label={t`Overwritten options`}
            help={t`A mapping of setting:value, where setting is a fully qualified name of a config setting name that should be overwritten only during download.
            For example: { 'import.move_gallery' : true, 'import.move_dir': 'some/other/path' } will move only downloaded galleries to 'some/other/path' during import`}
            cfg={cfg}
            isolation="user"
            nskey="download.options"
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
    </ModalWithBack>
  );
}

export function DownloadQueue({
  logDefaultVisible,
  logExpanded,
}: {
  logDefaultVisible?: boolean;
  logExpanded?: boolean;
}) {
  const drawerTab = useRecoilValue(AppState.drawerTab);

  const [active, setActive] = useState(true);
  const [url, setUrl] = useState('');

  const ref = useRef<HTMLInputElement>();

  const refetchEvery = 5000;

  const { data: queueState } = useQueryType(
    QueryType.QUEUE_STATE,
    {
      queue_type: QueueType.Download,
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
      queue_type: QueueType.Download,
    },
    {
      refetchInterval: active ? refetchEvery : false,
      keepPreviousData: true,
      refetchOnMount: 'always',
    }
  );

  const addItem = useMutationType(MutatationType.ADD_URLS_TO_DOWNLOAD_QUEUE);

  useEffect(() => {
    if (drawerTab === DrawerTab.Download) {
      ref.current.getElementsByTagName('input').item(0).focus();
    }
  }, [drawerTab]);

  return (
    <>
      <Segment basic className="no-margins">
        <Form
          onSubmit={useCallback(
            (e) => {
              e.preventDefault();
              if (url) {
                addItem.mutate({ urls: [url] });
                setUrl('');
              }
              refetchQueueItems();
            },
            [url]
          )}>
          <Ref innerRef={ref}>
            <Form.Input
              name="url"
              focus
              fluid
              value={url}
              onChange={useCallback((e) => setUrl(e.target.value), [])}
              placeholder="https://..."
              size="mini"
              action={useMemo(() => ({ icon: 'plus', color: 'teal' }), [])}
            />
          </Ref>
        </Form>
      </Segment>
      <ItemQueueBase
        logDefaultVisible={logDefaultVisible}
        logExpanded={logExpanded}
        queue_type={QueueType.Download}
        log_type={LogType.Download}
        Settings={DownloadSettings}
        refetch={refetchQueueItems}
        running={queueState?.data?.running}
        active_size={queueState?.data?.active?.length}
        queue_size={queueState?.data?.size}
        onActive={setActive}
      />
      <Header size="tiny" textAlign="center" className="no-margins sub-text">
        <HandlerLabelGroup type="download" />
      </Header>
      {!!queueItems?.data?.length && (
        <Segment tertiary className="no-margin-top">
          <Card.Group itemsPerRow={2} doubling>
            {queueItems?.data?.map?.((i) => (
              <DownloadItemCard
                key={i.item_id}
                item={i as DownloadItem}
                onUpdate={refetchQueueItems}
              />
            ))}
          </Card.Group>
        </Segment>
      )}
      {!queueItems?.data?.length && <EmptyMessage className="h-full" />}
    </>
  );
}

export function DownloadLabel() {
  const [interval, setInterval] = useState(5000);

  const { data } = useQueryType(
    QueryType.QUEUE_STATE,
    {
      queue_type: QueueType.Download,
    },
    {
      refetchInterval: interval,
      refetchOnMount: 'always',
    }
  );

  useEffect(() => {
    setInterval(data?.data?.running ? 5000 : 25000);
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
