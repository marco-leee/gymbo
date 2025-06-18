import { Select, Box, LoadingOverlay } from '@mantine/core';
import { useInfiniteQuery } from '@tanstack/react-query';
import { useInView } from 'react-intersection-observer';
import { useEffect, useState } from 'react';
import { useDebouncedValue } from '@mantine/hooks';

interface Option {
  value: string;
  label: string;
}

interface InfiniteScrollSelectProps {
  value: string | null;
  onChange: (value: string) => void;
  fetchData: (page: number, search: string) => Promise<{
    data: Option[];
    hasMore: boolean;
  }>;
  placeholder?: string;
  label?: string;
  description?: string;
  error?: string;
  required?: boolean;
  disabled?: boolean;
}

export function InfiniteScrollSelect({
  value,
  onChange,
  fetchData,
  placeholder = 'Select an option...',
  label,
  description,
  error,
  required,
  disabled,
}: InfiniteScrollSelectProps) {
  const [search, setSearch] = useState('');
  const [debouncedSearch] = useDebouncedValue(search, 300);
  const { ref, inView } = useInView();

  const {
    data,
    fetchNextPage,
    hasNextPage,
    isFetchingNextPage,
    isLoading,
  } = useInfiniteQuery({
    queryKey: ['infinite-select', debouncedSearch],
    queryFn: ({ pageParam = 1 }) => fetchData(pageParam, debouncedSearch),
    getNextPageParam: (lastPage, pages) => {
      if (!lastPage.hasMore) return undefined;
      return pages.length + 1;
    },
    initialPageParam: 1,
  });

  useEffect(() => {
    if (inView && hasNextPage && !isFetchingNextPage) {
      fetchNextPage();
    }
  }, [inView, hasNextPage, isFetchingNextPage, fetchNextPage]);

  const allOptions = data?.pages.flatMap((page) => page.data) ?? [];

  const handleChange = (value: string | null) => {
    if (value) {
      onChange(value);
      setSearch('');
    }
  }

  return (
    <Box pos="relative">
      <LoadingOverlay visible={isLoading} />
      <Select
        value={value}
        onChange={handleChange}
        data={allOptions}
        // searchable
        // searchValue={search}
        // onSearchChange={setSearch}
        placeholder={placeholder}
        label={label}
        description={description}
        error={error}
        required={required}
        disabled={disabled}
        rightSection={
          <Box ref={ref} h={20} />
        }
      />
    </Box>
  );
} 