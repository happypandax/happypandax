import { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import { useHoverDirty } from 'react-use';
import { useRecoilValue } from 'recoil';
import {
  Card,
  Checkbox,
  Form,
  Header,
  Icon,
  Image,
  Label,
  Modal,
  Progress,
  Ref,
  Segment,
  Select,
} from 'semantic-ui-react';

import {
  MutatationType,
  QueryType,
  useMutationType,
  useQueryType,
} from '../../client/queries';
import { CommandState, DrawerTab, LogType, QueueType } from '../../misc/enums';
import t from '../../misc/lang';
import { DownloadItem } from '../../misc/types';
import { AppState } from '../../state';
import { EmptyMessage } from '../Misc';
import { ItemQueueBase } from './index';

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

  if ([CommandState.finished, CommandState.failed].includes(item.state)) {
    lbl = <Icon name={item.success ? 'check' : 'remove'} color={color} />;
  } else if (item.state === CommandState.stopped) {
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
            {item.state !== CommandState.in_queue && (
              <Progress
                error={item.state === CommandState.failed}
                success={item.state === CommandState.finished && item.success}
                warning={item.state === CommandState.finished && !item.success}
                indicating={item.active}
                percent={item.active ? item.percent : 100}
                active={item.active}>
                {lbl}
              </Progress>
            )}
            {item.state === CommandState.in_queue && (
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

function DownloadSettings({ trigger }: { trigger: React.ReactNode }) {
  return (
    <Modal trigger={trigger} dimmer={false}>
      <Modal.Header>{t`Download Settings`}</Modal.Header>
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

export function DownloadQueue() {
  const drawerTab = useRecoilValue(AppState.drawerTab);

  const [active, setActive] = useState(true);
  const [url, setUrl] = useState('');

  const ref = useRef<HTMLInputElement>();

  const { data: downloadHandlers } = useQueryType(QueryType.DOWNLOAD_INFO);

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
        queue_type={QueueType.Download}
        log_type={LogType.Download}
        Settings={DownloadSettings}
        refetch={refetchQueueItems}
        running={queueState?.data?.running}
        onActive={setActive}
      />
      <Header size="tiny" textAlign="center" className="no-margins sub-text">
        {!downloadHandlers?.data?.length && t`No handlers activated`}
        {!!downloadHandlers?.data?.length && (
          <Label.Group>
            {downloadHandlers?.data?.map?.((h, i) => (
              <Label size="small" key={h.identifier}>
                {i + 1}
                <Label.Detail>{h.identifier}</Label.Detail>
              </Label>
            ))}
          </Label.Group>
        )}
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
      include_finished: false,
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
