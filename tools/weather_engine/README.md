# Weather Engine Tool

Atmospheric Disturbance & Optical Degradation Microservice for Mobile FSOC terminals.

## Responsibilities
- Models optical transmission degradation according to the Beer-Lambert and Koschmieder scattering laws:
  - **Fog**: Mie scattering with atmospheric airlight blending and transmittance loss.
  - **Haze**: Aerosol turbidity and dynamic range contrast compression.
  - **Rain**: Semi-transparent directional streaks with refraction blur.
  - **Snow**: Fluttering snowflake occlusion particles.
  - **Night / Low-light**: Severe illumination drop with non-linear gamma curve.
  - **Brightness & Contrast**: Real-time gain and offset modulation.
- Exposes REST API to process frames and tune environmental conditions on the fly.

## API Endpoints
- `GET /health`: Health status.
- `GET /config`: Retrieve current weather parameters.
- `POST /config`: Partial update of weather parameters.
- `POST /apply`: Apply atmospheric effects to input base64 image.
- `POST /reset`: Reset to clear sky conditions.

## Running Locally
```bash
python -m tools.weather_engine.main --host 0.0.0.0 --port 8005
```

## Running with Docker
```bash
docker build -t fsoc-weather -f tools/weather_engine/Dockerfile .
docker run -p 8005:8005 fsoc-weather
```
