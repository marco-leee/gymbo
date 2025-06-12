import { Organisation } from "@/gen/web/shared/entities/v1/organisation_pb";
import { CreateOrganisationResponse, DeleteOrganisationResponse, GetOrganisationResponse, UpdateOrganisationResponse } from "@/gen/web/shared/messages/v1/organisation_pb";
import { adminGatewayClient } from "./shared";

const client = adminGatewayClient;

export const createOrganisation = async (organisation: Organisation): Promise<CreateOrganisationResponse> => {
  const response = await client.createOrganisation({
    organisation
  });

  return response;
}

export const updateOrganisation = async (organisation: Organisation): Promise<UpdateOrganisationResponse> => {
  const response = await client.updateOrganisation({
    organisation
  });

  return response;
}

export const deleteOrganisation = async (id: string): Promise<DeleteOrganisationResponse> => {
  const response = await client.deleteOrganisation({
    id
  });

  return response;
}