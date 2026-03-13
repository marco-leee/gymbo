import { env as privateEnv } from '$env/dynamic/private';

export const env = {
	MONGO_URI: privateEnv.MONGO_URI || 'mongodb://admin:local@localhost:27017',
	MONGO_DB_NAME: privateEnv.MONGO_DB_NAME || 'gymbo',
	STORAGE_ENDPOINT: privateEnv.STORAGE_ENDPOINT || 'http://localhost:9000',
	STORAGE_REGION: privateEnv.STORAGE_REGION || 'ap-southeast-1',
	STORAGE_ACCESS_KEY: privateEnv.STORAGE_ACCESS_KEY || 'admin',
	STORAGE_SECRET_KEY: privateEnv.STORAGE_SECRET_KEY || 'qwertyui',
	STORAGE_BUCKET: privateEnv.STORAGE_BUCKET || 'gymbo',
	MODEL_KEY: privateEnv.MODEL_KEY || 'yolo26s-pose.onnx',
	MODEL_BUCKET: privateEnv.MODEL_BUCKET || privateEnv.STORAGE_BUCKET || 'gymbo',
	MODEL_VERSION: privateEnv.MODEL_VERSION || 'v1'
};
console.log(env);