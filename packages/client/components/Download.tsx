import { useEffect, useMemo, useState } from 'react';
import { Divider, Form, Icon, Label, Menu, Segment } from 'semantic-ui-react';

import { QueryType, useQueryType } from '../client/queries';
import { QueueType } from '../misc/enums';
import t from '../misc/lang';

export function DownloadQueue() {
  return (
    <Segment basic>
      <Form>
        <Form.Input
          fluid
          placeholder="https://..."
          action={useMemo(() => ({ icon: 'plus', color: 'teal' }), [])}
        />
        <Divider />
      </Form>
      <Menu labeled compact text fluid>
        <Menu.Item>
          <Icon name="play" color="green" /> {t`Running`}
        </Menu.Item>
        <Menu.Item>
          <Icon name="remove" /> {t`Clear`}
        </Menu.Item>
      </Menu>
    </Segment>
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
