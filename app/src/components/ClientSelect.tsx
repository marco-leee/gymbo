import { InfiniteScrollSelect } from "./InfiniteScrollSelect";

// Mock function to simulate API call - replace with your actual API call
async function fetchExercises(page: number, search: string) {
  // Simulate API delay
  await new Promise(resolve => setTimeout(resolve, 1000));

  // Mock data - replace with actual API call
  const mockData = Array.from({ length: 10 }, (_, i) => ({
    value: `exercise-${page}-${i}`,
    label: `Exercise ${page}-${i}`,
  }));

  return {
    data: mockData,
    hasMore: page < 3, // Simulate 3 pages of data
  };
}

type ClientSelectProps = {
  value: string;
  onChange: (value: string) => void;
  required?: boolean;
}

export function ClientSelect({ value, onChange, required }: ClientSelectProps) {
  return <InfiniteScrollSelect
    label="Client"
    value={value}
    onChange={onChange}
    fetchData={fetchExercises}
    placeholder="Search for a client..."
    required={required}
  />
}