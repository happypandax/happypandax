import classNames from 'classnames';
import { useMemo } from 'react';
import {
  Button,
  Grid,
  Header,
  Icon,
  Label,
  List,
  Modal,
  Progress,
  Segment,
  Tab,
  Table,
} from 'semantic-ui-react';

import { QueryType, useQueryType } from '../client/queries';
import { CommandState } from '../misc/enums';
import t from '../misc/lang';
import { CommandProgress } from '../misc/types';
import { dateFromTimestamp } from '../misc/utility';
import { EmptySegment } from './Misc';

function InfoPane() {
  return (
    <Grid as={Segment} basic>
      <Grid.Row textAlign="center">
        <Grid.Column>
          <Label basic>
            {t`Webclient`} <Label.Detail>1.1.1</Label.Detail>
          </Label>
          <Label basic>
            {t`Server`} <Label.Detail>1.1.1</Label.Detail>
          </Label>
          <Label basic>
            {t`Database`} <Label.Detail>1.1.1</Label.Detail>
          </Label>
          <Label basic>
            {t`Torrent`} <Label.Detail>1.1.1</Label.Detail>
          </Label>
        </Grid.Column>
      </Grid.Row>
      <Grid.Row>
        <Grid.Column>
          <Button
            as="a"
            href="https://www.patreon.com/twiddly"
            rel="noreferrer"
            target="_blank"
            size="small"
            color="orange">
            <Icon name="heart" />
            {t`Support on Patreon`}
          </Button>
          <Button
            as="a"
            href="https://ko-fi.com/twiddly"
            rel="noreferrer"
            target="_blank"
            size="small"
            color="blue">
            <Icon name="coffee" />
            {t`Buy me a Coffee`}
          </Button>

          <Button
            as="a"
            href="https://github.com/happypandax"
            rel="noreferrer"
            target="_blank"
            size="small"
            floated="right">
            <Icon name="github" />
            {t`View on Github`}
          </Button>
        </Grid.Column>
      </Grid.Row>
      <Grid.Row>
        <Grid.Column>
          <Table basic="very" size="small">
            <Table.Body>
              <Table.Row>
                <Table.Cell collapsing>
                  <Header as="h5">
                    <Icon name="github" />
                    {t`Developer`}
                  </Header>
                </Table.Cell>
                <Table.Cell>
                  <a
                    href="https://github.com/twiddli"
                    target="_blank"
                    rel="noreferrer">
                    Twiddly
                  </a>
                </Table.Cell>
              </Table.Row>
              <Table.Row>
                <Table.Cell collapsing>
                  <Header as="h5">
                    <Icon name="twitter" />
                    Twitter
                  </Header>
                </Table.Cell>
                <Table.Cell>
                  <a
                    href="https://twitter.com/twiddly_"
                    target="_blank"
                    rel="noreferrer">
                    @twiddly_
                  </a>
                </Table.Cell>
              </Table.Row>
            </Table.Body>
          </Table>
        </Grid.Column>
      </Grid.Row>
      <Grid.Row>
        <Grid.Column>
          <Button size="small">
            <Icon name="refresh" />
            {t`Check for updates`}
          </Button>
          <Button size="small">
            <Icon name="redo" />
            {t`Reindex library`}
          </Button>
          <Button size="small" floated="right">
            <Icon name="settings" />
            {t`Reset client settings`}
          </Button>
        </Grid.Column>
      </Grid.Row>
    </Grid>
  );
}

