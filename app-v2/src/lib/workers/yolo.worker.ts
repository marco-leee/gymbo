import * as ort from "onnxruntime-web/webgpu";

type WorkerScope = {
	onmessage: ((event: MessageEvent<WorkerMessage>) => void | Promise<void>) | null;
	postMessage: (message: unknown, transfer?: Transferable[]) => void;
};

const workerScope = self as unknown as WorkerScope;

type InitMessage = {
	type: "init";
	modelData: ArrayBuffer;
};

type RunMessage = {
	type: "run";
	id: number;
	input: {
		data: ArrayBuffer;
		dims: number[];
		type: "float32";
	};
};

type DisposeMessage = {
	type: "dispose";
};

type WorkerMessage = InitMessage | RunMessage | DisposeMessage;

type PoseKeypoint = {
	x: number;
	y: number;
	confidence: number;
};

type PoseDetection = {
	confidence: number;
	classId: number;
	box: {
		x: number;
		y: number;
		width: number;
		height: number;
	};
	keypoints: PoseKeypoint[];
};

let sessionPromise: Promise<ort.InferenceSession> | null = null;
let modelData: ArrayBuffer | null = null;

function configureOrt() {
	ort.env.wasm.wasmPaths = "/ort/";
	ort.env.wasm.numThreads = 1;
	ort.env.webgpu.device = "";
}

function getSession() {
	if (!modelData) {
		throw new Error("Pose model was not initialized");
	}

	if (!sessionPromise) {
		configureOrt();
		sessionPromise = ort.InferenceSession.create(new Uint8Array(modelData), {
			executionProviders: ["webgpu", "wasm"],
		}).catch((error) => {
			sessionPromise = null;
			throw error;
		});
	}

	return sessionPromise;
}

function decodePrimaryPose(output: ort.Tensor | undefined): PoseDetection | null {
	if (!output || output.dims.length !== 3) {
		return null;
	}

	const data = output.data;
	if (!(data instanceof Float32Array)) {
		return null;
	}

	const [, detectionCount, valuesPerDetection] = output.dims;
	if (valuesPerDetection < 57) {
		return null;
	}

	let bestOffset = -1;
	let bestConfidence = 0;

	for (let detectionIdx = 0; detectionIdx < detectionCount; detectionIdx++) {
		const offset = detectionIdx * valuesPerDetection;
		const confidence = data[offset + 4] ?? 0;
		if (confidence > bestConfidence) {
			bestConfidence = confidence;
			bestOffset = offset;
		}
	}

	if (bestOffset < 0 || bestConfidence <= 0) {
		return null;
	}

	const centerX = data[bestOffset] ?? 0;
	const centerY = data[bestOffset + 1] ?? 0;
	const width = data[bestOffset + 2] ?? 0;
	const height = data[bestOffset + 3] ?? 0;
	const classId = data[bestOffset + 5] ?? 0;
	const keypoints: PoseKeypoint[] = [];

	for (let keypointIdx = 0; keypointIdx < 17; keypointIdx++) {
		const keypointOffset = bestOffset + 6 + keypointIdx * 3;
		keypoints.push({
			x: data[keypointOffset] ?? 0,
			y: data[keypointOffset + 1] ?? 0,
			confidence: data[keypointOffset + 2] ?? 0,
		});
	}

	return {
		confidence: bestConfidence,
		classId,
		box: {
			x: centerX - width / 2,
			y: centerY - height / 2,
			width,
			height,
		},
		keypoints,
	};
}

workerScope.onmessage = async (event: MessageEvent<WorkerMessage>) => {
	const message = event.data;

	try {
		if (message.type === "dispose") {
			sessionPromise = null;
			modelData = null;
			return;
		}

		if (message.type === "init") {
			modelData = message.modelData;
			sessionPromise = null;
			await getSession();
			workerScope.postMessage({ type: "ready" });
			return;
		}

		const session = await getSession();
		const inputName = session.inputNames[0] ?? "images";
		const inputData = new Float32Array(message.input.data);
		const inputTensor = new ort.Tensor(
			message.input.type,
			inputData,
			message.input.dims,
		);
		const outputs = await session.run({ [inputName]: inputTensor });
		const pose = decodePrimaryPose(outputs.output0);

		workerScope.postMessage(
			{
				type: "result",
				id: message.id,
				inputName,
				outputNames: session.outputNames,
				pose,
			},
		);
	} catch (error) {
		const payload = {
			type: "error",
			message: error instanceof Error ? error.message : "Pose worker failed",
		};

		if (message.type === "run") {
			workerScope.postMessage({ ...payload, id: message.id });
			return;
		}

		workerScope.postMessage(payload);
	}
};
