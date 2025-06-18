import { adminGatewayClient } from "./shared";
import { CreateExerciseResponse, DeleteExerciseResponse, GetExerciseResponse, ListExercisesResponse, UpdateExerciseResponse } from "@/gen/web/shared/messages/v1/exercise_pb";
import { Exercise, NewExercise } from "@/gen/web/shared/entities/v1/exercise_pb";
import { NewMedia } from "@/gen/web/shared/entities/v1/media_pb";

export class AdminGatewayExerciseService {
  private static client = adminGatewayClient;
  
  public static async createExercise(newExercise: NewExercise, newMedia: NewMedia[]): Promise<CreateExerciseResponse> {
    const response = await AdminGatewayExerciseService.client.createExercise({
      $typeName: 'shared.messages.v1.CreateExerciseRequest',
      newExercise: {
        $typeName: 'shared.messages.v1.ExtendedNewExercise',
        newExercise,
        newMedia,
      },
    });

    return response;
  }

  public static async getExercise(id: string): Promise<GetExerciseResponse> {
    const response = await AdminGatewayExerciseService.client.getExercise({
      $typeName: 'shared.messages.v1.GetExerciseRequest',
      id,
    });

    return response;
  }

  public static async listExercises(index: number, limit: number, offset: number, filters: Record<string, string>, sort: Record<string, string>): Promise<ListExercisesResponse> {
    const response = await AdminGatewayExerciseService.client.listExercises({
      $typeName: 'shared.messages.v1.ListExercisesRequest',
      index,
      limit,
      offset,
      filters,
      sort,
    });

    return response;
  }

  public static async updateExercise(exercise: Exercise): Promise<UpdateExerciseResponse> {
    const response = await AdminGatewayExerciseService.client.updateExercise({
      $typeName: 'shared.messages.v1.UpdateExerciseRequest',
    });

    return response;
  }

  public static async deleteExercise(id: string): Promise<DeleteExerciseResponse> {
    const response = await AdminGatewayExerciseService.client.deleteExercise({
      $typeName: 'shared.messages.v1.DeleteExerciseRequest',
      id,
    });

    return response;
  }
}