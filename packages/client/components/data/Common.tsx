import React, { useCallback, useContext, useState } from 'react';
import { useRecoilState } from 'recoil';
import { Header, Icon, Label, Table } from 'semantic-ui-react';

import t from '../../misc/lang';
import { FieldPath, ServerGallery } from '../../misc/types';
import { dateFromTimestamp } from '../../misc/utility';
import { DataState } from '../../state';

export const DataContext = React.createContext({
  key: '',
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
    <Label title={t`Group number`} color="blue" basic {...props}>
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
