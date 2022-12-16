import React, { useCallback, useEffect, useState } from 'react';
import { useUpdateEffect } from 'react-use';
import { useRecoilState } from 'recoil';
import {
  Button,
  Divider,
  Grid,
  Icon,
  Label,
  Loader,
  Pagination,
  Segment,
  SemanticCOLORS,
} from 'semantic-ui-react';

import { useCommand } from '../../client/command';
import t from '../../client/lang';
import {
  MutatationType,
  QueryType,
  ServiceReturnType,
  useMutationType,
  useQueryType,
} from '../../client/queries';
import { dateFromTimestamp } from '../../client/utility';
import { CommandState, TransientViewAction } from '../../shared/enums';
import { CommandID, FileViewItem } from '../../shared/types';
import { ImportState } from '../../state';
import { EmptyMessage, LabelAccordion } from '../misc';
import { Progress } from '../misc/Progress';

import type ServerService from '../../services/server';
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

export function TransientView({
  label,
  data,
  defaultOpen,
  refetchToggle,
  children,
  headerContent,
  submitText,
  submitColor,
  onRemove,
  headerColor,
  onData,
  labelButtons,
  headerLabel,
  countLabel,
}: React.ComponentProps<typeof Segment> & {
  label?: string;
  submitText?: string;
  submitColor?: SemanticCOLORS;
  headerLabel?: React.ReactNode;
  countLabel?: React.ReactNode;
  labelButtons?: React.ReactNode;
  headerContent?: React.ReactNode;
  headerColor?: SemanticCOLORS;
  refetchToggle?: any;
  defaultOpen?: boolean;
  onRemove?: (id: string) => void;
  onData?: (data: ServiceReturnType['transient_view']) => void;
  data: Unwrap<Unwrap<ReturnType<ServerService['transient_views']>>>;
}) {
  const limit = 100;

  const [descView, setDescView] = useRecoilState(
    ImportState.descendingView(data?.id)
  );

  const [page, setPage] = useState(1);

  const [state, setState] = useState<CommandState>();
  const [clearLoading, setClearLoading] = useState(false);
  const [clearCmdId, setClearCmdId] = useState<CommandID<boolean>>();

  const [removeLoading, setRemoveLoading] = useState(false);
  const [removeCmdId, setRemoveCmdId] = useState<CommandID<boolean>>();

  const [submitLoading, setSubmitLoading] = useState(false);
  const [submitCmdId, setSubmitCmdId] = useState<CommandID<boolean>>();

  const doneState = [
    CommandState.Failed,
    CommandState.Stopped,
    CommandState.Finished,
  ];

  const { data: viewData, refetch, isLoading } = useQueryType(
    QueryType.TRANSIENT_VIEW,
    { view_id: data?.id, desc: descView, limit, offset: (page - 1) * limit },
    {
      enabled: !!data?.id,
      refetchInterval:
        doneState.includes(state) || submitLoading ? false : 1000,
    }
  );

  const { mutateAsync: viewApply } = useMutationType(
    MutatationType.TRANSIENT_VIEW_ACTION
  );

  useCommand(
    clearCmdId,
    undefined,
    () => {
      setClearLoading(false);
      setClearCmdId(undefined);
      refetch();
    },
    []
  );

  useCommand(
    removeCmdId,
    undefined,
    () => {
      setRemoveLoading(false);
      setRemoveCmdId(undefined);
      onRemove?.(data.id);
    },
    [onRemove, data]
  );

  useCommand(
    submitCmdId,
    undefined,
    () => {
      setSubmitLoading(false);
      setSubmitCmdId(undefined);
      refetch();
    },
    [onRemove, data]
  );

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

  const pagRow = () => {
    return (
      <Grid.Row textAlign="center">
        <Grid.Column>
          <Pagination
            size="tiny"
            activePage={page}
            onPageChange={(e, { activePage }) => {
              e.preventDefault();
              setPage(parseInt(activePage as string));
            }}
            totalPages={Math.floor(viewData?.data?.count / limit)}
          />
        </Grid.Column>
      </Grid.Row>
    );
  };

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

  return (
    <LabelAccordion
      basic={false}
      defaultShow={defaultOpen}
      progress
      color={headerColor}
      segmentColor={headerColor}
      basicLabel
      label={
        <>
          {label ?? data?.id}
          <Label size="small">
            {countLabel ?? viewData?.data?.count ?? data?.count}
            <Label.Detail>
              {dateFromTimestamp(data?.timestamp, { relative: true }) ||
                t`Unknown`}
            </Label.Detail>
          </Label>
          <Label size="small">{headerLabel}</Label>
          <Button
            basic
            icon={{ name: 'trash', color: 'red' }}
            floated="right"
            size="mini"
            loading={removeLoading}
            disabled={removeLoading}
            onClick={useCallback(
              (e) => {
                e.preventDefault();
                e.stopPropagation();
                setRemoveLoading(true);
                viewApply({
                  view_id: viewData?.data?.id,
                  action: TransientViewAction.Remove,
                }).then((r) => {
                  setRemoveCmdId(r.data);
                });
              },
              [viewData?.data]
            )}
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
            loading={clearLoading}
            disabled={clearLoading}
            onClick={useCallback(
              (e) => {
                e.preventDefault();
                e.stopPropagation();
                setClearLoading(true);
                viewApply({
                  view_id: viewData?.data?.id,
                  action: TransientViewAction.Clear,
                }).then((r) => {
                  setClearCmdId(r.data);
                });
              },
              [viewData?.data]
            )}
            compact>
            <Icon name="close" />
            {t`Clear`}
          </Button>
          <Button
            primary
            basic
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
          <Button
            primary
            loading={submitLoading}
            disabled={submitLoading}
            onClick={useCallback((e) => {
              e.preventDefault();
              e.stopPropagation();
              setSubmitLoading(true);
              viewApply({
                view_id: viewData?.data?.id,
                action: TransientViewAction.Submit,
              }).then((r) => {
                setSubmitCmdId(r.data);
              });
            }, [])}
            floated="right"
            size="mini"
            color={submitColor}
            compact>
            {submitText ?? t`Submit`}
          </Button>
          <Button
            basic
            className="visibility-hidden"
            floated="right"
            size="mini"
            compact
          />

          {labelButtons}
        </>
      }>
      <Divider hidden section />
      {headerContent}
      {prog}
      <Grid>
        {(viewData?.data?.items?.length ?? 0) > 25 && pagRow()}
        <Grid.Row>
          <Grid.Column>
            <Loader active={isLoading} />
            {children}
            {!viewData?.data?.items?.length && (
              <EmptyMessage title={t`No items found`} />
            )}
          </Grid.Column>
        </Grid.Row>
        {(viewData?.data?.items?.length ?? 0) > 25 && pagRow()}
        <Grid.Row>
          <Grid.Column>
            {(viewData?.data?.items?.length ?? 0) > 25 && prog}
          </Grid.Column>
        </Grid.Row>
      </Grid>
    </LabelAccordion>
  );
}
