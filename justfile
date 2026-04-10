default:
  just --list

gen-proto: clean
  cd proto && \
  buf generate && \
  cp -r gen/go/gateways/client ../services/client_gateway/gen/gateways && \
  cp -r gen/go/gateways/trainer ../services/trainer_gateway/gen/gateways && \
  cp -r gen/go/gateways/organisation ../services/organisation_gateway/gen/gateways && \
  cp -r gen/go/gateways/admin ../services/admin_gateway/gen/gateways && \
  cp -r gen/go/shared/entities ../services/shared/gen/entities && \
  cp -r gen/go/shared/messages ../services/shared/gen/messages && \
  cp -r gen/web ../app/src/gen && \
  cp -r gen/web ../app-v2/src/lib/proto

clean:
  rm -rf proto/gen/*
  rm -rf services/client_gateway/gen/*
  rm -rf services/trainer_gateway/gen/*
  rm -rf services/organisation_gateway/gen/*
  rm -rf services/admin_gateway/gen/*
  rm -rf services/shared/gen/*
  rm -rf app/src/gen/*
  rm -rf app-v2/src/lib/proto/*
db:
  docker compose exec postgres psql -U admin -d gymbo

db-mongo:
  docker compose exec -it mongo mongo -u admin -p local gymbo

fe:
  cd app-v2 && bun dev