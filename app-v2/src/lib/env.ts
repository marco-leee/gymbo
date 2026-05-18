import { env as privateEnv } from '$env/dynamic/private';

export const env = {
	MONGO_URI: privateEnv.MONGO_URI || 'mongodb://gymbo:gymbo@localhost:27017/gymbo?authSource=admin',
	STORAGE_ENDPOINT: privateEnv.STORAGE_ENDPOINT || 'http://localhost:9000',
	STORAGE_REGION: privateEnv.STORAGE_REGION || 'auto',
	STORAGE_ACCESS_KEY: privateEnv.STORAGE_ACCESS_KEY || 'admin',
	STORAGE_SECRET_KEY: privateEnv.STORAGE_SECRET_KEY || 'qwertyui',
	STORAGE_BUCKET: privateEnv.STORAGE_BUCKET || 'gymbo',
	MODEL_KEY: privateEnv.MODEL_KEY || 'yolo26s-pose.onnx',
	MODEL_VERSION: privateEnv.MODEL_VERSION || 'v1'
};