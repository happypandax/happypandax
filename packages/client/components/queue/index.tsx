import { useCallback, useEffect, useState } from 'react';
import { Icon, Loader, Menu } from 'semantic-ui-react';

import { MutatationType, useMutationType } from '../../client/queries';
import { LogType, QueueType } from '../../misc/enums';
import t from '../../misc/lang';
import { ServerLog } from '../Misc';

export function ItemQueueBase({
  Settings,
  refetch,
  onActive,
  running,
  log_type,
  queue_type,
  menuItems,
}: {
  Settings: React.ElementType;
  running: boolean;
  log_type: LogType;
  queue_type: QueueType;
  onActive: (boolean) => void;
  refetch: () => Promise<any>;
  menuItems?: React.ReactNode;
}) {
  const [runningLoading, setRunningLoading] = useState(false);
  const [clearLoading, setClearLoading] = useState(false);
  const [active, setActive] = useState(true);
  const [logVisible, setLogVisible] = useState(false);

  const clearQueue = useMutationType(MutatationType.CLEAR_QUEUE, {
    onMutate: () => setClearLoading(true),
    onSettled: () => refetch().finally(() => setClearLoading(false)),
  });

  const stopQueue = useMutationType(MutatationType.STOP_QUEUE, {
    onMutate: () => {
      setActive(false), setRunningLoading(true);
    },
    onSettled: () => setRunningLoading(false),
  });
  const startQueue = useMutationType(MutatationType.START_QUEUE, {
    onMutate: () => {
      setActive(true), setRunningLoading(true);
    },
    onSettled: () => setRunningLoading(false),
  });

  useEffect(() => {
    setActive(running);
  }, [running]);

  useEffect(() => {
    onActive?.(active);
  }, [active]);

  return (
    <>
      <Menu labeled compact text fluid>
        <Menu.Item
          disabled={runningLoading}
          onClick={useCallback(() => {
            if (active) {
              stopQueue.mutate({ queue_type });
            } else {
              startQueue.mutate({ queue_type });
            }
          }, [active])}>
          <Loader active={runningLoading} size="small" />
          <Icon
            name={active ? 'play' : 'pause'}
            color={active ? 'green' : 'red'}
          />{' '}
          {active ? t`Running` : t`Paused`}
        </Menu.Item>
        <Menu.Item
          disabled={clearLoading}
          onClick={useCallback(() => {
            clearQueue.mutate({ queue_type });
          }, [])}>
          <Loader active={clearLoading} size="small" />
          <Icon name="remove" /> {t`Clear`}
        </Menu.Item>
        <Menu.Menu position="right">
          <Menu.Item
            onClick={useCallback(() => setLogVisible(!logVisible), [
              logVisible,
            ])}>
            <Icon name={logVisible ? 'angle down' : 'angle right'} /> {t`Log`}
          </Menu.Item>
          <Settings
            trigger={
              <Menu.Item>
                <Icon name="setting" /> {t`Options`}
              </Menu.Item>
            }
          />
          {menuItems}
        </Menu.Menu>
      </Menu>
      {logVisible && (
        <ServerLog
          type={log_type}
          className="max-100-h no-margins"
          attached="top"
        />
      )}
    </>
  );
}
