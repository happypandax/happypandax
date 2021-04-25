import { Dimmer, Segment, Sidebar } from 'semantic-ui-react';
import { Column, Table, AutoSizer } from 'react-virtualized';
import { useState } from 'react';

export default function TableView() {
  const items = [
    { name: 'Brian Vaughn', description: 'Software engineer' },
    { name: 'Brian Vaughn', description: 'Software engineer' },
    { name: 'Brian Vaughn', description: 'Software engineer' },
  ];

  const [columns, setColumns] = useState(['name', 'description']);
  const [showHeader, setShowHeader] = useState(true);

  return (
    <AutoSizer>
      {({ height, width }) => (
        <Table
          className="ui table basic striped"
          headerClassName="thead"
          rowClassName="tr"
          disableHeader={!showHeader}
          width={width}
          height={height}
          headerHeight={20}
          rowHeight={30}
          rowCount={items.length}
          rowGetter={({ index }) => items[index]}>
          {columns.includes('name') && (
            <Column
              label="Name"
              dataKey="name"
              gridClassName="td"
              flexGrow={1}
              width={100}
            />
          )}
          {columns.includes('description') && (
            <Column
              label="Description"
              gridClassName="td"
              dataKey="description"
              flexGrow={2}
              width={100}
            />
          )}
        </Table>
      )}
    </AutoSizer>
  );
}
