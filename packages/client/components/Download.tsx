import { useMemo } from 'react';
import { Divider, Form, Icon, Menu, Segment } from 'semantic-ui-react';

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
