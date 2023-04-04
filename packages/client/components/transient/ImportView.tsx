import React, { useCallback, useEffect, useState } from 'react';
import { useMap } from 'react-use';
import { useRecoilState } from 'recoil';
import {
  Accordion,
  Button,
  Checkbox,
  Divider,
  Grid,
  Header,
  Icon,
  Label,
  Segment,
  SemanticCOLORS,
} from 'semantic-ui-react';

import t from '../../client/lang';
import {
  MutatationType,
  QueryType,
  useMutationType,
  useQueryType,
} from '../../client/queries';
import { dateFromTimestamp } from '../../client/utility';
import { CommandState, ItemType, TransientViewType } from '../../shared/enums';
import {
  FileViewItem,
  TransientView as TransientViewT,
  ViewID,
} from '../../shared/types';
import { humanFileSize } from '../../shared/utility';
import { ImportState } from '../../state';
import { itemText } from '../item';
import { itemColor } from '../item/index';
import { EmptySegment } from '../misc';
import LabelItem from '../misc/LabelItem';
import { TransientView } from './';

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
    <Grid className="no-top-padding">
      <Grid.Row>
        <Grid.Column>
          <Label>
            {t`Path`}:<Label.Detail>{data.path}</Label.Detail>
          </Label>
        </Grid.Column>
      </Grid.Row>
      <Grid.Row>
        <Grid.Column>
          <Label basic>
            {t`Size`}: <span className="muted">{humanFileSize(data.size)}</span>{' '}
            | {t`Created`}:{' '}
            <span className="muted">
              {dateFromTimestamp(data.date_created, { relative: false })}
            </span>{' '}
            | {t`Modified`}:{' '}
            <span className="muted">
              {dateFromTimestamp(data.date_modified, { relative: false })}
            </span>{' '}
            | {type}
          </Label>
        </Grid.Column>
      </Grid.Row>
      <Grid.Row>
        <Grid.Column>
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
        </Grid.Column>
      </Grid.Row>
    </Grid>
  );
}

export function TransientImportView({
  data,
  onData,
  ...props
}: React.ComponentProps<typeof TransientView>) {
  const [viewData, setViewData] =
    useState<TransientViewT<TransientViewType.Import>>(data);

  const [showItemType, { set: setShowItemType }] = useMap({
    [ItemType.Collection]: true,
    [ItemType.Grouping]: true,
    [ItemType.Gallery]: true,
  });

  const showTypeLabel = (
    type: ItemType.Grouping | ItemType.Gallery | ItemType.Collection,
    label: string
  ) => {
    return (
      <Label
        basic={!showItemType[type]}
        color={showItemType[type] ? 'teal' : 'grey'}
        as="a"
        onClick={(e) => {
          e.preventDefault();
          setShowItemType(type, !showItemType[type]);
        }}
      >
        {label}
      </Label>
    );
  };

  return (
    <TransientView
      limit={40}
      {...props}
      data={data}
      submitText={t`Import all`}
      onData={useCallback(
        (d) => {
          setViewData(d);
          onData?.(d);
        },
        [onData]
      )}
      headerLabel={
        <>
          {t`ID`}: <Label.Detail>{viewData?.id}</Label.Detail>
        </>
      }
      headerContent={
        <Grid>
          <Grid.Row centered>
            <Grid.Column width="4">
              <Checkbox toggle label={`Group items`} />
            </Grid.Column>
            <Grid.Column width="8" textAlign="center">
              {showTypeLabel(ItemType.Collection, t`Collection`)}
              {showTypeLabel(ItemType.Grouping, t`Series`)}
              {showTypeLabel(ItemType.Gallery, t`Gallery`)}
            </Grid.Column>
            <Grid.Column width="4" textAlign="right"></Grid.Column>
          </Grid.Row>
        </Grid>
      }
    >
      <Accordion
        exclusive={false}
        fluid
        styled
        panels={viewData?.items?.map?.((item) => ({
          key: item.id,
          title: {
            content: (
              <LabelItem size="big" fluid>
                <LabelItem.Image src="/img/default.png" />
                <LabelItem.Content>
                  <Grid stretched>
                    <Grid.Row textAlign="center">
                      <Grid.Column>{item.name}</Grid.Column>
                    </Grid.Row>
                    <Grid.Row>
                      <Grid.Column>
                        <span>
                          <Label basic color={itemColor(item.type)}>
                            {t`Type`}:
                            <Label.Detail>{itemText(item.type)}</Label.Detail>
                          </Label>
                          {[CommandState.Started].includes(data.state) && (
                            <Icon
                              loading
                              className="float-right"
                              name="circle notch"
                            />
                          )}
                          {![CommandState.Started].includes(data.state) && (
                            <Icon
                              className="float-right"
                              title={
                                item.processed ? t`Processed` : t`Unprocessed`
                              }
                              name={item.processed ? 'check' : 'question'}
                              color={item.processed ? 'green' : undefined}
                            />
                          )}
                          {item.error && (
                            <Icon
                              className="float-right"
                              name="exclamation triangle"
                              color="red"
                            />
                          )}
                        </span>
                      </Grid.Column>
                    </Grid.Row>
                  </Grid>
                </LabelItem.Content>
                <Label.Detail>
                  <Button
                    color="green"
                    size="mini"
                    icon="plus"
                    title={t`Import`}
                    compact
                  />
                </Label.Detail>
              </LabelItem>
            ),
          },
          content: {
            content: <>momo</>,
          },
        }))}
      />
    </TransientView>
  );
}

