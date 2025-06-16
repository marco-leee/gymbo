import { Table } from "@mantine/core";

type DataTableProps<T> = {
  headers: string[];
  data: T[];
  getValue: (item: T, header: string) => React.ReactNode;
}

export const DataTable = <T,>({ headers, data, getValue }: DataTableProps<T>) => {
  return (
    <Table striped highlightOnHover withTableBorder stickyHeader withRowBorders={false}>
      <Table.Thead>
        <Table.Tr>
          {headers.map((header) => (
            <Table.Th key={header}>{header}</Table.Th>
          ))}
        </Table.Tr>
      </Table.Thead>
      <Table.Tbody>
        {data && data.map((item, rowIndex) => (
          <Table.Tr key={rowIndex}>
            {headers.map((header) => (
              <Table.Td key={`${rowIndex}-${header}`}>
                {getValue(item, header)}
              </Table.Td>
            ))}
          </Table.Tr>
        ))}
      </Table.Tbody>
    </Table>
  )
}