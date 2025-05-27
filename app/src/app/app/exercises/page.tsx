'use client';

import { Table, Box, Grid } from '@mantine/core';
import { useExerciseStore } from '@/store/exercises';

export default function Exercises() {
  const exercises = useExerciseStore((state) => state.exercises);

  const rows = exercises.map((element, index) => (
    <Table.Tr key={index.toString()}>
      <Table.Td>{element.position}</Table.Td>
      <Table.Td>{element.name}</Table.Td>
      <Table.Td>{element.symbol}</Table.Td>
      <Table.Td>{element.mass}</Table.Td>
    </Table.Tr>
  ));

  return (
    <Table.ScrollContainer minWidth="100%">
      <Table striped highlightOnHover withTableBorder withRowBorders={false} stickyHeader>
        <Table.Thead>
          <Table.Tr>
            <Table.Th>Element position</Table.Th>
            <Table.Th>Element name</Table.Th>
            <Table.Th>Symbol</Table.Th>
            <Table.Th>Atomic mass</Table.Th>
          </Table.Tr>
        </Table.Thead>
        <Table.Tbody>{rows}</Table.Tbody>
        <Table.Caption>Scroll page to see sticky thead</Table.Caption>
      </Table>
    </Table.ScrollContainer>
  );
}