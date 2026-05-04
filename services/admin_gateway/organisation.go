package admingateway

import (
	"context"

	"connectrpc.com/connect"
	v1_messages "gymbo.stixman.co/shared/gen/messages/v1"
	"gymbo.stixman.co/shared/models"
)

func FormatOrganisationFilters(filters map[string]string) map[string]string {
	formattedFilters := make(map[string]string)
	for key, value := range filters {
		formattedFilters[key] = value
	}
	return formattedFilters
}

func FormatOrganisationSort(sort map[string]v1_messages.ListOrganisationRequest_Sort) map[string]string {
	formattedSort := make(map[string]string)
	for key, value := range sort {
		formattedSort[key] = value.String()
	}
	return formattedSort
}

func (as *AdminGateway) GetOrganisation(ctx context.Context, req *connect.Request[v1_messages.GetOrganisationRequest]) (*connect.Response[v1_messages.GetOrganisationResponse], error) {
	organisation, err := as.db.GetOrganisationByID(req.Msg.Id)

	if err != nil {
		return nil, err
	}

	return connect.NewResponse(&v1_messages.GetOrganisationResponse{
		Organisation: organisation.ToProto(),
	}), nil
}

func (as *AdminGateway) CreateOrganisation(ctx context.Context, req *connect.Request[v1_messages.CreateOrganisationRequest]) (*connect.Response[v1_messages.CreateOrganisationResponse], error) {
	organisation := &models.Organisation{
		Email:   req.Msg.Organisation.Email,
		Name:    req.Msg.Organisation.Name,
		Address: req.Msg.Organisation.Address,
		Phone:   req.Msg.Organisation.Phone,
		Logo:    req.Msg.Organisation.Logo,
	}

	if err := organisation.Validate(as.db.GetClient()); err != nil {
		return nil, err
	}

	if err := as.db.CreateOrganisation(organisation); err != nil {
		return nil, err
	}

	return connect.NewResponse(&v1_messages.CreateOrganisationResponse{
		Organisation: organisation.ToProto(),
	}), nil
}

func (as *AdminGateway) UpdateOrganisation(ctx context.Context, req *connect.Request[v1_messages.UpdateOrganisationRequest]) (*connect.Response[v1_messages.UpdateOrganisationResponse], error) {
	return connect.NewResponse(&v1_messages.UpdateOrganisationResponse{}), nil
}

func (as *AdminGateway) DeleteOrganisation(ctx context.Context, req *connect.Request[v1_messages.DeleteOrganisationRequest]) (*connect.Response[v1_messages.DeleteOrganisationResponse], error) {
	return connect.NewResponse(&v1_messages.DeleteOrganisationResponse{}), nil
}

func (as *AdminGateway) ListOrganisations(ctx context.Context, req *connect.Request[v1_messages.ListOrganisationRequest]) (*connect.Response[v1_messages.ListOrganisationResponse], error) {
	organisations, err := as.db.ListOrganisations(req.Msg.Index, int(req.Msg.Limit), int(req.Msg.Offset), FormatOrganisationFilters(req.Msg.Filters), FormatOrganisationSort(req.Msg.Sort))

	if err != nil {
		return nil, err
	}

	total, err := as.db.GetTotalOrganisationsCount(req.Msg.Filters)

	if err != nil {
		return nil, err
	}

	return connect.NewResponse(&v1_messages.ListOrganisationResponse{
		Organisations: models.OrganisationsToProto(organisations),
		Page:          req.Msg.Index,
		Limit:         req.Msg.Limit,
		Offset:        req.Msg.Offset,
		Total:         int32(total),
	}), nil
}
