import { useCallback, useState } from 'react';
import { Table, Header, Button, Icon, Label } from 'semantic-ui-react';
import t from '../misc/lang';
import {
  DateAddedLabel,
  DatePublishedLabel,
  LanguageLabel,
  LastReadLabel,
  LastUpdatedLabel,
  PageCountLabel,
  ReadCountLabel,
  StatusLabel,
  TitleTable,
} from './data/Common';
import { TextEditor } from './Misc';

export function GalleryDataTable({}: {}) {
  const [showDataText, setShowDataText] = useState(false);

  return (
    <DataTable showDataText={showDataText}>
      <DataTableItem>
        <TitleTable>
          <Label
            as="a"
            onClick={useCallback(() => {
              setShowDataText(true);
            }, [])}
            className="float-right"
            size="tiny">
            <Icon name="pencil" /> {t`Edit`}
          </Label>
        </TitleTable>
      </DataTableItem>
      <DataTableItem textAlign="center">
        <LanguageLabel />
        <ReadCountLabel />
        <PageCountLabel />
        <StatusLabel />
      </DataTableItem>
      <DataTableItem name={t`Artist`}>test</DataTableItem>
      <DataTableItem name={t`Rating`}>test</DataTableItem>
      <DataTableItem name={t`Series`}>test</DataTableItem>
      <DataTableItem name={t`Circle`}>test</DataTableItem>
      <DataTableItem name={t`Category`}>test</DataTableItem>
      <DataTableItem name={t`Tags`}>test</DataTableItem>
      <DataTableItem name={t`External links`}>test</DataTableItem>
      <DataTableItem textAlign="center">
        <LastReadLabel />
        <DatePublishedLabel />
        <DateAddedLabel />
        <LastUpdatedLabel />
      </DataTableItem>
    </DataTable>
  );
}

export function DataTableItem({
  children,
  colSpan = true,
  verticalAlign,
  textAlign,
  name,
}: {
  children?: React.ReactNode;
  name?: string;
  verticalAlign?: React.ComponentProps<typeof Table.Cell>['verticalAlign'];
  textAlign?: React.ComponentProps<typeof Table.Cell>['textAlign'];
  colSpan?: boolean;
}) {
  return (
    <Table.Row>
      {!!name && (
        <Table.Cell collapsing>
          <Header size="tiny" className="sub-text">
            {name}
          </Header>
        </Table.Cell>
      )}
      <Table.Cell
        colSpan={colSpan && !name ? '2' : undefined}
        verticalAlign={verticalAlign}
        textAlign={textAlign}>
        {children}
      </Table.Cell>
    </Table.Row>
  );
}

export function DataTable({
  children,
  size,
  compact,
  showDataText,
}: {
  size?: React.ComponentProps<typeof Table>['size'];
  children?: React.ReactNode;
  showDataText?: boolean;
  compact?: boolean;
}) {
  return (
    <Table basic="very" size={size} coamp={compact ? 'very' : false}>
      {showDataText && <TextEditor />}
      <Table.Body>{children}</Table.Body>
    </Table>
  );
}
