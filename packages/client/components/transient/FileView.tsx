import React, { useCallback, useState } from 'react';
import {
  Accordion,
  Grid,
  Header,
  Icon,
  Label,
  SemanticCOLORS,
} from 'semantic-ui-react';

import { ServiceReturnType } from '../../client/queries';
import t from '../../misc/lang';
import { FileViewItem } from '../../misc/types';
import { dateFromTimestamp, humanFileSize } from '../../misc/utility';
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

export function TransientFileView({
  data,
  onData,
  ...props
}: React.ComponentProps<typeof TransientView>) {
  const [viewData, setViewData] = useState<
    ServiceReturnType['transient_view']
  >();

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
            <Grid.Column>
              <Label size="tiny">
                {t`ID`}: <Label.Detail>{viewData?.id}</Label.Detail>
              </Label>
            </Grid.Column>
          </Grid.Row>
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
            content: <FileItemTitle data={file} />,
          },
          content: {
            content: <FileItemContent data={file} />,
          },
        }))}
      />
    </TransientView>
  );
}