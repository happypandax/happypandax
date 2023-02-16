import React, { useCallback, useState } from 'react';
import { useRecoilState } from 'recoil';
import {
  Button,
  Divider,
  Grid,
  Header,
  Icon,
  Label,
  Segment,
  SemanticCOLORS,
} from 'semantic-ui-react';

import t from '../../client/lang';
import { QueryType, useQueryType } from '../../client/queries';
import { dateFromTimestamp } from '../../client/utility';
import { TransientViewType } from '../../shared/enums';
import {
  FileViewItem,
  TransientView as TransientViewT,
} from '../../shared/types';
import { humanFileSize } from '../../shared/utility';
import { ImportState } from '../../state';
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
  const [viewData, setViewData] = useState<
    TransientViewT<TransientViewType.Import>
  >();

  return (
    <TransientView
      {...props}
      data={data}
      submitText={t`Add all`}
      onData={useCallback(
        (d) => {
          setViewData(d);
          onData?.(d);
        },
        [onData]
      )}
      headerLabel={viewData?.id}
      headerContent={<></>}>
      <Segment.Group>
        <Segment clearing>
          test{' '}
          <Button
            color="green"
            size="mini"
            compact
            floated="right">{t`Add`}</Button>{' '}
        </Segment>
      </Segment.Group>
    </TransientView>
  );
}


export function ImportViews(
  { data: cData, onRemove: otherOnRemove, labelButtons, submitAction, label, stateKey, submitValue, headerLabel, ...props }: 
  { data?: TransientViewT<TransientViewType.Import>[], stateKey: string } 
  & React.ComponentProps<typeof TransientImportView>
  & React.ComponentProps<typeof Segment>) {

  const enabled = cData === undefined

  const { data: uData, refetch } = useQueryType(
    QueryType.TRANSIENT_VIEWS,
    { view_type: TransientViewType.Import },
    { enabled }
  );

  const data = cData ?? uData?.data;

  const [active, setActive] = useRecoilState(ImportState.activeImportView(stateKey))

  const view = (d: TransientViewT<TransientViewType.Import>) => (
    <TransientImportView onRemove={(...args) => {
      if (enabled) {
        refetch();
      }
      otherOnRemove?.(...args);
  }} 
  label={label ?? t`Items`}
  headerColor={d.id === active ? "blue" : "grey"}
  labelButtons={
    <>
    {d.id !== active && <Button onClick={(e) => {
      e.preventDefault();
      e.stopPropagation();
      setActive(d.id)
    }} size="mini" floated='right' compact>{t`Make active`}</Button>}
    {labelButtons}
    </>
  }
  {...props} 
  key={d.id} data={d} submitAction={submitAction} submitValue={submitValue}  />
  )


  return <Segment {...props}>
    <Divider horizontal>{t`Active import view`}</Divider>
    {data?.filter?.(d => d.id === active).map?.(view)}
    <Divider horizontal>{t`Others`}</Divider>
    {data?.filter?.(d => d.id !== active).map?.(view)}
  </Segment>
}