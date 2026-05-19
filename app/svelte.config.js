import adapter from '@sveltejs/adapter-vercel';

/** @type {import('@sveltejs/kit').Config} */
const config = {
	kit: {
		// adapter: adapter({
		// 	// See below for an explanation of these options
		// 	config: undefined,
		// 	platformProxy: {
		// 		configPath: undefined,
		// 		environment: undefined,
		// 		persist: undefined
		// 	},
		// 	fallback: 'plaintext',
		// 	routes: {
		// 		include: ['/*'],
		// 		exclude: ['<all>']
		// 	}
		// })
		adapter: adapter()
	}
};

export default config;