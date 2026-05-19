export async function getMediaPlayUrl(
	key: string,
	fetchFn: typeof fetch = fetch
): Promise<string> {
	const searchParams = new URLSearchParams({ key });
	const response = await fetchFn(`/api/media/play?${searchParams}`);
	if (!response.ok) {
		throw new Error(`Failed to get media play URL: ${response.statusText}`);
	}

	const payload = await response.json() as { play_url: string };
	return payload.play_url;
}
