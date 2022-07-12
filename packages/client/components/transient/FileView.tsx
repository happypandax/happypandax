import React, { useCallback, useEffect, useState } from 'react';
import { useUpdateEffect } from 'react-use';
import { useRecoilState } from 'recoil';
import {
  Accordion,
  Button,
  Divider,
  Header,
  Icon,
  Label,
  Segment,
  SemanticCOLORS,
} from 'semantic-ui-react';

import {
  QueryType,
  ServiceReturnType,
  useQueryType,
} from '../../client/queries';
import { CommandState } from '../../misc/enums';
import t from '../../misc/lang';
import { FileViewItem } from '../../misc/types';
import { dateFromTimestamp, humanFileSize } from '../../misc/utility';
import type ServerService from '../../services/server';
import { ImportState } from '../../state';
import { LabelAccordion } from '../misc';
import { Progress } from '../misc/Progress';

function typeProp(data: FileViewItem) {
  let color: SemanticCOLORS = undefined;
  let type = data.type;

  switch (data.type) {
    case 'Gallery': {
      type = t`Gallery`;
      break;
    }
    case 'Collection': {
      color = 'violet';
      type = t`Collection`;
      break;
    }
    case 'Artist': {
      type = t`Artist`;
      color = 'blue';
      break;
    }
    case 'Grouping': {
      type = t`Series`;
      color = 'teal';
      break;
    }
  }

  return {
    color,
    type,
  };
}

function FileItemTitle({ data }: { data: FileViewItem }) {
  return (
    <>
      <Icon name={data.is_directory ? 'folder' : 'file'} />
      {data.name}
      {data.children.map((child) => {
        let n = child.name;
        if (n.length > 25) {
          n = n.slice(0, 25) + '...';
        }

        const { color, type } = typeProp(child);

        return (
          <Label color={color} size="mini" key={data.id}>
            {type}
            <Label.Detail>{n}</Label.Detail>
          </Label>
        );
      })}
    </>
  );
}

function FileItemContent({ data }: { data: FileViewItem }) {
  const { type } = typeProp(data);

  return (
    <Segment basic className="no-top-padding">
      <Label>
        {t`Path`}:<Label.Detail>{data.path}</Label.Detail>
      </Label>
      <Header size="tiny" dividing>
        {t`Attached items`}
      </Header>

      {data.children.map((child) => {
        const { color, type } = typeProp(child);

        return (
          <>
            <Label basic color={color} key={data.id}>
              {type}
              <Label.Detail>{child.path}</Label.Detail>
            </Label>
            <br />
          </>
        );
      })}

      <Divider hidden />
      <Label attached="bottom">
        {t`Size`}: <span className="muted">{humanFileSize(data.size)}</span> |{' '}
        {t`Created`}:{' '}
        <span className="muted">
          {dateFromTimestamp(data.date_created, { relative: false })}
        </span>{' '}
        | {t`Modified`}:{' '}
        <span className="muted">
          {dateFromTimestamp(data.date_modified, { relative: false })}
        </span>{' '}
        | {type}
      </Label>
    </Segment>
  );
}

export function TransientFileView({
  label,
  data,
  defaultOpen,
  refetchToggle,
  onData,
  labelButtons,
}: React.ComponentProps<typeof Segment> & {
  label?: string;
  labelButtons?: React.ReactNode;
  refetchToggle?: any;
  defaultOpen?: boolean;
  onData?: (data: ServiceReturnType['transient_view']) => void;
  data: Unwrap<Unwrap<ReturnType<ServerService['transient_views']>>>;
}) {
  const [descView, setDescView] = useRecoilState(
    ImportState.descendingView(data?.id)
  );

  const [state, setState] = useState<CommandState>();

  const doneState = [
    CommandState.Failed,
    CommandState.Stopped,
    CommandState.Finished,
  ];

  const { data: viewData, refetch } = useQueryType(
    QueryType.TRANSIENT_VIEW,
    { view_id: data?.id, desc: descView },
    {
      enabled: !!data?.id,
      refetchInterval: doneState.includes(state) ? false : 1000,
    }
  );

  const prog = viewData ? (
    <Progress
      size="tiny"
      indeterminate={doneState.includes(state) ? undefined : 'filling'}
      percent={100}
      color="blue"
      error={state === CommandState.Failed}
      success={state == CommandState.Finished}>
      {viewData?.data?.progress?.text}
    </Progress>
  ) : null;

  useEffect(() => {
    if (refetchToggle !== undefined) {
      refetch();
    }
  }, [refetchToggle]);

  useEffect(() => {
    if (viewData?.data?.state !== state) {
      setState(viewData?.data?.state);
    }
  }, [viewData?.data?.state]);

  useUpdateEffect(() => {
    if (viewData?.data) {
      onData?.(viewData.data);
    }
  }, [onData, viewData?.data]);

  let root = viewData?.data?.roots?.[0] ?? data?.id;

  if (root.length > 70) {
    root = root.slice(0, 50) + '...';
  }

  return (
    <LabelAccordion
      basic={false}
      defaultShow={defaultOpen}
      progress
      basicLabel
      label={
        <>
          {label ?? t`Files`}
          <Button
            basic
            icon={{ name: 'trash', color: 'red' }}
            floated="right"
            size="mini"
            onClick={useCallback((e) => {
              e.preventDefault();
              e.stopPropagation();
            }, [])}
            title={t`Remove`}
            compact
          />
          <Button
            basic
            className="visibility-hidden"
            floated="right"
            size="mini"
            compact
          />
          <Button
            basic
            floated="right"
            size="mini"
            onClick={useCallback((e) => {
              e.preventDefault();
              e.stopPropagation();
            }, [])}
            compact>
            <Icon name="close" />
            {t`Clear`}
          </Button>
          <Button
            primary
            onClick={useCallback(
              (e) => {
                e.preventDefault();
                e.stopPropagation();
                setDescView(!descView);
              },
              [descView]
            )}
            icon={descView ? 'sort numeric up' : 'sort numeric down'}
            floated="right"
            size="mini"
            title={t`Sort ascending/descending`}
            compact
          />
          <Button
            basic
            className="visibility-hidden"
            floated="right"
            size="mini"
            compact
          />
          <Label.Detail>
            {viewData?.data?.count ?? data?.count}
            <Label size="tiny">
              {dateFromTimestamp(data?.timestamp, { relative: true })} |
              <Label.Detail>{root}</Label.Detail>
            </Label>
          </Label.Detail>
          {labelButtons}
        </>
      }>
      <Divider hidden section />
      {viewData?.data?.roots?.map((root) => (
        <>
          <Label size="small" key={root}>
            {t`Path`}: <Label.Detail>{root}</Label.Detail>
          </Label>
          <br />
        </>
      ))}
      {prog}
      <Accordion
        exclusive={false}
        fluid
        styled
        panels={viewData?.data?.items?.map?.((file) => ({
          key: file.id,
          title: {
            content: <FileItemTitle data={file} />,
          },
          content: {
            content: <FileItemContent data={file} />,
          },
        }))}
      />
      {(viewData?.data?.items?.length ?? 0) > 50 && prog}
    </LabelAccordion>
  );
}