export function ImportViews({
  data: cData,
  onRemove: otherOnRemove,
  onCreate,
  labelButtons,
  submitAction,
  label,
  stateKey,
  submitValue,
  headerLabel,
  ...props
}: React.ComponentProps<typeof TransientImportView> &
  React.ComponentProps<typeof Segment> & {
    data?: TransientViewT<TransientViewType.Import>[];
    stateKey: string;
    onCreate?: (view_id: ViewID) => void;
  }) {
  const enabled = cData === undefined;

  const { data: uData, refetch } = useQueryType(
    QueryType.TRANSIENT_VIEWS,
    { view_type: TransientViewType.Import },
    { enabled }
  );

  const { mutate: createView } = useMutationType(
    MutatationType.CREATE_TRANSIENT_VIEW,
    {
      onSuccess: (r) => {
        onCreate?.(r.data);
        if (enabled) {
          refetch();
        }
      },
    }
  );

  const data = cData ?? uData?.data;

  const [active, setActive] = useRecoilState(
    ImportState.activeImportView(stateKey)
  );

  useEffect(() => {
    if (data.length === 1 && !active) {
      setActive(data[0].id);
    } else if (!data.length && active !== undefined) {
      setActive(undefined);
    } else if (
      active &&
      data.length &&
      data.findIndex((d) => d.id === active) === -1
    ) {
      setActive(undefined);
    }
  }, [data, active]);

  const view = (d: TransientViewT<TransientViewType.Import>) => (
    <TransientImportView
      defaultOpen={d.id === active}
      onRemove={(...args) => {
        if (enabled) {
          refetch();
        }
        otherOnRemove?.(...args);
      }}
      label={label ?? t`Items`}
      headerColor={d.id === active ? 'blue' : 'grey'}
      labelButtons={
        <>
          {d.id !== active && (
            <Button
              onClick={(e) => {
                e.preventDefault();
                e.stopPropagation();
                setActive(d.id);
              }}
              size="mini"
              floated="right"
              compact
            >{t`Make active`}</Button>
          )}
          {labelButtons}
        </>
      }
      {...props}
      key={d.id}
      data={d}
      submitAction={submitAction}
      submitValue={submitValue}
    />
  );

  return (
    <Segment {...props}>
      <Button
        primary
        size="tiny"
        onClick={useCallback((e) => {
          e.preventDefault();
          createView({
            type: TransientViewType.Import,
          });
        }, [])}
      >
        {t`Create new import view`}
      </Button>
      <Divider horizontal>{t`Active import view`}</Divider>
      {!data?.length && <EmptySegment />}
      {data?.filter?.((d) => d.id === active).map?.(view)}
      <Divider horizontal>{t`Others`}</Divider>
      {data?.filter?.((d) => d.id !== active).map?.(view)}
    </Segment>
  );
}
