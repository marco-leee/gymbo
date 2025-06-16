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

type AssessmentSelectProps = {
  value: string;
  onChange: (value: string) => void;
  required?: boolean;
  disable?: boolean;
}

export function AssessmentSelect({ value, onChange, required, disable }: AssessmentSelectProps) {
  return <InfiniteScrollSelect
    label="Assessment"
    value={value}
    onChange={onChange}
    fetchData={fetchExercises}
    placeholder="Select a client and search for an assessment..."
    required={required}
    disabled={disable}
  />
}