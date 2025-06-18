package admingateway

import (
	"context"
	"fmt"

	"connectrpc.com/connect"
	v1_messages "gymbo.stixman.co/shared/gen/messages/v1"
	"gymbo.stixman.co/shared/models"
)

func (as *AdminGateway) GetClient(ctx context.Context, req *connect.Request[v1_messages.GetClientRequest]) (*connect.Response[v1_messages.GetClientResponse], error) {
	client, err := as.db.GetClientByID(req.Msg.Id)

	if err != nil {
		return nil, err
	}

	return connect.NewResponse(&v1_messages.GetClientResponse{
		Client: client.ToProto(),
	}), nil
}

func (as *AdminGateway) CreateClient(ctx context.Context, req *connect.Request[v1_messages.CreateClientRequest]) (*connect.Response[v1_messages.CreateClientResponse], error) {

	client := &models.Client{
		User: models.Users{
			Email:     req.Msg.Client.Email,
			FullName:  req.Msg.Client.FullName,
			FirstName: *req.Msg.Client.FirstName,
			LastName:  *req.Msg.Client.LastName,
		},
		Gender: req.Msg.Client.Gender,
	}

	if req.Msg.Client.Height != nil {
		client.Height = float64(req.Msg.Client.Height.Value)
	}
	if req.Msg.Client.Weight != nil {
		client.Weight = float64(req.Msg.Client.Weight.Value)
	}

	if err := client.Validate(as.db.GetClient()); err != nil {
		return nil, err
	}

	if err := as.db.CreateClient(client); err != nil {
		return nil, err
	}

	return connect.NewResponse(&v1_messages.CreateClientResponse{
		Client: client.ToProto(),
	}), nil
}

func (as *AdminGateway) UpdateClient(ctx context.Context, req *connect.Request[v1_messages.UpdateClientRequest]) (*connect.Response[v1_messages.UpdateClientResponse], error) {
	return connect.NewResponse(&v1_messages.UpdateClientResponse{}), nil
}

func (as *AdminGateway) DeleteClient(ctx context.Context, req *connect.Request[v1_messages.DeleteClientRequest]) (*connect.Response[v1_messages.DeleteClientResponse], error) {
	if err := as.db.DeleteClient(req.Msg.Id); err != nil {
		return nil, err
	}

	return connect.NewResponse(&v1_messages.DeleteClientResponse{}), nil
}

func (as *AdminGateway) ListClients(ctx context.Context, req *connect.Request[v1_messages.ListClientsRequest]) (*connect.Response[v1_messages.ListClientsResponse], error) {
	clients, err := as.db.ListClients(int32(req.Msg.Index), int(req.Msg.Limit), int(req.Msg.Offset), req.Msg.Filters, req.Msg.Sort)

	if err != nil {
		return nil, err
	}

	total, err := as.db.GetTotalClientsCount(req.Msg.Filters)

	if err != nil {
		return nil, err
	}

	fmt.Println(clients)

	for _, client := range clients {
		fmt.Printf("%+v\n", client)
	}

	return connect.NewResponse(&v1_messages.ListClientsResponse{
		Clients: models.ClientsToProto(clients),
		Total:   int32(total),
		Page:    int32(req.Msg.Index),
		Limit:   int32(req.Msg.Limit),
		Offset:  int32(req.Msg.Offset),
	}), nil
}
