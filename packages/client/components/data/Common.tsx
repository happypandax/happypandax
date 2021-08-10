import React, { useCallback, useContext, useState } from 'react';
import { useRecoilState } from 'recoil';
import { Header, Icon, Label, List, Table } from 'semantic-ui-react';

import { ItemType } from '../../misc/enums';
import t from '../../misc/lang';
import { FieldPath, ServerGallery, ServerTag } from '../../misc/types';
import { dateFromTimestamp } from '../../misc/utility';
import { DataState } from '../../state';

export const DataContext = React.createContext({
  key: '',
  type: ItemType.Gallery,
});

export function LanguageLabel({
  children,
  ...props
}: React.ComponentProps<typeof Label>) {
  return (
    <Label color="blue" basic {...props}>
      <Icon className="globe africa" />
      {children}
    </Label>
  );
}

export function ReadCountLabel({
  children,
  ...props
}: React.ComponentProps<typeof Label>) {
  return (
    <Label title={t`Timed read`} color="blue" basic {...props}>
      <Icon className="book open" />
      {children}
    </Label>
  );
}

export function PageCountLabel({
  children,
  ...props
}: React.ComponentProps<typeof Label>) {
  return (
    <Label title={t`Page count`} color="blue" basic {...props}>
      <Icon name="clone outline" />
      {children}
    </Label>
  );
}

export function CategoryLabel() {
  const ctx = useContext(DataContext);
  const [data, setData] = useRecoilState<PartialExcept<ServerGallery, 'id'>>(
    DataState.data(ctx.key)
  );

  return (
    <Label title={t`Category`} color="black" basic>
      <Icon name="folder outline" />
      {data?.category?.name}
    </Label>
  );
}

export function StatusLabel({
  children,
  ...props
}: React.ComponentProps<typeof Label>) {
  return (
    <Label title={t`Status`} color="blue" basic {...props}>
      <Icon name="calendar check" />
      {children}
    </Label>
  );
}

export function GroupingNumberLabel({
  children,
  ...props
}: React.ComponentProps<typeof Label>) {
  return (
    <Label title={t`Group number`} color="teal" basic {...props}>
      {children}
    </Label>
  );
}

export function DateLabel({
  timestamp,
  text,
  ...props
}: React.ComponentProps<typeof Label> & { text?: string; timestamp?: number }) {
  const [showRelative, setShowRelative] = useState(true);

  const date = dateFromTimestamp(timestamp, { relative: showRelative });

  return (
    <Label
      as="a"
      {...props}
      onClick={useCallback(() => setShowRelative(!showRelative), [
        showRelative,
      ])}>
      {text}
      <Label.Detail>{date ? date : t`Unknown`}</Label.Detail>
    </Label>
  );
}

export function DateAddedLabel({
  children,
  ...props
}: React.ComponentProps<typeof DateLabel>) {
  return <DateLabel {...props} text={t`Added`} title={t`Date added`} />;
}

export function LastReadLabel({
  children,
  ...props
}: React.ComponentProps<typeof DateLabel>) {
  return <DateLabel {...props} text={t`Last read`} title={t`Last read`} />;
}

export function LastUpdatedLabel({
  children,
  ...props
}: React.ComponentProps<typeof DateLabel>) {
  return <DateLabel {...props} text={t`Updated`} title={t`Last updated`} />;
}

export function DatePublishedLabel({
  children,
  ...props
}: React.ComponentProps<typeof DateLabel>) {
  return <DateLabel {...props} text={t`Published`} title={t`Date published`} />;
}

export function ArtistLabels() {
  const ctx = useContext(DataContext);
  const [data, setData] = useRecoilState<PartialExcept<ServerGallery, 'id'>>(
    DataState.data(ctx.key)
  );

  return (
    <Label.Group color="blue">
      {data?.artists?.map?.((a) => (
        <Label>
          <Icon name="user outline" /> {a?.preferred_name?.name}
        </Label>
      ))}
    </Label.Group>
  );
}

