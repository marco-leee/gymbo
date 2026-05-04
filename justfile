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
  cp -r gen/web ../app/src/gen

clean:
  rm -rf proto/gen/*
  rm -rf services/client_gateway/gen/*
  rm -rf services/trainer_gateway/gen/*
  rm -rf services/organisation_gateway/gen/*
  rm -rf services/admin_gateway/gen/*
  rm -rf services/shared/gen/*
  rm -rf app/src/gen/*

# cqlsh -u cassandra -p cassandra
# create user if not exists 'admin' with password 'local' nosuperuser;
# grant all permissions on keyspaces exercise_analyser to admin;