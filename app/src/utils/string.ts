import { Client_Gender } from "@/gen/web/shared/entities/v1/client_pb";
import { ExerciseType } from "@/gen/web/shared/entities/v1/exercise_pb";
import { CameraView } from "@/gen/web/shared/entities/v1/media_pb";

/**
 * Formats a string by:
 * 1. Stripping all whitespaces
 * 2. Converting special characters between words into whitespace
 * 3. Capitalizing the first character
 * @param str - The input string to format
 * @returns The formatted string
 */
export function formatLabel(str: string): string {
	if (!str) return "";

	// Replace special characters with whitespace
	const withoutSpecialChars = str.replace(/[^a-zA-Z0-9\s]/g, " ");

	// Remove extra whitespaces and trim
	const withoutExtraSpaces = withoutSpecialChars.replace(/\s+/g, " ").trim();

	// Capitalize first character
	return (
		withoutExtraSpaces.charAt(0).toUpperCase() +
		withoutExtraSpaces.slice(1).toLowerCase()
	);
}

export function toCameraView(str: string): CameraView {
	let cv: CameraView;

	switch (str) {
		case "LEFT":
			cv = CameraView.LEFT;
			break;
		case "RIGHT":
			cv = CameraView.RIGHT;
			break;
		case "FRONT":
			cv = CameraView.FRONT;
			break;
		case "BACK":
			cv = CameraView.BACK;
			break;
		case "TOP":
			cv = CameraView.TOP;
			break;
		case "BOTTOM":
			cv = CameraView.BOTTOM;
			break;
		default:
			cv = CameraView.UNSPECIFIED;
	}
	return cv;
}

export function toExerciseType(str: string): ExerciseType {
	let et: ExerciseType;

	switch (str) {
		case "PUSH_UP":
			et = ExerciseType.PUSH_UP;
			break;
		case "LUNGE":
			et = ExerciseType.LUNGE;
			break;
		case "SQUAT":
			et = ExerciseType.SQUAT;
    default:
      et = ExerciseType.UNSPECIFIED;
	}

  return et;
}

export function toClientGender(str: string): Client_Gender {
	let cg: Client_Gender;

	switch (str) {
		case "MALE":
			cg = Client_Gender.MALE;
			break;
		case "FEMALE":
			cg = Client_Gender.FEMALE;
			break;
		case "OTHER":
			cg = Client_Gender.OTHER;
			break;
		default:
			cg = Client_Gender.UNSPECIFIED;
	}

	return cg;
}