export function CircleLabels() {
  const ctx = useContext(DataContext);
  const [data, setData] = useRecoilState<PartialExcept<ServerGallery, 'id'>>(
    DataState.data(ctx.key)
  );

  return (
    <Label.Group>
      {data?.circles?.map?.((c) => (
        <Label color="teal">
          <Icon name="group" /> {c.name}
        </Label>
      ))}
      {data?.artists.flatMap?.((a) =>
        a?.circles?.map?.((c) => (
          <Label basic color="teal" className="border-dashed">
            <Icon name="group" /> {c.name}
          </Label>
        ))
      )}
    </Label.Group>
  );
}

export function GroupingLabel() {
  const ctx = useContext(DataContext);
  const [data, setData] = useRecoilState<PartialExcept<ServerGallery, 'id'>>(
    DataState.data(ctx.key)
  );

  return (
    <Label basic>
      <Icon className="stream" /> {data?.grouping?.name}
    </Label>
  );
}

export function NameTable({
  children,
  dataPrimaryKey,
  dataKey,
}: {
  dataKey: FieldPath;
  dataPrimaryKey: FieldPath;
  children?: React.ReactNode;
}) {
  const ctx = useContext(DataContext);
  const [data, setData] = useRecoilState<PartialExcept<ServerGallery, 'id'>>(
    DataState.data(ctx.key)
  );

  return (
    <Table basic="very" compact="very" verticalAlign="middle">
      <Table.Body>
        <Table.Row>
          <Table.Cell colspan="2" textAlign="center">
            {children}
            <Label size="tiny" className="float-right">
              {t`ID`}
              <Label.Detail>{data?.id}</Label.Detail>
            </Label>
            <div>
              <Header size="medium">{data?.[dataPrimaryKey]?.name}</Header>
            </div>
          </Table.Cell>
        </Table.Row>
        {data?.[dataPrimaryKey]?.map?.((v) => (
          <Table.Row key={v.id ?? v.title} verticalAlign="middle">
            <Table.Cell collapsing>
              <LanguageLabel color={undefined} basic={false} size="tiny">
                {v.language}
              </LanguageLabel>
            </Table.Cell>
            <Table.Cell>
              <Header size="tiny" className="sub-text">
                {v.title}
              </Header>
            </Table.Cell>
          </Table.Row>
        ))}
      </Table.Body>
    </Table>
  );
}

export function UrlList() {
  const ctx = useContext(DataContext);
  const [data, setData] = useRecoilState<PartialExcept<ServerGallery, 'id'>>(
    DataState.data(ctx.key)
  );

  return (
    <List>
      {data?.urls?.map?.((u) => (
        <List.Item as="a" target="_blank">
          {u.name}
        </List.Item>
      ))}
    </List>
  );
}

export function TagsTable() {
  const ctx = useContext(DataContext);
  const [data, setData] = useRecoilState<PartialExcept<ServerGallery, 'id'>>(
    DataState.data(ctx.key)
  );

  const freeTags: ServerTag[] = [];
  const tags = {} as Record<string, ServerTag[]>;

  data?.tags?.forEach?.((t) => {
    // TODO: query this value from server
    if (t?.namespace?.name === '__namespace__') {
      freeTags.push(t.tag);
    } else {
      const l = tags[t?.namespace?.name] ?? [];
      tags[t?.namespace?.name] = [...l, t.tag];
    }
  });

  return (
    <Table basic="very" compact="very" verticalAlign="middle" size="small">
      <Table.Body>
        {!!freeTags.length && (
          <Table.Row>
            <Table.Cell colspan="2">
              {freeTags
                .sort((a, b) => a?.name?.localeCompare?.(b?.name))
                .map((x) => (
                  <Label key={x?.id}>{x?.name}</Label>
                ))}
            </Table.Cell>
          </Table.Row>
        )}
        {Object.entries(tags)
          .sort((a, b) => a[0]?.localeCompare?.(b[0]))
          .map(([ns, t]) => (
            <Table.Row key={ns} verticalAlign="middle">
              <Table.Cell collapsing className="sub-text">
                {ns}
              </Table.Cell>
              <Table.Cell>
                <Label.Group>
                  {t
                    .sort((a, b) => a?.name?.localeCompare?.(b?.name))
                    .map((x) => (
                      <Label key={x?.id}>{x?.name}</Label>
                    ))}
                </Label.Group>
              </Table.Cell>
            </Table.Row>
          ))}
      </Table.Body>
    </Table>
  );
}
