import { useSupabaseClient } from "@/app/utils/supabase-client";
import { SupabaseClient } from "@supabase/supabase-js";
import { Trainer } from "@/app/models";

class TrainerService {
  private readonly TRAINER_TABLE = "trainers";
  private trainer: SupabaseClient = useSupabaseClient();

  async getTrainers(page: number, limit: number): Promise<Trainer[]> {
    const offset = (page - 1) * limit;

    const { data, error } = await this.trainer.from(this.TRAINER_TABLE).select("*").range(offset, offset + limit - 1);

    if (error) {
      throw error;
    }

    return data.map((trainer) => Trainer.parse(trainer));
  }

  async getTrainerById(id: string): Promise<Trainer> {
    const { data, error } = await this.trainer.from(this.TRAINER_TABLE).select("*").eq("id", id).single();

    if (error) {
      throw error;
    }

    return Trainer.parse(data);
  }

  async getTrainerByEmail(email: string): Promise<Trainer> {
    const { data, error } = await this.trainer.from(this.TRAINER_TABLE).select("*").eq("email", email).single();

    if (error) {
      throw error;
    }

    return Trainer.parse(data);
  }


  async createTrainer(trainer: Trainer): Promise<Trainer> {
    const { data, error } = await this.trainer.from(this.TRAINER_TABLE).insert(trainer).select("*").limit(1).single();

    if (error) {
      throw error;
    }

    return Trainer.parse(data);
  }
}

const trainerService = new TrainerService();

export default trainerService;