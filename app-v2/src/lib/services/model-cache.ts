type PoseModelResponse = {
	version: string;
	downloadUrl: string;
	etag?: string;
	contentLength?: number;
};

type CachedPoseModel = {
	version: string;
	modelData: ArrayBuffer;
	etag?: string;
	contentLength?: number;
	cachedAt: number;
};

const DB_NAME = "gymbo-model-cache";
const STORE_NAME = "pose-models";

let inflightModelPromise: Promise<ArrayBuffer> | null = null;

function isIndexedDbAvailable() {
	return typeof indexedDB !== "undefined";
}

function openDatabase(): Promise<IDBDatabase | null> {
	if (!isIndexedDbAvailable()) {
		return Promise.resolve(null);
	}

	return new Promise((resolve, reject) => {
		const request = indexedDB.open(DB_NAME, 1);
		request.onerror = () =>
			reject(request.error ?? new Error("Failed to open model cache"));
		request.onupgradeneeded = () => {
			const db = request.result;
			if (!db.objectStoreNames.contains(STORE_NAME)) {
				db.createObjectStore(STORE_NAME, { keyPath: "version" });
			}
		};
		request.onsuccess = () => resolve(request.result);
	});
}

async function getCachedPoseModel(version: string): Promise<CachedPoseModel | null> {
	const db = await openDatabase();
	if (!db) {
		return null;
	}

	return new Promise((resolve, reject) => {
		const tx = db.transaction(STORE_NAME, "readonly");
		const store = tx.objectStore(STORE_NAME);
		const request = store.get(version);

		request.onerror = () =>
			reject(request.error ?? new Error("Failed to read model cache"));
		request.onsuccess = () =>
			resolve((request.result as CachedPoseModel | undefined) ?? null);
		tx.oncomplete = () => db.close();
		tx.onerror = () => reject(tx.error ?? new Error("Failed to read model cache"));
		tx.onabort = () => reject(tx.error ?? new Error("Failed to read model cache"));
	});
}

async function putCachedPoseModel(record: CachedPoseModel): Promise<void> {
	const db = await openDatabase();
	if (!db) {
		return;
	}

	return new Promise((resolve, reject) => {
		const tx = db.transaction(STORE_NAME, "readwrite");
		const store = tx.objectStore(STORE_NAME);

		store.put(record);

		const cursorRequest = store.openCursor();
		cursorRequest.onerror = () =>
			reject(cursorRequest.error ?? new Error("Failed to update model cache"));
		cursorRequest.onsuccess = () => {
			const cursor = cursorRequest.result;
			if (!cursor) {
				return;
			}
			if (cursor.key !== record.version) {
				cursor.delete();
			}
			cursor.continue();
		};

		tx.oncomplete = () => {
			db.close();
			resolve();
		};
		tx.onerror = () =>
			reject(tx.error ?? new Error("Failed to update model cache"));
		tx.onabort = () =>
			reject(tx.error ?? new Error("Failed to update model cache"));
	});
}

async function fetchPoseModelInfo(): Promise<PoseModelResponse> {
	const response = await fetch("/api/model");
	if (!response.ok) {
		throw new Error((await response.text()) || "Failed to fetch pose model");
	}

	const payload = (await response.json()) as Partial<PoseModelResponse>;
	if (typeof payload.version !== "string" || typeof payload.downloadUrl !== "string") {
		throw new Error("Invalid pose model response");
	}

	return {
		version: payload.version,
		downloadUrl: payload.downloadUrl,
		etag: typeof payload.etag === "string" ? payload.etag : undefined,
		contentLength:
			typeof payload.contentLength === "number" ? payload.contentLength : undefined,
	};
}

async function downloadPoseModel(
	model: PoseModelResponse,
	retryOnExpiredUrl = true,
): Promise<ArrayBuffer> {
	const response = await fetch(model.downloadUrl);
	if ((response.status === 401 || response.status === 403) && retryOnExpiredUrl) {
		return downloadPoseModel(await fetchPoseModelInfo(), false);
	}
	if (!response.ok) {
		throw new Error((await response.text()) || "Failed to download pose model");
	}

	return response.arrayBuffer();
}

async function loadPoseModelData(): Promise<ArrayBuffer> {
	const model = await fetchPoseModelInfo();
	const cached = await getCachedPoseModel(model.version);
	if (cached?.modelData) {
		return cached.modelData;
	}

	const modelData = await downloadPoseModel(model);
	await putCachedPoseModel({
		version: model.version,
		modelData,
		etag: model.etag,
		contentLength: model.contentLength,
		cachedAt: Date.now(),
	});

	return modelData;
}

export async function getPoseModelData(): Promise<ArrayBuffer> {
	if (!inflightModelPromise) {
		inflightModelPromise = loadPoseModelData().finally(() => {
			inflightModelPromise = null;
		});
	}

	return (await inflightModelPromise).slice(0);
}
