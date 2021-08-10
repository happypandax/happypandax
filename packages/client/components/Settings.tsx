import classNames from 'classnames';
import { useMemo } from 'react';
import { Header, Icon, Modal, Segment, Tab } from 'semantic-ui-react';

import t from '../misc/lang';

function GeneralPane() {
  return <Segment basic></Segment>;
}

function NetworkPane() {
  return <Segment basic></Segment>;
}

function ServerPane() {
  return <Segment basic></Segment>;
}

function AdvancedPane() {
  return <Segment basic></Segment>;
}

export function SettingsTab() {
  return (
    <Tab
      menu={useMemo(
        () => ({
          pointing: true,
          secondary: true,
          stackable: true,
        }),
        []
      )}
      panes={useMemo(
        () => [
          {
            menuItem: {
              key: 'general',
              content: t`General`,
            },
            render: () => (
              <Tab.Pane basic className="no-padding-segment">
                <GeneralPane />
              </Tab.Pane>
            ),
          },
          {
            menuItem: {
              key: 'network',
              content: t`Network`,
            },
            render: () => (
              <Tab.Pane basic className="no-padding-segment">
                <NetworkPane />
              </Tab.Pane>
            ),
          },
          {
            menuItem: {
              key: 'server',
              content: t`Server`,
            },
            render: () => (
              <Tab.Pane basic className="no-padding-segment">
                <ServerPane />
              </Tab.Pane>
            ),
          },
          {
            menuItem: {
              key: 'advanced',
              content: t`Advanced`,
            },
            render: () => (
              <Tab.Pane basic className="no-padding-segment">
                <AdvancedPane />
              </Tab.Pane>
            ),
          },
        ],
        []
      )}
    />
  );
}

export default function SettingsModal({
  className,
  ...props
}: React.ComponentProps<typeof Modal>) {
  return (
    <Modal
      dimmer="inverted"
      closeIcon
      {...props}
      className={classNames('min-400-h', className)}>
      <Modal.Header>
        <Icon name="settings" />
        {t`Preferences`}
      </Modal.Header>
      <Modal.Content as={Segment} basic>
        <SettingsTab />
      </Modal.Content>
    </Modal>
  );
}
