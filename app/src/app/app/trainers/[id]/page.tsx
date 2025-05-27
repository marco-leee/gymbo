import { useParams } from "next/navigation";

export default function TrainerPage() {
  const { id } = useParams();

  return <div>TrainerPage {id}</div>;
}