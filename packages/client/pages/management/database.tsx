import { NextPageContext } from 'next';
import { useEffect, useState } from 'react';
import { useLocalStorage, useUpdateEffect } from 'react-use';
import { Button, Container, Dropdown, Segment, Tab } from 'semantic-ui-react';

import { useCommand } from '../../client/command';
import t from '../../client/lang';
import {
  MutatationType,
  QueryType,
  useMutationType,
  useQueryType,
} from '../../client/queries';
import { PageTitle } from '../../components/misc';
import { Progress } from '../../components/misc/Progress';
import { ServiceType } from '../../server/constants';
import { CommandState } from '../../shared/enums';
import { CommandProgress } from '../../shared/types';
import ManagementPage from './index';

interface PageProps {}

const limit = 100;

export async function getServerSideProps(context: NextPageContext) {
  const server = await global.app.service
    .get(ServiceType.Server)
    .context(context);

  return {
    props: {},
  };
}

function SearchIndexPane() {
  const [storedValue, setStoredValue] = useLocalStorage(
    '_search_index_cmd',
    ''
  );

  const { data, mutate } = useMutationType(MutatationType.REINDEX, {
    onSuccess(data, variables, context) {
      setProgressId(data.data);
    },
  });

  const [progressId, setProgressId] = useState(
    data?.data || storedValue ? storedValue : undefined
  );

  useCommand(
    data?.data || storedValue ? storedValue : undefined,
    {
      onError: () => {
        setProgressId(undefined);
      },
    },
    () => {
      setProgressId(undefined);
    },
    []
  );

  const { data: progressData } = useQueryType(
    QueryType.COMMAND_PROGRESS,
    {
      command_ids: [progressId ?? storedValue],
      __options: {
        notifyError: false,
      },
    },
    {
      enabled: !!progressId || !!storedValue,
      refetchInterval: 1000,
      onError: () => {
        setProgressId(undefined);
        setStoredValue('');
      },
    }
  );

  const prog = progressData?.data as Record<string, CommandProgress>;
  const running = prog?.[progressId as string]?.state === CommandState.Started;

  useUpdateEffect(() => {
    setStoredValue(progressId || '');
  }, [progressId]);

  useEffect(() => {
    if (progressData?.data && !running) {
      setProgressId(undefined);
    }
  }, [running]);

  const [reindexLimit, setReindexLimit] = useState(0);

  return (
    <Tab.Pane>
      <Progress
        indeterminate={running ? 'pulsating' : undefined}
        color="blue"
      />
      <Button.Group>
        <Button
          disabled={running}
          primary
          onClick={() => {
            mutate({ limit: reindexLimit });
          }}>{t`Rebuild Index`}</Button>
        <Dropdown
          disabled={running}
          className="button icon"
          floating
          defaultValue={reindexLimit}
          onChange={(_, { value }) => {
            setReindexLimit(value as number);
          }}
          options={[
            { text: t`All items`, value: 0 },
            { text: t`100 recently added items`, value: 100 },
            { text: t`500 recently added items`, value: 500 },
            { text: t`1000 recently added items`, value: 1000 },
          ]}
          trigger={<></>}
        />
      </Button.Group>{' '}
      <Button.Group>
        <Button disabled>{t`Rebuild library index`}</Button>
        <Dropdown
          disabled={running || true}
          className="button icon"
          floating
          options={[]}
          trigger={<></>}
        />
      </Button.Group>{' '}
      <Button.Group>
        <Button disabled>{t`Rebuild inbox index`}</Button>
        <Dropdown
          disabled={running || true}
          className="button icon"
          floating
          options={[]}
          trigger={<></>}
        />
      </Button.Group>
    </Tab.Pane>
  );
}

const panes = [
  {
    menuItem: { key: 'search-index', icon: 'redo', content: t`Search Index` },
    render: () => <SearchIndexPane />,
  },
  {
    menuItem: t`Backup/Restore Database`,
    render: () => <Tab.Pane>Use GUI for now</Tab.Pane>,
  },
  {
    menuItem: t`Refresh Database`,
    render: () => <Tab.Pane>Refresh database command</Tab.Pane>,
  },
];

export default function Page({}: PageProps) {
  return (
    <ManagementPage>
      <PageTitle title={t`Database`} />
      <Container centered clearing as={Segment} basic>
        <Tab
          menu={{ stackable: true, className: 'tabs item three' }}
          panes={panes}
          className="tabs"
        />
      </Container>
    </ManagementPage>
  );
}
