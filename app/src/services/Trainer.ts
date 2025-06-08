import { useSupabaseClient } from "@/utils/supabase";
import { SupabaseClient } from "@supabase/supabase-js";
import { Trainer } from "@/models";

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

  async getTrainerById(id: string): Promise<Trainer | null> {
    const { data, error } = await this.trainer.from(this.TRAINER_TABLE).select("*").eq("id", id).limit(1);

    if (error) {
      throw error;
    }

    return data.length > 0 ? Trainer.parse(data[0]) : null;
  }

  async getTrainerByEmail(email: string): Promise<Trainer | null> {
    const { data, error } = await this.trainer.from(this.TRAINER_TABLE).select("*").eq("email", email).limit(1);

    if (error) {
      throw error;
    }

    return data.length > 0 ? Trainer.parse(data[0]) : null;
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