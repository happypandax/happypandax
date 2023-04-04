import { AnyJson } from 'happypandax-client';
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
  useMutationType,
  useQueryType,
} from '../../client/queries';
import { dateFromTimestamp } from '../../client/utility';
import {
  CommandState,
  TransientViewAction,
  TransientViewSubmitAction,
} from '../../shared/enums';
import {
  CommandID,
  FileViewItem,
  TransientView as TransientViewT,
  ViewID,
} from '../../shared/types';
import { ImportState } from '../../state';
import { EmptyMessage, LabelAccordion } from '../misc';
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

export function TransientView({
  label,
  data,
  defaultOpen,
  submitAction,
  submitValue,
  limit = 100,
  children,
  headerContent,
  submitText,
  submitColor = 'green',
  onRemove,
  headerColor,
  onData,
  onSubmit,
  onProcess,
  labelButtons,
  headerLabel,
  countLabel,
  actions,
}: React.ComponentProps<typeof Segment> & {
  submitAction: TransientViewSubmitAction;
  submitValue: AnyJson;
  label?: string;
  limit?: number;
  submitText?: string;
  submitColor?: SemanticCOLORS;
  headerLabel?: React.ReactNode;
  countLabel?: React.ReactNode;
  labelButtons?: React.ReactNode;
  headerContent?: React.ReactNode;
  headerColor?: SemanticCOLORS;
  defaultOpen?: boolean;
  actions?: React.MutableRefObject<{ refetch: () => void }>;
  onSubmit?: (id: ViewID) => void;
  onProcess?: (id: ViewID) => void;
  onRemove?: (id: ViewID) => void;
  onData?: (data: TransientViewT<any>) => void;
  data: TransientViewT<any>;
}) {
  const [descView, setDescView] = useRecoilState(
    ImportState.descendingView(data?.id)
  );

  const [page, setPage] = useState(1);

  const [showing, setShowing] = useState(defaultOpen ?? false);

  const [state, setState] = useState<CommandState>();
  const [clearLoading, setClearLoading] = useState(false);
  const [clearCmdId, setClearCmdId] = useState<CommandID<boolean>>();

  const [removeLoading, setRemoveLoading] = useState(false);
  const [removeCmdId, setRemoveCmdId] = useState<CommandID<boolean>>();

  const [submitLoading, setSubmitLoading] = useState(false);
  const [submitCmdId, setSubmitCmdId] = useState<CommandID<boolean>>();
  const [processCmdId, setProcessCmdId] = useState<CommandID<boolean>>();

  const doneState = [
    0,
    CommandState.Failed,
    CommandState.Stopped,
    CommandState.Finished,
  ];

  const {
    data: viewData,
    refetch,
    isLoading,
  } = useQueryType(
    QueryType.TRANSIENT_VIEW,
    { view_id: data?.id, desc: descView, limit, offset: (page - 1) * limit },
    {
      enabled: !!data?.id,
      refetchInterval:
        doneState.includes(state) || submitLoading
          ? false
          : showing
          ? 1000
          : 5000,
    }
  );

  const { mutateAsync: viewAction } = useMutationType(
    MutatationType.TRANSIENT_VIEW_ACTION,
    {
      onSettled: () => {
        refetch();
      },
    }
  );

  const { mutate: viewSubmitAction } = useMutationType(
    MutatationType.TRANSIENT_VIEW_SUBMIT_ACTION,
    {
      onSuccess: (r) => {
        setSubmitCmdId(r.data);
      },
    }
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
      onSubmit?.(data.id);
      refetch();
    },
    [onSubmit, data]
  );

  useCommand(
    processCmdId,
    undefined,
    () => {
      setSubmitLoading(false);
      setProcessCmdId(undefined);
      onProcess?.(data.id);
      refetch();
    },
    [onProcess, data]
  );

  useEffect(() => {
    if (actions) {
      actions.current = {
        refetch,
      };
    }
  }, [actions]);

  useUpdateEffect(() => {
    refetch();
  }, [data?.state]);

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

  const statusLabel = {
    text: '',
    color: 'grey' as SemanticCOLORS,
    basic: true,
  };

  if (viewData?.data?.processed) {
    statusLabel.text = t`Processed`;
    statusLabel.color = 'green';
    statusLabel.basic = true;
  } else {
    statusLabel.text = t`Unprocessed`;
    statusLabel.color = 'grey';
    statusLabel.basic = false;
  }

  const pagRow = () => {
    return (
      <Grid.Row textAlign="center">
        <Grid.Column>
          <Pagination
            size="mini"
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

  const prog =
    viewData && state ? (
      <Progress
        size="tiny"
        indeterminate={doneState.includes(state) ? undefined : 'filling'}
        percent={viewData?.data?.progress?.percent}
        color="blue"
        error={state === CommandState.Failed}
        warning={state === CommandState.Stopped}
        success={state == CommandState.Finished}
      >
        {viewData?.data?.progress?.text}
      </Progress>
    ) : null;

  const onSubmitClick = useCallback(
    (e) => {
      e.preventDefault();
      e.stopPropagation();
      setSubmitLoading(true);
      viewSubmitAction({
        view_id: viewData?.data?.id,
        action: submitAction,
        value: submitValue,
      });
    },
    [viewData, submitAction]
  );

  const onProcessClick = useCallback(
    (e) => {
      e.preventDefault();
      e.stopPropagation();
      setSubmitLoading(true);
      viewAction({
        view_id: viewData?.data?.id,
        action: TransientViewAction.Process,
      }).then((r) => {
        setSubmitCmdId(r.data);
      });
    },
    [viewData]
  );

  const submitButton = (props: React.ComponentProps<typeof Button>) => {
    let text = submitText ?? t`Submit`;
    let color = submitColor;
    if (!viewData?.data?.processed) {
      text = t`Process`;
      color = 'blue';
    }

    let disabled = false;

    if (viewData?.data?.processed) {
      if (submitValue === undefined) {
        disabled = true;
      }
    }

    return (
      <Button
        primary
        loading={submitLoading}
        disabled={
          disabled ||
          submitLoading ||
          viewData?.data?.deleted ||
          ![
            CommandState.Finished,
            CommandState.Failed,
            CommandState.Stopped,
          ].includes(state)
        }
        onClick={viewData?.data?.processed ? onSubmitClick : onProcessClick}
        color={color}
        {...props}
      >
        {text}
      </Button>
    );
  };

  return (
    <LabelAccordion
      basic={false}
      visible={viewData?.data?.deleted ? false : undefined}
      defaultVisible={defaultOpen}
      onVisible={setShowing}
      progress
      color={headerColor}
      segmentColor={headerColor}
      basicLabel
      label={
        <>
          {viewData?.data?.deleted && (
            <Label size="small" color="red">{t`Deleted`}</Label>
          )}

          {label}
          <Label size="tiny" circular>
            {countLabel ?? viewData?.data?.count ?? data?.count}
          </Label>
          <Label size="tiny">
            {dateFromTimestamp(data?.timestamp, { relative: true }) ||
              t`Unknown`}
          </Label>
          {!!statusLabel.text && !viewData?.data?.deleted && (
            <Label
              size="tiny"
              basic={statusLabel.basic}
              color={statusLabel.color}
            >
              {statusLabel.text}
            </Label>
          )}
          {headerLabel && (
            <Label size="small" className="text-ellipsis max-250-w">
              {headerLabel}
            </Label>
          )}

          {submitButton({ size: 'mini', compact: true, floated: 'right' })}
          <Button
            basic
            className="visibility-hidden"
            floated="right"
            size="mini"
            compact
          />

          {labelButtons}
        </>
      }
    >
      <Divider hidden section />
      <Segment
        disabled={viewData?.data?.deleted}
        basic
        className="no-padding-segment"
      >
        <Grid>
          <Grid.Row className="small-padding-segment">
            <Grid.Column>
              <Label size="tiny">
                {t`ID`}: <Label.Detail>{data?.id}</Label.Detail>
              </Label>
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
                    viewAction({
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
                disabled={clearLoading || viewData?.data?.deleted}
                onClick={useCallback(
                  (e) => {
                    e.preventDefault();
                    e.stopPropagation();
                    setClearLoading(true);
                    viewAction({
                      view_id: viewData?.data?.id,
                      action: TransientViewAction.Clear,
                    }).then((r) => {
                      setClearCmdId(r.data);
                    });
                  },
                  [viewData?.data]
                )}
                compact
              >
                <Icon name="close" />
                {t`Clear all`}
              </Button>

              <Button
                basic
                className="visibility-hidden"
                floated="right"
                size="mini"
                compact
              />
              <Button
                primary
                disabled={viewData?.data?.deleted}
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
            </Grid.Column>
          </Grid.Row>
        </Grid>

        {headerContent}
        {prog}
        <Grid>
          {(viewData?.data?.items?.length ?? 0) > 25 && pagRow()}
          <Grid.Row>
            <Grid.Column>
              <Loader active={isLoading} />
              {children}
              {!viewData?.data?.items?.length && (
                <EmptyMessage title={t`No items`} />
              )}
            </Grid.Column>
          </Grid.Row>
          {(viewData?.data?.items?.length ?? 0) > 25 && (
            <Grid.Row textAlign="center">
              <Grid.Column>{submitButton({})}</Grid.Column>
            </Grid.Row>
          )}
          {(viewData?.data?.items?.length ?? 0) > 25 && pagRow()}
          <Grid.Row>
            <Grid.Column>
              {(viewData?.data?.items?.length ?? 0) > 25 && prog}
            </Grid.Column>
          </Grid.Row>
        </Grid>
      </Segment>
    </LabelAccordion>
  );
}
