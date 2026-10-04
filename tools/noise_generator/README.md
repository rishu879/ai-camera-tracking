# Noise Generator Tool

Sensor Disturbance & Optical Blur Microservice for Mobile FSOC tracking.

## Responsibilities
- Generates high-fidelity sensor disturbances and optical blurs according to **ISRO SIH specifications**:
  - **Gaussian Noise**: Thermal and amplifier readout noise with standard deviation up to $20$ pixels.
  - **Salt & Pepper Noise**: Random dead/hot pixel defects covering up to $10\%$ of the image.
  - **Poisson Noise**: Photon shot noise modeling discrete quantum photon arrival statistics.
  - **Motion Blur**: Linear Point Spread Function (PSF) kernel convolution in arbitrary angular directions.
  - **Camera Defocus Blur**: Gaussian / Airy disc aberration modeling focal plane defocusing.
- Provides REST API to apply configured noise profiles to base64 images.

## API Endpoints
- `GET /health`: Health status.
- `GET /config`: Retrieve current noise settings.
- `POST /config`: Partial update of noise parameters.
- `POST /apply`: Apply noise and blur pipeline to input image.
- `POST /reset`: Reset all noise levels to zero.

## Running Locally
```bash
python -m tools.noise_generator.main --host 0.0.0.0 --port 8006
```

## Running with Docker
```bash
docker build -t fsoc-noise -f tools/noise_generator/Dockerfile .
docker run -p 8006:8006 fsoc-noise
```
