default:
  just --list

init:
  docker compose up -d

fe:
  cd app && bun run dev

ai:
  cd backend && source ./.venv/bin/activate && cd src && uv run python __main__.py --listen --model-size n

image := "ghcr.io/marco-leee/gymbo/pose:yolov26"
build-pose version:
    docker build --platform linux/amd64 -f backend/Dockerfile.video-worker -t {{image}}-{{version}} backend/
    docker push {{image}}-{{version}}

# mongosh --host localhost:27017 --username gymbo --password gymbo --authenticationDatabase admin
# use gymbo
# db.createUser({user: "gymbo", pwd: "gymbo", roles: [{role: "readWrite", db: "gymbo"}]})