import { Header, Loader, Table } from 'semantic-ui-react';

import { TextEditor } from '../Misc';

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
  loading,
}: {
  size?: React.ComponentProps<typeof Table>['size'];
  children?: React.ReactNode;
  showDataText?: boolean;
  loading?: boolean;
  compact?: boolean;
}) {
  return (
    <Table basic="very" size={size} coamp={compact ? 'very' : false}>
      {showDataText && <TextEditor />}
      <Loader active={loading} />
      <Table.Body>{children}</Table.Body>
    </Table>
  );
}
