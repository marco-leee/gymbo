FROM caddy:2.9.1-alpine

COPY infra/caddyfile /etc/caddy/Caddyfile

EXPOSE 443

CMD ["caddy", "run", "--config", "/etc/caddy/Caddyfile"]