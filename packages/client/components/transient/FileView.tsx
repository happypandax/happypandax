import React, { useCallback, useState } from 'react';
import {
  Accordion,
  Grid,
  Header,
  Icon,
  Label,
  Message,
  SemanticCOLORS,
} from 'semantic-ui-react';

import { useCommand } from '../../client/command';
import t from '../../client/lang';
import { MutatationType, useMutationType } from '../../client/queries';
import { dateFromTimestamp } from '../../client/utility';
import { TransientViewAction, TransientViewType } from '../../shared/enums';
import {
  CommandID,
  FileViewItem,
  TransientView as TransientViewT,
  ViewID,
} from '../../shared/types';
import { humanFileSize } from '../../shared/utility';
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
    case 'Parody': {
      type = t`Parody`;
      color = 'violet';
      break;
    }
    case 'Artist': {
      type = t`Artist`;
      color = 'blue';
      break;
    }
    case 'Language': {
      type = t`Language`;
      color = 'blue';
      break;
    }
    case 'Circle': {
      type = t`Circle`;
      color = 'teal';
      break;
    }
    case 'Grouping': {
      type = t`Series`;
      color = 'teal';
      break;
    }
    case 'Category': {
      type = t`Category`;
      color = 'black';
      break;
    }
  }

  return {
    color,
    type,
  };
}


function FileItemTitle({ data, viewId, onDeleteItem }: { data: FileViewItem, viewId: ViewID, onDeleteItem?: (id: string, command: CommandID<any>) => void }) {
  const [deleted, setDeleted] = useState(false);

  const { mutate, data: deleteData } = useMutationType(
    MutatationType.TRANSIENT_VIEW_ACTION,
    {
      onSuccess: (r) => {
        setDeleted(true);

      },
    }
  );

  useCommand(deleteData?.data, undefined, () => {
    onDeleteItem?.(data.id, deleteData?.data)
  }, [deleteData?.data])

  return (
    <span>
      <Icon name={data.is_directory ? 'folder' : 'file'} />
      {(data.processed || !!data.error) && <Icon name={data.error ? "close" : "check"} color={data.error ? "red" : "green"} />}
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
      <Icon loading={deleted} onClick={(e) => {
        e.preventDefault();
        e.stopPropagation();
        mutate({
          view_id: viewId,
          action: TransientViewAction.Discard,
          value: data.id,
        })
      }} name='close' className='float-right' />
    </span>
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
      {data.error &&
        <Grid.Row>
          <Grid.Column>
            <Message error size="tiny">
              Some error here
            </Message>
          </Grid.Column>
        </Grid.Row>
      }
      <Grid.Row>
        <Grid.Column>
          <Label color={data.processed ? 'green' : 'grey'} basic={data.processed}>
            {data.processed ? t`Processed` : t`Unprocessed`}
          </Label>
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

export function TransientFileView({
  data,
  onData,
  onDeleteItem,
  ...props
}: React.ComponentProps<typeof TransientView> & {
  onDeleteItem?: (id: string, commmand: CommandID<any>) => void;
}) {
  const [viewData, setViewData] = useState<
    TransientViewT<TransientViewType.File>
  >(data);

  let root = viewData?.roots?.[0] ?? data?.id;

  if (root.length > 70) {
    root = root.slice(0, 50) + '...';
  }

  return (
    <TransientView
      {...props}
      data={data}
      onData={useCallback(
        (d) => {
          setViewData(d);
          onData?.(d);
        },
        [onData]
      )}
      headerLabel={root}
      headerContent={
        <Grid>
          <Grid.Row>
            {viewData?.roots?.map((root) => (
              <Grid.Column key={root} width="16">
                <Label basic color="black" size="small">
                  {t`Path`}: <Label.Detail>{root}</Label.Detail>
                </Label>
              </Grid.Column>
            ))}
          </Grid.Row>
          <Grid.Row>
            {(viewData?.properties?.patterns as string[])?.map((p) => (
              <Grid.Column key={p} width="16">
                <Label size="small" basic>
                  {t`Pattern`}: <Label.Detail>{p}</Label.Detail>
                </Label>
              </Grid.Column>
            ))}
          </Grid.Row>
        </Grid>
      }>
      <Accordion
        exclusive={false}
        fluid
        styled
        panels={viewData?.items?.map?.((file) => ({
          key: file.id,
          title: {
            content: <FileItemTitle viewId={data?.id} data={file} onDeleteItem={onDeleteItem} />,
          },
          content: {
            content: <FileItemContent data={file} />,
          },
        }))}
      />
    </TransientView>
  );
}
