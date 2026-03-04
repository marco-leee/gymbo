import tailwindcss from '@tailwindcss/vite';
import { sveltekit } from '@sveltejs/kit/vite';
import { defineConfig } from 'vite';

const backendUrl = process.env.PUBLIC_API_URL ?? process.env.VITE_PUBLIC_API_URL ?? 'http://localhost:3000';

export default defineConfig({
	plugins: [tailwindcss(), sveltekit()],
	server: {
		proxy: {
			'/gateways.admin.v1.AdminGatewayService': backendUrl,
			'/gateways.trainer.v1.TrainerGatewayService': backendUrl,
			'/gateways.client.v1.ClientGatewayService': backendUrl,
			'/gateways.organisation.v1.OrganisationGatewayService': backendUrl,
		},
	},
});
