default:
  just --list

init:
  docker compose up -d

fe:
  cd app && bun run dev

ai:
  cd backend && source ./.venv/bin/activate && cd src && uv run python __main__.py --listen

# mongosh --host localhost:27017 --username gymbo --password gymbo --authenticationDatabase admin
# use gymbo
# db.createUser({user: "gymbo", pwd: "gymbo", roles: [{role: "readWrite", db: "gymbo"}]})