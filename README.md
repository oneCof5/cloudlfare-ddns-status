# cloudlfare-ddns-status
 A small webserver to report ddns status changes to an api intended to use in [Homepage](https:/gethomepage.dev)

 ## Requirements
 This wrapper container was built around the (Hotio Cloudflare DDNS)[https://hotio.dev/containers/cloudflareddns/] container and is intended to run as a side-care container.

 ## Docker
 ```
 docker run
  -d
  --name='cloudflare-ddns-status'
  --net='{custom-bridge-network}'
  -e 'SOURCE_FILE'='/data/cf-ddns-{mydomain}.cache'
  -e 'REFRESH_SECONDS'='30'
  -e 'PORT'='8080'
  -p '8129:8080/tcp'
  -v '/mnt/cache/appdata/cloudflareddns/':'/data':'ro' 'ghcr.io/onecof5/cloudflare-ddns-status'
 ```