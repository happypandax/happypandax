import { Header, Loader, Table } from 'semantic-ui-react';

import { TextEditor } from '../misc/';

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
        textAlign={textAlign}
      >
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
  ...props
}: {
  size?: React.ComponentProps<typeof Table>['size'];
  children?: React.ReactNode;
  showDataText?: boolean;
  loading?: boolean;
  compact?: boolean;
} & React.ComponentProps<typeof Table>) {
  return (
    <Table
      basic="very"
      size={size}
      compact={compact ? 'very' : false}
      {...props}
    >
      {showDataText && <TextEditor />}
      <Loader active={loading} />
      <Table.Body>{children}</Table.Body>
    </Table>
  );
}