function ActivityPane() {
  const { data } = useQueryType(QueryType.COMMAND_PROGRESS);

  return (
    <Segment basic className="small-padding-segment max-400-h">
      {!data?.data?.length && <EmptySegment />}
      {!!data?.data?.length && (
        <List size="mini">
          {data.data.map((p: CommandProgress) => (
            <List.Item key={p.id}>
              <List.Content>
                <List.Header>
                  <span className="right">
                    <Label size="mini">
                      {t`ID`}:<Label.Detail>{p.id}</Label.Detail>
                    </Label>
                    <Label size="mini" basic color="black">
                      {t`Status`}:
                      <Label.Detail>
                        {p.state === CommandState.failed
                          ? t`Failed`
                          : p.state === CommandState.finished
                          ? t`Finished`
                          : p.state === CommandState.in_queue
                          ? t`In Queue`
                          : p.state === CommandState.in_service
                          ? t`In Service`
                          : p.state === CommandState.out_of_service
                          ? t`Out of Service`
                          : p.state === CommandState.started
                          ? t`Started`
                          : p.state === CommandState.stopped
                          ? t`Stopped`
                          : t`Unknown`}
                      </Label.Detail>
                    </Label>
                  </span>
                  {p.title}
                </List.Header>
                <Progress
                  precision={2}
                  active
                  indicating
                  size="small"
                  progress="percent"
                  percent={
                    p.max
                      ? undefined
                      : [
                          CommandState.finished,
                          CommandState.stopped,
                          CommandState.failed,
                        ].includes(p.state)
                      ? 100
                      : 99
                  }
                  total={p.max ? p.max : undefined}
                  value={p.max ? p.value : undefined}
                  success={
                    p.max ? undefined : p.state === CommandState.finished
                  }
                  autoSuccess={p.max ? true : false}>
                  {p.subtitle}
                </Progress>
                <List.Description className="sub-text">
                  <List divided horizontal size="mini">
                    <List.Item>
                      {dateFromTimestamp(p.timestamp, { relative: true })}
                    </List.Item>
                    <List.Item>
                      <List.Content>{p.text}</List.Content>
                    </List.Item>
                  </List>
                </List.Description>
              </List.Content>
            </List.Item>
          ))}
        </List>
      )}
    </Segment>
  );
}

function StatsPane() {
  return (
    <Segment basic>
      <EmptySegment />
    </Segment>
  );
}

export function AboutTab() {
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
            menuItem: { key: 'info', icon: 'info circle', content: t`Info` },
            render: () => (
              <Tab.Pane basic className="no-padding-segment">
                <InfoPane />
              </Tab.Pane>
            ),
          },
          {
            menuItem: {
              key: 'activity',
              icon: 'exchange',
              content: t`Activity`,
            },
            render: () => (
              <Tab.Pane basic className="no-padding-segment">
                <ActivityPane />
              </Tab.Pane>
            ),
          },
          {
            menuItem: {
              key: 'statistics',
              icon: 'bar chart',
              content: t`Statistics`,
            },
            render: () => (
              <Tab.Pane basic className="no-padding-segment">
                <StatsPane />
              </Tab.Pane>
            ),
          },
          {
            menuItem: {
              key: 'trash',
              icon: 'trash',
              content: t`Trash`,
            },
            render: () => (
              <Tab.Pane basic className="no-padding-segment">
                <StatsPane />
              </Tab.Pane>
            ),
          },
        ],
        []
      )}
    />
  );
}

export default function AboutModal({
  className,
  ...props
}: React.ComponentProps<typeof Modal>) {
  return (
    <Modal
      dimmer="inverted"
      closeIcon
      {...props}
      className={classNames('min-300-h', className)}>
      <Modal.Content as={Segment} basic>
        <Header icon textAlign="center">
          <Icon className="hpx-standard" circular />
          {t`About`}
        </Header>
        <AboutTab />
      </Modal.Content>
      <Segment
        attached="bottom"
        textAlign="center"
        secondary
        className="no-margins">
        {t`HappyPanda X is a cross platform manga/doujinshi manager made out of pure`}
        <Icon name="heart" color="red" size="large" />
        {t`by`}{' '}
        <a href="https://twitter.com/twiddly_" target="_blank" rel="noreferrer">
          Twiddly
        </a>
      </Segment>
    </Modal>
  );
}
