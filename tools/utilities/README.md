# Utilities Module

Provides mathematical, geometrical, image processing, serialization, and networking helpers shared across all microservices in the FSOC tracking system.

## Features
- **Projective Geometry**: World canvas coordinates to camera sensor pixel plane conversions with jitter and platform motion offsets.
- **Image Processing**: Fast Base64, JPEG encoding/decoding, HUD telemetry renderer with aerospace reticles and 10px ISRO requirement circles.
- **Networking**: Standardized JSON envelopes, Numpy-aware JSON encoders.
