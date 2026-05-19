import { ObjectId } from 'mongodb';
import { z } from 'zod';

export function isValidObjectIdParam(id: string): boolean {
	return Boolean(id && ObjectId.isValid(id) && id.length === 24);
}

export function parseObjectId(id: string): ObjectId {
	if (!isValidObjectIdParam(id)) {
		throw new Error('Invalid id');
	}
	return new ObjectId(id);
}

export const objectIdRefSchema = z
	.string()
	.refine(isValidObjectIdParam, { message: 'Invalid id' });

export function objectIdToString(value: ObjectId | string): string {
	return value instanceof ObjectId ? value.toString() : value;
}

export function objectIdsEqual(a: ObjectId | string, b: string): boolean {
	return objectIdToString(a) === b;
}
