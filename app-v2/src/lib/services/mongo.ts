import { MongoClient, ObjectId, type Collection, type WithId, type Filter } from 'mongodb';
import { z } from 'zod';
import { env } from '$env/dynamic/private';
import { v7 as uuidv7 } from 'uuid';

const MONGO_URI = env.MONGO_URI || 'mongodb://admin:local@localhost:27017';
const DB_NAME = env.MONGO_DB_NAME || 'gymbo';

let client: MongoClient | null = null;

export const UserSchema = z.object({
	email: z.string().email(),
	full_name: z.string().min(1),
	first_name: z.string(),
	last_name: z.string(),
	created_at: z.date(),
	updated_at: z.date(),
	deleted_at: z.date().nullable().optional()
});

export const ClientSchema = z.object({
	user_id: z.string(),
	gender: z.string(),
	height_cm: z.number().nonnegative(),
	weight_kg: z.number().nonnegative(),
	user: UserSchema,
	created_at: z.date(),
	updated_at: z.date(),
	deleted_at: z.date().nullable().optional()
});

export const CreateClientSchema = z.object({
	email: z.string().email(),
	full_name: z.string().min(1),
	first_name: z.string().optional().default(''),
	last_name: z.string().optional().default(''),
	gender: z.string().optional().default(''),
	height_cm: z.number().nonnegative().optional().default(0),
	weight_kg: z.number().nonnegative().optional().default(0)
});

export const UpdateClientSchema = z.object({
	gender: z.string().optional(),
	height_cm: z.number().nonnegative().optional(),
	weight_kg: z.number().nonnegative().optional(),
	user: z.object({
		email: z.string().email().optional(),
		full_name: z.string().min(1).optional(),
		first_name: z.string().optional(),
		last_name: z.string().optional()
	}).optional()
});

export type UserDoc = z.infer<typeof UserSchema>;
export type ClientDoc = z.infer<typeof ClientSchema>;
export type CreateClientInput = z.infer<typeof CreateClientSchema>;
export type UpdateClientInput = z.infer<typeof UpdateClientSchema>;
export type ClientWithId = WithId<ClientDoc>;

export async function getMongoClient(): Promise<MongoClient> {
	if (!client) {
		client = new MongoClient(MONGO_URI);
		await client.connect();
	}
	return client;
}

export async function getDb() {
	const mongo = await getMongoClient();
	return mongo.db(DB_NAME);
}

export async function getClientsCollection(): Promise<Collection<ClientDoc>> {
	const db = await getDb();
	return db.collection<ClientDoc>('clients');
}

export async function listClients(filter: Filter<ClientDoc> = {}): Promise<ClientWithId[]> {
	const collection = await getClientsCollection();
	return collection.find(filter).sort({ created_at: -1 }).toArray();
}

export async function getClientById(id: string): Promise<ClientWithId | null> {
	const collection = await getClientsCollection();
	return collection.findOne({ _id: new ObjectId(id) } as Filter<ClientDoc>);
}

export async function getClientByUserId(userId: string): Promise<ClientWithId | null> {
	const collection = await getClientsCollection();
	return collection.findOne({ user_id: userId });
}

export async function createClient(data: Omit<ClientDoc, 'created_at' | 'updated_at'>): Promise<ClientWithId> {
	const collection = await getClientsCollection();
	const now = new Date();
	const doc: ClientDoc = {
		...data,
		created_at: now,
		updated_at: now
	};
	const result = await collection.insertOne(doc);
	return { _id: result.insertedId, ...doc };
}

export async function updateClient(
	id: string,
	data: Partial<Omit<ClientDoc, '_id' | 'created_at'>>
): Promise<ClientWithId | null> {
	const collection = await getClientsCollection();
	const update = {
		$set: {
			...data,
			updated_at: new Date()
		}
	};
	await collection.updateOne({ _id: new ObjectId(id) } as Filter<ClientDoc>, update);
	return getClientById(id);
}

export async function deleteClient(id: string): Promise<boolean> {
	const collection = await getClientsCollection();
	const result = await collection.deleteOne({ _id: new ObjectId(id) } as Filter<ClientDoc>);
	return result.deletedCount === 1;
}

export async function softDeleteClient(id: string): Promise<boolean> {
	const collection = await getClientsCollection();
	const result = await collection.updateOne(
		{ _id: new ObjectId(id) } as Filter<ClientDoc>,
		{ $set: { deleted_at: new Date(), updated_at: new Date() } }
	);
	return result.modifiedCount === 1;
}

export function generateUUID(): string {
    return uuidv7();
}
