export default function ExercisePage({
  params,
}: {
  params: { id: string };
}) {
  return <div>ExercisePage {params.id}</div>;
}