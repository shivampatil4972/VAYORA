## OSRM Map Data Setup

VAYORA uses OSRM (Open Source Routing Machine) for road routing.

### Development

In development mode, if no OSRM data is present, Spring Boot falls back to
Haversine distance estimation. The OSRM service is in the `full` Docker profile.

### Setting up real OSRM data (India region)

```bash
# Download India OSM data
wget https://download.geofabrik.de/asia/india-latest.osm.pbf -P database/osrm/

# Extract (requires OSRM Docker)
docker run -t -v $(pwd)/database/osrm:/data osrm/osrm-backend osrm-extract \
  -p /opt/car.lua /data/india-latest.osm.pbf

# Partition
docker run -t -v $(pwd)/database/osrm:/data osrm/osrm-backend osrm-partition \
  /data/india-latest.osrm

# Customize
docker run -t -v $(pwd)/database/osrm:/data osrm/osrm-backend osrm-customize \
  /data/india-latest.osrm
```

After processing, rename:
```bash
mv database/osrm/india-latest.osrm database/osrm/map.osrm
```

Then start with:
```bash
docker compose --profile full up osrm
```
